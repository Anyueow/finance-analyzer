import pymysql
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# RDS connection parameters
rds_config = {
    'host': os.getenv('RDS_HOST'),
    'port': int(os.getenv('RDS_PORT')),
    'user': os.getenv('RDS_USER'),
    'password': os.getenv('RDS_PASSWORD'),
    'db': os.getenv('RDS_DB')
}

try:
    # Attempt to connect to RDS
    print("Attempting to connect to RDS...")
    connection = pymysql.connect(**rds_config)
    
    # If connection successful, list available tables
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print("\n✅ Successfully connected to RDS!")
        print(f"\nAvailable tables in {rds_config['db']}:")
        for table in tables:
            print(f"- {table[0]}")
            
except Exception as e:
    print(f"\n❌ Error connecting to RDS: {e}")
finally:
    if 'connection' in locals():
        connection.close() 