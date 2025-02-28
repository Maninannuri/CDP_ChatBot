from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

def verify_data():
    """Verify data storage structure and content"""
    base_dir = Path(__file__).resolve().parent.parent.parent
    docs_dir = base_dir / 'data' / 'docs'
    index_dir = base_dir / 'data' / 'index'
    
    # Check directory structure
    logger.info("Checking directory structure...")
    if not docs_dir.exists():
        logger.error(f"Docs directory missing: {docs_dir}")
        return False
    if not index_dir.exists():
        logger.error(f"Index directory missing: {index_dir}")
        return False
        
    # Check doc files
    doc_files = list(docs_dir.glob('*_docs.json'))
    if not doc_files:
        logger.error("No documentation files found!")
        return False
        
    # Verify content structure
    valid_files = True
    for doc_file in doc_files:
        try:
            with open(doc_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, list):
                    logger.error(f"{doc_file.name}: Invalid format (should be list)")
                    valid_files = False
                    continue
                    
                # Check required fields
                for idx, doc in enumerate(data):
                    if not all(k in doc for k in ['title', 'content', 'url']):
                        logger.error(f"{doc_file.name}: Missing required fields in document {idx}")
                        valid_files = False
                        
                logger.info(f"{doc_file.name}: {len(data)} documents")
                
        except Exception as e:
            logger.error(f"Error reading {doc_file}: {e}")
            valid_files = False
            
    return valid_files

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    is_valid = verify_data()
    print(f"\nData verification {'passed' if is_valid else 'failed'}")
