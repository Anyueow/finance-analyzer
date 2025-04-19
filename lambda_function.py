import boto3
import csv
import logging
import tempfile
import json
import os
import io
from datetime import datetime

import pymysql

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

# ─── Configuration ─────────────────────────────────────────────────────────────
SOURCE_BUCKET = "first-bucket-raw"
DEST_BUCKET = "processed-data-finance-analyzer"

# S3 bucket where your cleaned CSVs land
CLEANED_BUCKET = "processed-data-finance-analyzer"

# RDS connection settings
RDS_HOST     = "ds4300-rds-finance-analyzer.c0t46g0ic3b7.us-east-1.rds.amazonaws.com"
RDS_PORT     = 3306
RDS_USER     = "admin"
RDS_PASSWORD = "password"
RDS_DB       = "finance_tracker"

# Target table
TABLE_NAME = "processed_transactions"

# ─── Clients & Logging ─────────────────────────────────────────────────────────

s3     = boto3.client("s3")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def check_s3_access():
    """Verify S3 bucket access"""
    s3 = boto3.client('s3')
    try:
        s3.head_bucket(Bucket=SOURCE_BUCKET)
        s3.head_bucket(Bucket=DEST_BUCKET)
        return True
    except Exception as e:
        logger.error(f"S3 access check failed: {str(e)}")
        return False

def process_csv_file(raw_file_path, processed_file_path):
    """Process the CSV file and return number of rows processed"""
    rows_processed = 0
    try:
        with open(raw_file_path, 'r', newline='', encoding='utf-8') as raw_file:
            reader = csv.DictReader(raw_file)
            with open(processed_file_path, 'w', newline='', encoding='utf-8') as proc_file:
                writer = csv.DictWriter(proc_file, fieldnames=['date','description','amount','category'])
                writer.writeheader()

                for row in reader:
                    date = row.get('Date') or row.get('date')
                    desc = row.get('Description') or row.get('description','')
                    debit = row.get('Debit (-)') or row.get('Debit')
                    credit = row.get('Credit (+)') or row.get('Credit')
                    category = row.get('Category') or row.get('category','')

                    if not date:
                        logger.warning(f"Skipping row with no date: {row}")
                        continue

                    try:
                        if debit and debit.strip():
                            amt = -float(debit.replace(',', ''))
                        elif credit and credit.strip():
                            amt = float(credit.replace(',', ''))
                        else:
                            logger.warning(f"Skipping row with no amount: {row}")
                            continue
                    except ValueError:
                        logger.warning(f"Invalid amount {debit or credit} in row: {row}")
                        continue

                    writer.writerow({
                        'date': date,
                        'description': desc,
                        'amount': f"{amt:.2f}",
                        'category': category
                    })
                    rows_processed += 1
                    
        return rows_processed
    except Exception as e:
        logger.error(f"Error processing CSV: {str(e)}")
        raise

