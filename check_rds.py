import pymysql
import boto3
import json
from datetime import datetime, timedelta

# AWS Configuration
AWS_REGION = 'us-east-1'
LAMBDA_FUNCTION = 'second-lambda-categorize'

# RDS Configuration
RDS_CONFIG = {
    'host': 'ds4300-rds-finance-analyzer.c0t46g0ic3b7.us-east-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'password',
    'db': 'finance_tracker',
    'port': 3306
}

def check_rds_data():
    try:
        print("\nAttempting to connect to RDS...")
        print(f"Host: {RDS_CONFIG['host']}")
        print(f"Database: {RDS_CONFIG['db']}")
        
        # Connect to RDS
        conn = pymysql.connect(**RDS_CONFIG)
        cursor = conn.cursor()
        
        # Check table structure
        cursor.execute("DESCRIBE processed_transactions")
        columns = cursor.fetchall()
        print("\nTable Structure:")
        for col in columns:
            print(f"Column: {col[0]}, Type: {col[1]}")
        
        # Check data counts
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT DATE(transaction_date)) as unique_days,
                MIN(transaction_date) as earliest_date,
                MAX(transaction_date) as latest_date
            FROM processed_transactions
        """)
        stats = cursor.fetchone()
        print("\nData Statistics:")
        print(f"Total Records: {stats[0]}")
        print(f"Unique Days: {stats[1]}")
        print(f"Date Range: {stats[2]} to {stats[3]}")
        
        # Check recent data
        cursor.execute("""
            SELECT 
                transaction_date,
                description,
                amount,
                category
            FROM processed_transactions
            ORDER BY transaction_date DESC
            LIMIT 5
        """)
        recent_data = cursor.fetchall()
        print("\nMost Recent Transactions:")
        for row in recent_data:
            print(f"Date: {row[0]}, Description: {row[1]}, Amount: {row[2]}, Category: {row[3]}")
        
        conn.close()
        
    except Exception as e:
        print(f"\nError checking RDS: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Verify RDS security group allows inbound MySQL traffic (port 3306)")
        print("2. Check if your IP address is allowed in the security group")
        print("3. Verify database credentials")
        print("4. Check if the database is in the same VPC as your Lambda function")

def check_lambda_logs():
    try:
        # Initialize CloudWatch client with correct region
        cloudwatch = boto3.client('logs', region_name=AWS_REGION)
        
        # Get log group name for the second Lambda
        log_group = f'/aws/lambda/{LAMBDA_FUNCTION}'
        
        print(f"\nChecking logs for Lambda: {LAMBDA_FUNCTION}")
        print(f"Log Group: {log_group}")
        
        # Get recent log streams
        log_streams = cloudwatch.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=5
        )
        
        print("\nRecent Lambda Executions:")
        for stream in log_streams['logStreams']:
            # Get log events
            events = cloudwatch.get_log_events(
                logGroupName=log_group,
                logStreamName=stream['logStreamName'],
                limit=20
            )
            
            print(f"\nExecution: {stream['logStreamName']}")
            print(f"Last Event Time: {datetime.fromtimestamp(stream['lastEventTimestamp']/1000)}")
            
            # Print relevant log messages
            for event in events['events']:
                message = event['message']
                if any(keyword in message for keyword in ['ERROR', 'error', 'successfully', 'Success', 'START', 'END', 'RDS', 'database']):
                    print(f"  {message}")
                    
    except Exception as e:
        print(f"\nError checking Lambda logs: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Verify Lambda function name is correct")
        print("2. Check if CloudWatch logs are enabled for the Lambda function")
        print("3. Verify IAM permissions for CloudWatch access")

def check_lambda_status():
    try:
        # Initialize Lambda client with correct region
        lambda_client = boto3.client('lambda', region_name=AWS_REGION)
        
        # Get Lambda function details
        response = lambda_client.get_function(
            FunctionName=LAMBDA_FUNCTION
        )
        
        print("\nLambda Function Status:")
        print(f"Function Name: {response['Configuration']['FunctionName']}")
        print(f"Runtime: {response['Configuration']['Runtime']}")
        print(f"Last Modified: {response['Configuration']['LastModified']}")
        print(f"State: {response['Configuration']['State']}")
        
        # Get function configuration
        print("\nFunction Configuration:")
        print(f"Memory Size: {response['Configuration']['MemorySize']} MB")
        print(f"Timeout: {response['Configuration']['Timeout']} seconds")
        print(f"Handler: {response['Configuration']['Handler']}")
        
        # Check VPC configuration
        if 'VpcConfig' in response['Configuration']:
            print("\nVPC Configuration:")
            print(f"VPC ID: {response['Configuration']['VpcConfig']['VpcId']}")
            print(f"Subnets: {response['Configuration']['VpcConfig']['SubnetIds']}")
            print(f"Security Groups: {response['Configuration']['VpcConfig']['SecurityGroupIds']}")
        
    except Exception as e:
        print(f"\nError checking Lambda status: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Verify Lambda function name is correct")
        print("2. Check IAM permissions for Lambda access")
        print("3. Verify the function exists in the correct region")

if __name__ == "__main__":
    print("Checking RDS Data...")
    check_rds_data()
    
    print("\nChecking Lambda Status...")
    check_lambda_status()
    
    print("\nChecking Lambda Logs...")
    check_lambda_logs() 