from difflib import get_close_matches
from typing import Dict, List, Optional
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path
import json
import logging
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)

class CDPKnowledgeBase:
    def __init__(self):
        # Document structure with screenshots and normalized terminology
        self.documents = {
            'segment_source': {
                'title': 'Setting up a Source in Segment',
                'keywords': [
                    'source', 'segment', 'setup', 'tracking', 'collect', 'data', 
                    'add source', 'new source', 'create source', 'configure source',
                    'how to source', 'segment source', 'data source'
                ],
                'content': """
                To set up a new source in Segment:
                1. Log in to your Segment workspace
                2. Go to Connections > Sources in the left navigation
                3. Click "Add Source" button
                4. Select your source type (Website, Mobile App, Server, etc.)
                5. Name your source and click "Add Source"
                6. Follow the source-specific setup instructions
                7. Configure your settings and preferences
                8. Enable the source when ready

                Common source types:
                • Analytics.js for websites
                • iOS/Android SDKs for mobile apps
                • Server-side libraries
                • Cloud sources for SaaS tools
                """,
                'screenshots': [
                    {'path': '/static/images/segment/add-source.png', 'caption': 'Adding a new source'},
                    {'path': '/static/images/segment/source-config.png', 'caption': 'Source configuration'}
                ]
            },
            'mparticle_profile': {
                'title': 'Creating User Profiles in mParticle',
                'keywords': [
                    'profile', 'mparticle', 'user', 'identity', 'customer',
                    'create profile', 'user profile', 'customer profile',
                    'how to profile', 'mparticle profile', 'setup profile'
                ],
                'content': """
                To create and manage user profiles in mParticle:
                1. Implement identity management
                2. Set up user attributes
                3. Configure identity priority
                4. Define user identity mapping
                5. Enable cross-platform identity resolution

                Key concepts:
                • Customer IDs
                • Device IDs
                • User attributes
                • Identity resolution
                """
            },
            'lytics_audience': {
                'title': 'Building Audience Segments in Lytics',
                'keywords': [
                    'audience', 'lytics', 'segment', 'targeting', 'segmentation',
                    'create audience', 'build segment', 'audience segment',
                    'how to audience', 'lytics segment', 'setup audience'
                ],
                'content': """
                To build an audience segment in Lytics:
                1. Go to Audiences in your Lytics account
                2. Click "Create New Audience"
                3. Define segment criteria
                4. Set behavioral rules
                5. Add profile attributes
                6. Configure content affinities
                7. Set audience rules
                8. Save and activate

                Best practices:
                • Start with broad criteria
                • Use behavioral data
                • Test audience sizes
                • Monitor audience growth
                """
            },
            'zeotap_integration': {
                'title': 'Integrating Data with Zeotap',
                'keywords': [
                    'zeotap', 'integration', 'data', 'connect', 'setup', 'configure',
                    'how to integrate', 'zeotap integration', 'data integration'
                ],
                'content': """
                To integrate your data with Zeotap:
                1. Log in to your Zeotap account
                2. Navigate to the Integrations section
                3. Click "Add Integration"
                4. Select your data source type
                5. Follow the setup instructions for your specific source
                6. Configure your integration settings
                7. Test the integration to ensure data flow
                8. Activate the integration when ready

                Tips:
                • Ensure your data is clean and formatted correctly
                • Use Zeotap's data mapping tools for accurate integration
                • Monitor data flow regularly to catch any issues early
                """
            },
            'segment_advanced': {
                'title': 'Advanced Configurations in Segment',
                'keywords': [
                    'advanced', 'configuration', 'segment', 'custom', 'setup', 'tracking plan',
                    'protocols', 'data governance', 'schema', 'validation'
                ],
                'content': """
                Advanced configurations in Segment include:
                1. Setting up a Tracking Plan:
                   - Define your data schema
                   - Use Protocols to enforce data quality
                   - Validate incoming data against your schema

                2. Custom Destinations:
                   - Create custom integrations using Functions
                   - Use the Segment API for advanced data routing

                3. Data Governance:
                   - Implement data access controls
                   - Monitor data flow and quality

                Tips:
                • Regularly review and update your tracking plan
                • Use Segment's debugging tools to troubleshoot issues
                """
            },
            'mparticle_advanced': {
                'title': 'Advanced Integrations in mParticle',
                'keywords': [
                    'advanced', 'integration', 'mparticle', 'custom', 'setup', 'sdk',
                    'api', 'data pipeline', 'real-time', 'event processing'
                ],
                'content': """
                Advanced integrations in mParticle include:
                1. Real-time Event Processing:
                   - Use mParticle's SDKs for real-time data collection
                   - Implement custom event processing logic

                2. API Integrations:
                   - Use mParticle's API for custom data flows
                   - Integrate with third-party services

                3. Data Pipeline Management:
                   - Configure data routing and transformation
                   - Monitor data flow and performance

                Tips:
                • Leverage mParticle's developer resources for custom integrations
                • Test integrations thoroughly before deployment
                """
            },
            'lytics_advanced': {
                'title': 'Advanced Audience Building in Lytics',
                'keywords': [
                    'advanced', 'audience', 'lytics', 'segmentation', 'personalization',
                    'machine learning', 'predictive', 'scoring', 'content affinity'
                ],
                'content': """
                Advanced audience building in Lytics includes:
                1. Predictive Scoring:
                   - Use machine learning models to score users
                   - Predict user behavior and preferences

                2. Content Affinity:
                   - Analyze user interactions to determine content preferences
                   - Personalize content delivery based on affinity scores

                3. Dynamic Segmentation:
                   - Create segments that update in real-time
                   - Use behavioral data for precise targeting

                Tips:
                • Continuously refine your models for better accuracy
                • Use Lytics' insights to drive personalized marketing campaigns
                """
            },
            'segment_analytics': {
                'title': 'Implementing Segment Analytics.js',
                'content': """
                To implement Segment's Analytics.js on your website:
                1. Get your Segment write key from your source settings
                2. Add the Analytics.js snippet to your website:
                   ```
                   <script>
                     !function(){var analytics=window.analytics=window.analytics||[];...}();
                   </script>
                   ```
                3. Initialize with your write key:
                   ```
                   analytics.load("YOUR_WRITE_KEY");
                   ```
                4. Start tracking events:
                   ```
                   analytics.track("Event Name", {
                     property: value
                   });
                   ```
                
                Best Practices:
                - Place the snippet in the <head> tag
                - Initialize as early as possible
                - Use a data layer for dynamic properties
                - Test with the Segment debugger
                """,
                'keywords': ['analytics.js', 'implement', 'website', 'tracking', 'javascript']
            },
            
            'mparticle_ios': {
                'title': 'Configuring mParticle iOS SDK',
                'content': """
                To configure mParticle's iOS SDK:
                1. Install the SDK:
                   ```
                   pod 'mParticle-Apple-SDK'
                   ```
                
                2. Initialize in AppDelegate:
                   ```swift
                   let options = MParticleOptions(key: "APP-KEY", secret: "APP-SECRET")
                   MParticle.sharedInstance().start(with: options)
                   ```
                
                3. Configure user identity:
                   - Set customer ID
                   - Add email or other identifiers
                   - Enable identity sync
                
                4. Implement tracking:
                   - Screen views
                   - Custom events
                   - Commerce events
                
                5. Test implementation using:
                   - Live Stream
                   - Debug logging
                   - Data Master validation
                """,
                'keywords': ['ios', 'sdk', 'mobile', 'apple', 'swift']
            }
        }

        # Add terminology mapping
        self.term_mapping = {
            'segment': {
                'workspace': ['project', 'account'],
                'source': ['tracker', 'integration'],
                'destination': ['connection', 'integration']
            },
            'mparticle': {
                'workspace': ['account', 'environment'],
                'input': ['source', 'integration'],
                'output': ['destination', 'connection']
            }
        }

        # Add comparison documents
        self.comparisons = {
            'audience_creation': {
                'title': 'Audience Creation Comparison',
                'content': """
                Comparing audience creation across CDPs:

                Segment:
                - Uses Personas for audience building
                - SQL-based audience definitions
                - Real-time computation

                Lytics:
                - Visual audience builder
                - Machine learning scoring
                - Behavioral triggers

                Key differences:
                - Segment focuses on SQL-powered definitions
                - Lytics emphasizes ML-driven behavioral scoring
                """,
                'keywords': ['compare', 'comparison', 'difference', 'versus', 'vs']
            }
        }

        # Add conversation patterns
        self.conversation_patterns = {
            r'hi|hello|hey': self._greeting_response,
            r'thank|thanks': self._thank_response,
            r'bye|goodbye': self._goodbye_response,
            r'help|assist': self._help_response,
            r'what can you do|what do you do': self._capabilities_response
        }

        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.vectors = None
        self.base_dir = Path(__file__).resolve().parent.parent
        self.docs_dir = self.base_dir / 'data' / 'docs'
        self.index_dir = self.base_dir / 'data' / 'index'
        
        # Create directories if they don't exist
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.indexes = self._load_indexes()
        try:
            self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        except Exception as e:
            logger.error(f"Error loading SentenceTransformer: {e}")
            self.model = None
        self.cdp_vectors = {}
        self.cdp_docs = {}

    def initialize_vectors(self):
        """Initialize TF-IDF vectors for improved search"""
        texts = [doc['content'] for doc in self.documents.values()]
        self.vectors = self.vectorizer.fit_transform(texts)
        """Load documents and create vector embeddings for search"""
        if not self.model:
            logger.error("SentenceTransformer not initialized, vector search disabled")
            return

        try:
            texts = [doc['content'] for doc in self.documents.values()]
            self.vectors = self.vectorizer.fit_transform(texts)
            
            # Process each CDP's documents
            for cdp_file in self.docs_dir.glob('*_docs.json'):
                try:
                    cdp_name = cdp_file.stem.split('_')[0]
                    
                    with open(cdp_file, 'r', encoding='utf-8') as f:
                        docs = json.load(f)
                        
                    if not docs:  # Skip empty documents
                        continue
                        
                    self.cdp_docs[cdp_name] = docs
                    vectors = []
                    
                    for doc in docs:
                        if not all(k in doc for k in ['title', 'content']):
                            logger.warning(f"Missing required fields in {cdp_name} document")
                            continue
                            
                        text = f"{doc['title']} {doc['content']}"
                        vector = self.model.encode(text, convert_to_numpy=True)
                        vectors.append(vector)
                    
                    if vectors:  # Only store if we have valid vectors
                        self.cdp_vectors[cdp_name] = np.array(vectors)
                        
                except Exception as e:
                    logger.error(f"Error processing {cdp_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Vector initialization failed: {e}")

    def _load_indexes(self) -> Dict:
        """Load document indexes"""
        indexes = {}
        if not self.index_dir.exists():
            return indexes
            
        for index_file in self.index_dir.glob('*_index.json'):
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    cdp = index_file.stem.replace('_index', '')
                    indexes[cdp] = json.load(f)
            except Exception as e:
                logger.error(f"Error loading index {index_file}: {str(e)}")
        return indexes

    def search(self, query: str, top_k: int = 3) -> dict:
        """Search for relevant documents using vector similarity"""
        if not self.model or not self.cdp_vectors:
            logger.warning("Vector search not available, returning default response")
            return self._get_default_response()
            
        try:
            # Encode the query
            query_vector = self.model.encode(query, convert_to_numpy=True)
            
            all_results = []
            # Search in each CDP's documents
            for cdp_name, vectors in self.cdp_vectors.items():
                if vectors.size == 0:
                    continue
                    
                # Calculate similarity
                similarities = cosine_similarity([query_vector], vectors)[0]
                
                # Get top matches
                top_indices = np.argsort(similarities)[::-1][:top_k]
                
                for idx in top_indices:
                    if similarities[idx] > 0.3:  # Threshold for relevance
                        result = self.cdp_docs[cdp_name][idx].copy()
                        result['score'] = float(similarities[idx])
                        result['cdp'] = cdp_name
                        all_results.append(result)
            
            # Sort by similarity score
            all_results.sort(key=lambda x: x['score'], reverse=True)
            
            if not all_results:
                return self._get_default_response()
                
            # Return the most relevant result
            best_match = all_results[0]
            return {
                'title': best_match['title'],
                'content': best_match['content'],
                'score': best_match['score'],
                'url': best_match.get('url', '')
            }
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return self._get_default_response()

    def _get_default_response(self) -> Dict:
        """Return default response when no match is found"""
        return {
            'title': 'How can I help you?',
            'content': """
            I can help you with:
            1. Setting up sources in Segment
            2. Creating user profiles in mParticle
            3. Building audience segments in Lytics

            Please try:
            • Being specific about which CDP you're asking about
            • Mentioning the feature you're interested in (source, profile, audience)
            """
        }

    def _greeting_response(self) -> Dict:
        return {
            'title': 'Hello! 👋',
            'content': """
            Hi! I'm your CDP assistant. I can help you with:
            • Setting up sources in Segment
            • Creating user profiles in mParticle
            • Building audience segments in Lytics

            What would you like to know about?
            """
        }

    def _thank_response(self) -> Dict:
        return {
            'title': 'You\'re Welcome! 😊',
            'content': """
            Happy to help! Let me know if you have any other questions about:
            • Segment sources and destinations
            • mParticle user profiles
            • Lytics audience segments

            Thanks for chatting! Feel free to come back if you have more questions about CDPs.
            """
        }

    def _goodbye_response(self) -> Dict:
        return {
            'title': 'Goodbye! 👋',
            'content': """
            Thanks for chatting! Feel free to come back if you have more questions about CDPs.
            Have a great day!
            """
        }

    def _help_response(self) -> Dict:
        return {
            'title': 'How Can I Help? 🤝',
            'content': """
            I can help you with various CDP tasks:
            1. Segment:
            • Setting up data sources
            • Configuring destinations
            • Managing tracking

            2. mParticle:
            • Creating user profiles
            • Identity management
            • Data mapping

            3. Lytics:
            • Building audiences
            • Segmentation rules
            • Campaign activation

            Just ask me specific questions about any of these topics!
            """
        }

    def _capabilities_response(self) -> Dict:
        return {
            'title': 'My Capabilities 💡',
            'content': """
            I'm a specialized CDP assistant that can help you with:
            1. Step-by-step guides for:
            • Segment implementation
            • mParticle setup
            • Lytics configuration

            2. Best practices for:
            • Data collection
            • User identification
            • Audience building

            3. Technical documentation for:
            • API integrations
            • SDK implementations
            • Data mapping

            Try asking specific questions about these topics!
            """
        }

    def _cdp_overview_response(self) -> Dict:
        return {
            'title': 'Customer Data Platform (CDP) Overview',
            'content': """
            A CDP helps you collect, unify, and activate customer data:
            1. Segment - Leading CDP for data collection
            2. mParticle - Mobile-first CDP
            3. Lytics - AI-driven CDP

            Key Features:
            • Data Collection (Sources)
            • Identity Resolution
            • Audience Segmentation
            • Data Activation (Destinations)

            What specific aspect would you like to learn about?
            """
        }

    def _normalize_terminology(self, query: str) -> str:
        """Normalize terminology variations in the query"""
        normalized = query.lower()
        for cdp, terms in self.term_mapping.items():
            if cdp in normalized:
                for standard, variants in terms.items():
                    for variant in variants:
                        normalized = normalized.replace(variant, standard)
        return normalized