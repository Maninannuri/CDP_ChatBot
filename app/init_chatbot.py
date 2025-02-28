from app.scraper import DocumentationScraper
import os
from pathlib import Path
import json
import logging
import sys
import time
import psutil
import signal

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scraper.log')
    ]
)
logger = logging.getLogger(__name__)

def cleanup_webdrivers():
    """Ensure all WebDriver processes are properly terminated"""
    # Suppress all warnings during cleanup
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        old_stderr = sys.stderr
        try:
            with open(os.devnull, 'w') as null_file:
                sys.stderr = null_file
                # List of process names to check for
                driver_processes = ['chromedriver', 'chrome.exe', 'undetected_chromedriver']
                
                # First try graceful shutdown
                time.sleep(1)
                
                # Then force terminate remaining processes
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if any(driver_name.lower() in proc.info['name'].lower() 
                              for driver_name in driver_processes):
                            cmdline = proc.info.get('cmdline', [])
                            if any('--headless' in cmd for cmd in cmdline if cmd):
                                try:
                                    if os.name == 'nt':
                                        proc.terminate()
                                        time.sleep(0.5)
                                        if proc.is_running():
                                            proc.kill()
                                    else:
                                        os.killpg(os.getpgid(proc.info['pid']), signal.SIGTERM)
                                except:
                                    pass
                    except:
                        continue
        finally:
            sys.stderr = old_stderr

def init():
    # Create necessary directories
    docs_dir = Path("data/docs")
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    index_dir = Path("data/index")
    index_dir.mkdir(parents=True, exist_ok=True)
    
    print("Initializing CDP documentation scraper...")
    scraper = None
    try:
        scraper = DocumentationScraper()
        scraper.scrape_documentation()
        
        # Verify the scraped data
        verify_scraping(docs_dir)
    except Exception as e:
        logger.error(f"Initialization failed: {str(e)}")
        print(f"ERROR: Initialization failed - {str(e)}")
    finally:
        try:
            # Clean up WebDriver resources
            if scraper:
                for cdp_scraper in scraper.scrapers.values():
                    if hasattr(cdp_scraper, 'driver') and cdp_scraper.driver:
                        try:
                            cdp_scraper.driver.quit()
                        except:
                            pass
            
            # Add delay and cleanup
            time.sleep(2)
            try:
                cleanup_webdrivers()
                logger.info("Cleanup completed")
            except OSError as e:
                if "[WinError 6] The handle is invalid" in str(e):
                    logger.info("Ignoring expected invalid handle error during cleanup")
                else:
                    logger.error(f"Error during cleanup: {e}")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

def verify_scraping(docs_dir):
    """Verify that documentation was scraped and saved properly"""
    print("\nVerifying scraped documentation:")
    found_files = list(docs_dir.glob('*_docs.json'))
    
    if not found_files:
        print("Warning: No documentation files were created!")
        return
        
    total_articles = 0
    for file_path in found_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                total_articles += len(data)
                print(f"\n{file_path.name}:")
                print(f"- Number of articles: {len(data)}")
                if data:
                    print(f"- First article title: {data[0]['title']}")
                    content_preview = data[0]['content']
                    if len(content_preview) > 200:
                        content_preview = content_preview[:200] + "..."
                    print(f"- Content preview: {content_preview}")
        except Exception as e:
            print(f"Error reading {file_path}: {str(e)}")
    
    print(f"\nTotal articles across all CDPs: {total_articles}")
    
    # Check for empty or very small files
    small_files = [f for f in found_files if os.path.getsize(f) < 1000]
    if small_files:
        print("\nWarning: The following files are suspiciously small:")
        for f in small_files:
            print(f"- {f.name} ({os.path.getsize(f)} bytes)")

if __name__ == "__main__":
    init()