import asyncio
import logging
from app.vector_search import VectorSearch

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("feedback_integration")

async def run_feedback_integration():
    """
    Process user feedback corrections and add them to the vector store.
    """
    try:
        logger.info("Starting feedback integration")
        
        vector_search = VectorSearch()
        added_count = await vector_search.add_feedback_corrections_to_vector_store()
        
        logger.info(f"Added {added_count} corrections to vector store")
        return {"status": "success", "corrections_added": added_count}
        
    except Exception as e:
        logger.error(f"Error during feedback integration: {str(e)}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    result = asyncio.run(run_feedback_integration())
    logger.info(f"Result: {result}")