def validate_date(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        logger.warning(f"Invalid date format: {date_str}")
        return None

def validate_amount(amount_str):
    try:
        return float(amount_str)
    except (ValueError, TypeError):
        logger.warning(f"Invalid amount: {amount_str}")
        return 0.0

def check_rds_connection():
    """Test RDS connection and return True if successful"""
    try:
        conn = pymysql.connect(
            host     = RDS_HOST,
            user     = RDS_USER,
            password = RDS_PASSWORD,
            database = RDS_DB,
            port     = RDS_PORT,
            connect_timeout=5
        )
        conn.close()
        return True
    except Exception as e:
        logger.error(f"RDS connection failed: {str(e)}")
        return False

def archive_file(bucket, key):
    """Archive a file by moving it to the archive folder"""
    try:
        # Extract filename from key
        filename = os.path.basename(key)
        archive_key = f"archive/{filename}"
        
        # Copy to archive location
        s3.copy_object(
            Bucket=bucket,
            Key=archive_key,
            CopySource={'Bucket': bucket, 'Key': key}
        )
        
        # Delete original
        s3.delete_object(Bucket=bucket, Key=key)
        logger.info(f"Archived {key} to {archive_key}")
    except Exception as e:
        logger.error(f"Failed to archive {key}: {str(e)}")
        raise

def lambda_handler(event, context):
    """Main Lambda handler"""
    try:
        # Log the incoming event
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Check S3 access first
        if not check_s3_access():
            raise Exception("Failed to access S3 buckets")

        # Validate event structure
        if 'Records' not in event:
            raise ValueError("Event does not contain 'Records' array")
        if not event['Records']:
            raise ValueError("'Records' array is empty")
        if 's3' not in event['Records'][0]:
            raise ValueError("First record does not contain 's3' object")
            
        # Extract S3 details
        record = event['Records'][0]['s3']
        src_bucket = record['bucket']['name']
        src_key = record['object']['key']
        logger.info(f"Processing file: {src_key} from bucket: {src_bucket}")

        # Validate source bucket
        if src_bucket != SOURCE_BUCKET:
            raise ValueError(f"Unexpected source bucket: {src_bucket}. Expected: {SOURCE_BUCKET}")

        s3 = boto3.client('s3')
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as raw_tf, \
             tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as proc_tf:
            
            # Download source file
            logger.info(f"Downloading {src_key} to {raw_tf.name}")
            s3.download_file(src_bucket, src_key, raw_tf.name)
            
            # Process the file
            rows_processed = process_csv_file(raw_tf.name, proc_tf.name)
            logger.info(f"Processed {rows_processed} rows")
            
            if rows_processed == 0:
                raise ValueError(f"No valid rows found in {src_key}")
            
            # Upload to destination bucket
            logger.info(f"Uploading to {DEST_BUCKET}/{src_key}")
            s3.upload_file(proc_tf.name, DEST_BUCKET, src_key)
            
            # Archive original file
            archive_file(src_bucket, src_key)
            
            # Cleanup temporary files
            os.unlink(raw_tf.name)
            os.unlink(proc_tf.name)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f"Successfully processed {src_key}",
                'rows_processed': rows_processed,
                'source_bucket': src_bucket,
                'destination_bucket': DEST_BUCKET,
                'archived_path': f"archive/{src_key}"
            })
        }

    except Exception as e:
        error_msg = f"Lambda execution failed: {str(e)}"
        logger.error(error_msg)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_msg,
                'event': event
            })
        }

    # ─── 1) Download & parse the CSV ─────────────────────────────────────────────
    try:
        obj = s3.get_object(Bucket=src_bucket, Key=src_key)
        text = obj["Body"].read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        logger.info("Read %d transactions from %s", len(rows), src_key)
    except Exception as e:
        logger.error("Failed to fetch or parse %s: %s", src_key, e, exc_info=True)
        return {"statusCode": 500, "body": "S3 read error"}

    # ─── 2) Write into RDS ────────────────────────────────────────────────────────
    try:
        conn = pymysql.connect(
            host     = RDS_HOST,
            user     = RDS_USER,
            password = RDS_PASSWORD,
            database = RDS_DB,
            port     = RDS_PORT,
            autocommit=True
        )
    except Exception as e:
        logger.error("Could not connect to RDS: %s", e, exc_info=True)
        return {"statusCode": 500, "body": "DB connection error"}

    inserted = 0
    try:
        with conn.cursor() as cur:
            # Ensure table exists
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                  id                INT AUTO_INCREMENT PRIMARY KEY,
                  transaction_date  DATE,
                  description       VARCHAR(255),
                  amount            DECIMAL(16,2),
                  category          VARCHAR(100)
                ) CHARACTER SET utf8mb4;
            """)

            # Prepare insert statement
            sql = f"""
                INSERT INTO {TABLE_NAME}
                  (transaction_date, description, amount, category)
                VALUES (%s, %s, %s, %s)
            """

            # Batch up the rows
            batch = []
            for r in rows:
                txn_date = validate_date(r.get("date") or r.get("transaction_date"))
                desc = (r.get("description") or "").strip()
                amt = validate_amount(r.get("amount") or r.get("transaction_amount"))
                cat = (r.get("category") or "").strip()
                
                if txn_date:  # Only include rows with valid dates
                    batch.append((txn_date, desc, amt, cat))

            if batch:
                cur.executemany(sql, batch)
                inserted = len(batch)
                logger.info("Inserted %d rows into %s", inserted, TABLE_NAME)

    except Exception as e:
        logger.error("DB write failure: %s", e, exc_info=True)
        return {"statusCode": 500, "body": "DB write error"}

    finally:
        conn.close()

    # Archive the file after successful processing
    try:
        archive_file(src_bucket, src_key)
    except Exception as e:
        logger.error("Failed to archive file: %s", e, exc_info=True)
        return {"statusCode": 500, "body": "Archive failed"}

    return {
        "statusCode": 200,
        "body": f"Successfully inserted {inserted} transactions into {TABLE_NAME}"
    } 