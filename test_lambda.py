import boto3
import csv
import logging
import tempfile
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# ─── Configuration ─────────────────────────────────────────────────────────────
SOURCE_BUCKET = os.getenv('RAW_BUCKET')  # first-bucket-raw
DEST_BUCKET = os.getenv('CLEANED_BUCKET')  # processed-data-finance-analyzer

def test_s3_permissions():
    """Test S3 bucket permissions"""
    s3 = boto3.client('s3')
    try:
        # Test source bucket access
        logger.info(f"Testing access to source bucket: {SOURCE_BUCKET}")
        s3.head_bucket(Bucket=SOURCE_BUCKET)
        
        # Test destination bucket access
        logger.info(f"Testing access to destination bucket: {DEST_BUCKET}")
        s3.head_bucket(Bucket=DEST_BUCKET)
        
        # List contents of source bucket
        logger.info(f"Listing contents of source bucket: {SOURCE_BUCKET}")
        response = s3.list_objects_v2(Bucket=SOURCE_BUCKET)
        if 'Contents' in response:
            for obj in response['Contents']:
                logger.info(f"Found file: {obj['Key']}")
        else:
            logger.warning(f"No files found in {SOURCE_BUCKET}")
            
        return True
    except Exception as e:
        logger.error(f"Error testing S3 permissions: {str(e)}")
        return False

def test_lambda_handler():
    """Test the Lambda handler with a sample event"""
    # Create a sample S3 event
    test_event = {
        'Records': [{
            's3': {
                'bucket': {
                    'name': SOURCE_BUCKET
                },
                'object': {
                    'key': 'test.csv'
                }
            }
        }]
    }
    
    # Create a test CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as test_csv:
        writer = csv.writer(test_csv)
        writer.writerow(['Date', 'Description', 'Debit (-)', 'Credit (+)', 'Category'])
        writer.writerow(['2024-01-01', 'Test Transaction', '50.00', '', 'Shopping'])
        test_csv_path = test_csv.name
    
    # Upload test file to S3
    s3 = boto3.client('s3')
    try:
        logger.info(f"Uploading test file to {SOURCE_BUCKET}/test.csv")
        s3.upload_file(test_csv_path, SOURCE_BUCKET, 'test.csv')
    except Exception as e:
        logger.error(f"Error uploading test file: {str(e)}")
        return False
    
    # Call lambda_handler with test event
    try:
        result = lambda_handler(test_event, None)
        logger.info(f"Lambda handler result: {result}")
        return True
    except Exception as e:
        logger.error(f"Error in lambda handler: {str(e)}")
        return False
    finally:
        # Cleanup test file
        os.unlink(test_csv_path)

if __name__ == "__main__":
    print("Testing S3 permissions...")
    if test_s3_permissions():
        print("\nS3 permissions test passed!")
    else:
        print("\nS3 permissions test failed!")
        exit(1)
        
    print("\nTesting Lambda handler...")
    if test_lambda_handler():
        print("\nLambda handler test passed!")
    else:
        print("\nLambda handler test failed!")
        exit(1) 