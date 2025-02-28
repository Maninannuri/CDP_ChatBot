import requests
from bs4 import BeautifulSoup
import html2text
from pathlib import Path
from typing import Dict, List
import json
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import platform
import os
import random
from .config.settings import (
    CHROME_OPTIONS,
    USER_AGENT,
    REQUEST_HEADERS,
    CDP_URLS,
    REQUEST_DELAY,
    MAX_RETRIES,
    WAIT_TIMEOUT
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseDocScraper:
    def __init__(self):
        self.converter = html2text.HTML2Text()
        self.converter.ignore_links = False
        self.driver = None
        self.wait = None
        self.setup_driver()

    def setup_driver(self):
        """Setup Chrome WebDriver with improved Win32 error handling"""
        chrome_options = Options()
        for option in CHROME_OPTIONS:
            chrome_options.add_argument(option)
        chrome_options.add_argument(f'--user-agent={USER_AGENT}')
        
        try:
            # Get Chrome version
            chrome_version = self._get_chrome_version()
            logger.info(f"Detected Chrome version: {chrome_version}")
            
            # First try undetected_chromedriver with explicit version
            try:
                import undetected_chromedriver as uc
                uc.TARGET_VERSION = chrome_version
                self.driver = uc.Chrome(
                    use_subprocess=True,
                    options=chrome_options,
                    version_main=chrome_version
                )
                logger.info("Undetected ChromeDriver setup successful")
            except Exception as e:
                logger.error(f"Undetected ChromeDriver failed: {str(e)}")
                
                # Fall back to standard ChromeDriver with explicit architecture handling
                try:
                    is_64bits = platform.architecture()[0] == '64bit'
                    
                    if is_64bits and platform.system() == 'Windows':
                        driver_path = ChromeDriverManager(
                            chrome_type="google",
                            version=f"{chrome_version}.0"
                        ).install()
                        service = Service(driver_path)
                        self.driver = webdriver.Chrome(service=service, options=chrome_options)
                        logger.info("Standard ChromeDriver (64-bit) setup successful")
                    else:
                        service = Service(ChromeDriverManager().install())
                        self.driver = webdriver.Chrome(service=service, options=chrome_options)
                        logger.info("Standard ChromeDriver setup successful")
                except Exception as inner_e:
                    logger.error(f"All ChromeDriver attempts failed: {str(inner_e)}")
                    logger.info("Falling back to requests-only mode")
                    self.driver = None
                    self.wait = None
                    return
            
            self.wait = WebDriverWait(self.driver, WAIT_TIMEOUT)
            
        except Exception as e:
            logger.error(f"All WebDriver attempts failed: {str(e)}")
            logger.info("Falling back to requests-only mode")
            self.driver = None
            self.wait = None

    def _get_chrome_version(self) -> int:
        """Detect installed Chrome version"""
        try:
            if platform.system() == 'Windows':
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Google\Chrome\BLBeacon')
                version = winreg.QueryValueEx(key, 'version')[0]
                return int(version.split('.')[0])
            elif platform.system() == 'Darwin':  # macOS
                import subprocess
                process = subprocess.Popen(
                    ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version'],
                    stdout=subprocess.PIPE
                )
                version = process.communicate()[0].decode('utf-8').replace('Google Chrome ', '').strip()
                return int(version.split('.')[0])
            elif platform.system() == 'Linux':
                import subprocess
                process = subprocess.Popen(['google-chrome', '--version'], stdout=subprocess.PIPE)
                version = process.communicate()[0].decode('utf-8').replace('Google Chrome ', '').strip()
                return int(version.split('.')[0])
        except Exception as e:
            logger.warning(f"Could not detect Chrome version: {e}")
            return 120  # Default to a recent version as fallback

    def get_page(self, url: str) -> str:
        """Get page content with improved error handling"""
        if self.driver is None:
            return self._get_with_requests(url)
        return self._get_with_selenium(url)

    def _get_with_requests(self, url: str) -> str:
        try:
            response = requests.get(url, headers=REQUEST_HEADERS, timeout=WAIT_TIMEOUT)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Failed to get page using requests: {str(e)}")
            return ""

    def _get_with_selenium(self, url: str) -> str:
        max_attempts = MAX_RETRIES
        for attempt in range(max_attempts):
            try:
                # Check if driver is alive
                if not self.driver or not hasattr(self.driver, 'current_url'):
                    logger.warning("Driver not available, reinitializing...")
                    self.setup_driver()
                    if not self.driver:
                        return self._get_with_requests(url)

                # Load page
                self.driver.get(url)
                
                # Check for common error patterns
                error_patterns = [
                    "ERR_", "400 Bad Request", "403 Forbidden",
                    "404 Not Found", "500 Internal Server", "502 Bad Gateway",
                    "503 Service Unavailable", "504 Gateway Timeout"
                ]
                
                page_source = self.driver.page_source
                for error in error_patterns:
                    if error in page_source:
                        raise Exception(f"Page load error ({error}): {url}")
                
                # Wait for body with timeout
                try:
                    self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                except Exception as wait_error:
                    logger.error(f"Wait timeout: {wait_error}")
                    raise
                
                # Adaptive wait based on page complexity
                page_size = len(page_source)
                wait_time = min(3 + (page_size // 100000), 10)
                time.sleep(wait_time)
                
                # Verify content was actually loaded
                if len(page_source.strip()) < 100:  # Suspiciously small
                    raise Exception("Page content appears empty or too small")
                
                return page_source
                
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                
                # Last attempt, switch to requests
                if attempt == max_attempts - 1:
                    logger.info(f"Switching to requests for {url}")
                    return self._get_with_requests(url)
                
                # Exponential backoff with jitter
                backoff_time = (2 ** attempt) + random.uniform(0, 1)
                logger.info(f"Backing off for {backoff_time:.2f} seconds")
                time.sleep(backoff_time)
                
                # Reset driver on failure
                if self.driver:
                    try:
                        self.driver.quit()
                    except Exception as quit_error:
                        logger.error(f"Error quitting driver: {quit_error}")
                    finally:
                        self.driver = None
                        self.wait = None
                
                # Reinitialize driver for next attempt
                self.setup_driver()
        
        logger.error(f"All attempts failed for {url}")
        return ""

    def _scrape_urls(self, urls: List[str]) -> List[Dict]:
        articles = []
        for url in urls:
            html = self.get_page(url)
            if not html:
                continue
            articles.extend(self._parse_html(html, url))
        return articles

    def _parse_html(self, html: str, url: str) -> List[Dict]:
        soup = BeautifulSoup(html, 'html.parser')
        articles = []
        
        # More comprehensive selector for documentation content
        selectors = [
            '.DocSearch-content', '.doc-content', 'main article', 
            '.content-body', '.documentation-content', 
            'main .content', '.docs-content', '.markdown-body',
            'article.doc', 'div.documentation', '.main-content',
            '.article-content', 'div[class*="docs"]', 'div[class*="article"]',
            '.post-content', '.entry-content'
        ]
        
        main_content = soup.select(', '.join(selectors))
        
        if not main_content:
            # Try finding content by heading pattern if selectors fail
            headings = soup.find_all(['h1', 'h2', 'h3'], limit=5)
            for heading in headings:
                parent = heading
                for _ in range(3):  # Check up to 3 levels up
                    if parent.parent and parent.parent.name != 'body':
                        parent = parent.parent
                    else:
                        break
                
                if parent and parent.name != 'body':
                    main_content.append(parent)
        
        # If still no content found, try to extract from body with heuristics
        if not main_content:
            body = soup.find('body')
            if body:
                # Remove navigation, headers, footers 
                for element in body.select('nav, header, footer, .sidebar, .navigation, .menu, .comments, aside'):
                    element.decompose()
                
                # Get largest text block
                paragraphs = body.find_all('p')
                if paragraphs and len(paragraphs) > 3:
                    # Find the parent containing most paragraphs
                    parents = {}
                    for p in paragraphs:
                        parent = p.parent
                        parents[parent] = parents.get(parent, 0) + 1
                    
                    # Select parent with most paragraphs as main content
                    if parents:
                        main_parent = max(parents.items(), key=lambda x: x[1])[0]
                        main_content = [main_parent]
        
        for article in main_content:
            title = article.find(['h1', 'h2', 'h3'])
            title = title.text.strip() if title else url.split('/')[-1].replace('-', ' ').title() or "Untitled"
            
            # Clean content before converting
            for script in article.find_all(['script', 'style']):
                script.decompose()
                
            content = self.converter.handle(str(article))
            
            # Skip if article is too short (likely not meaningful content)
            if len(content.split()) < 20:
                continue
                
            if any(a['title'] == title for a in articles):
                continue
                
            articles.append({
                'title': title,
                'content': content,
                'url': url
            })
        
        return articles

    def __del__(self):
        """Safe cleanup of webdriver with improved error handling"""
        if hasattr(self, 'driver') and self.driver is not None:
            try:
                # Disable the sleep call in undetected_chromedriver
                import undetected_chromedriver as uc
                if isinstance(self.driver, uc.Chrome):
                    # Patch the quit method to avoid sleep
                    original_quit = self.driver.quit
                    def patched_quit():
                        try:
                            self.driver.service.stop()
                        except:
                            pass
                    self.driver.quit = patched_quit
                
                # Gracefully close any remaining windows
                try:
                    if hasattr(self.driver, 'window_handles'):
                        for handle in self.driver.window_handles:
                            self.driver.switch_to.window(handle)
                            self.driver.close()
                except:
                    pass

                # Now call quit
                self.driver.quit()
            except:
                pass
            finally:
                # Ensure cleanup of service process
                try:
                    if hasattr(self.driver, 'service') and \
                       hasattr(self.driver.service, 'process') and \
                       self.driver.service.process:
                        self.driver.service.process.kill()
                except:
                    pass
                self.driver = None
                self.wait = None

class SegmentScraper(BaseDocScraper):
    def scrape(self) -> List[Dict]:
        return self._scrape_urls(CDP_URLS['segment'])

class MParticleScraper(BaseDocScraper):
    def scrape(self) -> List[Dict]:
        return self._scrape_urls(CDP_URLS['mparticle'])

class LyticsScraper(BaseDocScraper):
    def scrape(self) -> List[Dict]:
        return self._scrape_urls(CDP_URLS['lytics'])

class ZeotapScraper(BaseDocScraper):
    def scrape(self) -> List[Dict]:
        return self._scrape_urls(CDP_URLS['zeotap'])

class DocumentationScraper:
    def __init__(self):
        self.data_dir = Path('data/docs')
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize specialized scrapers
        self.scrapers = {
            'segment': SegmentScraper(),
            'mparticle': MParticleScraper(),
            'lytics': LyticsScraper(),
            'zeotap': ZeotapScraper(),
        }
        
        # Default documentation for common queries
        self.default_docs = {
            'segment': [{
                'title': 'Setting up Sources in Segment',
                'content': """
                To set up a new source in Segment:
                1. Log in to your Segment workspace
                2. Navigate to Connections > Sources
                3. Click 'Add Source'
                4. Choose your source type (Website, Mobile App, Server, etc.)
                5. Follow the setup instructions for your specific source
                6. Configure your source settings
                7. Enable the source when ready
                
                Common source types:
                - Analytics.js for websites
                - Mobile SDKs for iOS/Android apps
                - Server-side libraries
                - Cloud sources for SaaS tools
                """,
                'url': 'https://segment.com/docs/connections/sources/'
            }],
            'mparticle': [{
                'title': 'Creating User Profiles in mParticle',
                'content': """
                To create and manage user profiles in mParticle:
                1. Implement identity management
                2. Set up user attributes
                3. Configure identity priority
                4. Define user identity mapping
                5. Enable cross-platform identity resolution
                
                Key concepts:
                - Customer IDs
                - Device IDs
                - User attributes
                - Identity resolution
                """,
                'url': 'https://docs.mparticle.com/guides/idsync/'
            }],
            'lytics': [{
                'title': 'Building Audience Segments in Lytics',
                'content': """
                To build an audience segment in Lytics:
                1. Go to Audiences in your Lytics account
                2. Click 'Create New Audience'
                3. Define segment criteria using:
                   - User behaviors
                   - Profile attributes
                   - Content affinities
                4. Set audience rules and conditions
                5. Save and activate your audience
                
                Best practices:
                - Start with broad criteria
                - Use behavioral data
                - Test audience sizes
                - Monitor audience growth
                """,
                'url': 'https://docs.lytics.com/audiences/'
            }],
            'zeotap': [{
                'title': 'Data Integration with Zeotap',
                'content': """
                To integrate data with Zeotap:
                1. Set up a Zeotap account
                2. Configure data source connections
                3. Define data mapping schema
                4. Set up identity resolution rules
                5. Configure data export destinations
                
                Integration methods:
                - API integration
                - Batch file uploads
                - Server-to-server connections
                - Tag management systems
                """,
                'url': 'https://docs.zeotap.com/docs/'
            }]
        }
        
        # Add document indexing and rate limiting
        self.index_dir = Path('data/index')
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.request_delay = REQUEST_DELAY

    def _merge_content(self, existing_content: List[Dict], new_content: List[Dict]) -> List[Dict]:
        """Merge existing and new content, avoiding duplicates"""
        existing_titles = {doc['title'] for doc in existing_content}
        merged = existing_content.copy()
        
        for article in new_content:
            if article['title'] not in existing_titles:
                merged.append(article)
                existing_titles.add(article['title'])
        
        return merged

    def scrape_documentation(self):
        """Scrape documentation with improved error handling and content merging"""
        # Save default documentation first
        for cdp, content in self.default_docs.items():
            try:
                self._save_content(cdp, content)
                self._index_content(cdp, content)
                logger.info(f"Saved default documentation for {cdp}")
            except Exception as e:
                logger.error(f"Error saving default docs for {cdp}: {str(e)}")

        # Then try to scrape and merge live documentation
        for cdp, scraper in self.scrapers.items():
            try:
                logger.info(f"Scraping {cdp} documentation...")
                scraped_content = scraper.scrape()
                
                if scraped_content:
                    try:
                        # Load existing content (including defaults)
                        existing_content = self.default_docs.get(cdp, []).copy()
                        
                        # Merge with scraped content
                        merged_content = self._merge_content(existing_content, scraped_content)
                        
                        # Save and index merged content
                        self._save_content(cdp, merged_content)
                        self._index_content(cdp, merged_content)
                        logger.info(f"Successfully indexed {len(merged_content)} articles for {cdp}")
                    except Exception as e:
                        logger.error(f"Error processing content for {cdp}: {str(e)}")
                        # Ensure default content is saved
                        if cdp in self.default_docs:
                            self._save_content(cdp, self.default_docs[cdp])
                            self._index_content(cdp, self.default_docs[cdp])
                else:
                    logger.warning(f"No content scraped for {cdp}, using default content")
                    if cdp in self.default_docs:
                        self._save_content(cdp, self.default_docs[cdp])
                        self._index_content(cdp, self.default_docs[cdp])
                
                time.sleep(self.request_delay)
            except Exception as e:
                logger.error(f"Error scraping {cdp}: {str(e)}")
                # Save default content as fallback
                if cdp in self.default_docs:
                    self._save_content(cdp, self.default_docs[cdp])
                    self._index_content(cdp, self.default_docs[cdp])

    def _index_content(self, cdp: str, content: List[Dict]):
        """Create searchable index of documentation content"""
        index = {
            'articles': content,
            'keywords': {},
            'sections': {}
        }
        
        for article in content:
            # Index by keywords in title
            words = set(word.lower() for word in article['title'].split())
            for word in words:
                if word not in index['keywords']:
                    index['keywords'][word] = []
                index['keywords'][word].append(article['title'])
            
            # Index by sections/headings
            sections = self._extract_sections(article['content'])
            for section in sections:
                if section not in index['sections']:
                    index['sections'][section] = []
                index['sections'][section].append(article['title'])
                
        # Save index
        index_path = self.index_dir / f'{cdp}_index.json'
        try:
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving index for {cdp}: {str(e)}")
    
    def _extract_sections(self, content: str) -> List[str]:
        """Extract section headings from content"""
        sections = []
        lines = content.split('\n')
        for line in lines:
            # Look for markdown headings
            if line.strip().startswith('#'):
                sections.append(line.strip('#').strip())
        return sections

    def _save_content(self, cdp: str, content: List[Dict]):
        """Save content with validation and error handling"""
        if not content:
            logger.warning(f"No content to save for {cdp}")
            return
            
        filepath = self.data_dir / f'{cdp}_docs.json'
        try:
            # Validate content structure
            for article in content:
                if not all(key in article for key in ['title', 'content', 'url']):
                    raise ValueError(f"Invalid article structure in {cdp} content")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(content)} articles for {cdp}")
        except Exception as e:
            logger.error(f"Error saving content for {cdp}: {str(e)}")
            raise