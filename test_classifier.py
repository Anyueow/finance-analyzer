import pandas as pd
from transformers import pipeline
import logging
import time

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_classifier():
    logger.info("Loading zero-shot classifier...")
    start_time = time.time()
    classifier = pipeline(
        "zero-shot-classification",
        model="typeform/distilbert-base-uncased-mnli"
    )
    logger.info(f"Classifier loaded in {time.time() - start_time:.2f} seconds")
    return classifier

def test_classifier(classifier, text, candidate_labels):
    logger.info(f"Testing classification for text: '{text}'")
    logger.info(f"Candidate labels: {candidate_labels}")
    
    try:
        start_time = time.time()
        result = classifier(text, candidate_labels)
        logger.info(f"Classification completed in {time.time() - start_time:.2f} seconds")
        
        logger.info(f"Raw result: {result}")
        logger.info(f"Top label: {result['labels'][0]}")
        logger.info(f"Top score: {result['scores'][0]:.4f}")
        logger.info(f"All scores: {dict(zip(result['labels'], result['scores']))}")
        
        return result
    except Exception as e:
        logger.error(f"Error during classification: {str(e)}")
        raise

def main():
    # Load classifier
    classifier = load_classifier()
    
    # Test cases
    test_cases = [
        ("Walmart Grocery", ["Food", "Shopping", "Entertainment", "Transportation"]),
        ("Shell Gas Station", ["Transportation", "Food", "Shopping"]),
        ("Netflix Subscription", ["Entertainment", "Shopping"]),
        ("Rent Payment", ["Housing", "Utilities"]),
        ("Electric Bill", ["Utilities", "Housing"]),
        ("Gym Membership", ["Health & Wellness", "Entertainment"]),
        ("Amazon Purchase", ["Shopping", "Entertainment"]),
        ("Starbucks Coffee", ["Food", "Entertainment"]),
        ("Uber Ride", ["Transportation", "Entertainment"]),
        ("Doctor Visit", ["Health & Wellness", "Insurance"])
    ]
    
    logger.info("Starting classification tests...")
    for text, labels in test_cases:
        logger.info("\n" + "="*50)
        test_classifier(classifier, text, labels)
        time.sleep(1)  # Add delay to avoid rate limiting

if __name__ == "__main__":
    main() 