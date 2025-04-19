import pymysql
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

# RDS connection settings
RDS_HOST     = "ds4300-rds-finance-analyzer.c0t46g0ic3b7.us-east-1.rds.amazonaws.com"
RDS_PORT     = 3306
RDS_USER     = "admin"
RDS_PASSWORD = "password"
RDS_DB       = "finance_tracker"

def test_connection():
    try:
        logger.info("Attempting to connect to RDS...")
        logger.info(f"Host: {RDS_HOST}")
        logger.info(f"Database: {RDS_DB}")
        
        # Try to connect with a short timeout
        conn = pymysql.connect(
            host=RDS_HOST,
            user=RDS_USER,
            password=RDS_PASSWORD,
            database=RDS_DB,
            port=RDS_PORT,
            connect_timeout=5
        )
        
        logger.info("Successfully connected to RDS!")
        
        # Test a simple query
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
            logger.info(f"Test query result: {result}")
        
        conn.close()
        return True
        
    except pymysql.Error as e:
        logger.error(f"MySQL Error: {str(e)}")
        logger.error(f"Error code: {e.args[0]}")
        logger.error(f"Error message: {e.args[1]}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection() 