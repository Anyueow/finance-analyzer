import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar
import re
import io
from decimal import Decimal
import boto3
import uuid
import pymysql
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AWS Configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
RAW_BUCKET = "first-bucket-raw"
s3_client = boto3.client(
    's3',
    region_name=AWS_REGION,
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

# RDS Configuration
RDS_CONFIG = {
    'host': os.getenv('RDS_HOST'),
    'user': os.getenv('RDS_USER'),
    'password': os.getenv('RDS_PASSWORD'),
    'db': os.getenv('RDS_DB'),
    'port': 3306
}

# Set page configuration
st.set_page_config(
    page_title="Personal Finance Insights 💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

def upload_to_s3(file_obj, filename):
    """Upload file to S3 and return the key"""
    unique_key = f"{uuid.uuid4()}_{filename}"
    s3_client.upload_fileobj(file_obj, RAW_BUCKET, unique_key)
    return unique_key

def fetch_transactions() -> Optional[pd.DataFrame]:
    """Fetch transactions from RDS"""
    try:
        conn = pymysql.connect(**RDS_CONFIG)
        query = """
            SELECT transaction_date AS date, description, amount, category
            FROM processed_transactions
            ORDER BY transaction_date ASC
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error connecting to RDS: {str(e)}")
        return None

# Initialize session state
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'show_analysis' not in st.session_state:
    st.session_state.show_analysis = False
if 'monthly_income' not in st.session_state:
    st.session_state.monthly_income = 5000.0
if 'savings_goal' not in st.session_state:
    st.session_state.savings_goal = 10000.0
if 'data_source' not in st.session_state:
    st.session_state.data_source = 'sample'  # 'sample' or 'aws'

# ... existing code ...

def main():
    st.markdown('<div class="main-header">Personal Finance Insights</div>', unsafe_allow_html=True)
    
    with st.expander("How to use this app", expanded=False):
        st.write("""
        1. Choose your data source (Sample or AWS)
        2. If using AWS:
           - Upload your bank statement CSV
           - Wait for processing
           - Click "Fetch My Data" to load processed data
        3. If using Sample:
           - Click "Generate Sample Data"
        4. Enter your monthly income and savings goal
        5. Review your spending analysis and personalized insights
        """)
    
    # Data source selection
    data_source = st.radio(
        "Choose Data Source",
        ["Sample Data", "AWS (Upload & Process)"],
        index=0 if st.session_state.data_source == 'sample' else 1
    )
    
    if data_source == "AWS (Upload & Process)":
        st.session_state.data_source = 'aws'
        
        # File uploader
        uploaded_file = st.file_uploader("Upload your bank statement (CSV)", type=["csv"])
        if uploaded_file:
            st.info("Uploading to AWS...")
            key = upload_to_s3(uploaded_file, uploaded_file.name)
            st.success(f"Uploaded and triggered processing: `{key}`")
            
            if st.button("🔁 Fetch My Data from AWS"):
                with st.spinner("Fetching from RDS..."):
                    df = fetch_transactions()
                    if df is not None:
                        processed_df = process_transactions(df)
                        st.session_state.processed_data = processed_df
                        st.session_state.show_analysis = True
                        st.success("Data loaded!")
                        st.rerun()
    else:
        st.session_state.data_source = 'sample'
        
        # Income and goals input
        col1, col2 = st.columns(2)
        
        with col1:
            st.session_state.monthly_income = st.number_input(
                "Monthly Income (Post-Tax)",
                min_value=0.0,
                value=5000.0,
                step=100.0,
                help="Enter your typical monthly income after taxes"
            )
        
        with col2:
            st.session_state.savings_goal = st.number_input(
                "Savings Goal ($)",
                min_value=0.0,
                value=10000.0,
                step=1000.0,
                help="Enter your savings goal"
            )
        
        # Generate sample data button
        st.markdown('<div class="section-header">Generate Sample Data</div>', unsafe_allow_html=True)
        
        if st.button("Generate Sample Data"):
            with st.spinner("Generating sample data..."):
                # Generate sample data
                df = generate_sample_data()
                
                # Process the data
                processed_df = process_transactions(df)
                
                if processed_df is not None:
                    st.session_state.processed_data = processed_df
                    st.session_state.show_analysis = True
                    st.success("✅ Successfully generated sample data!")
                    st.rerun()
    
    # Show analysis if data is processed
    if st.session_state.show_analysis:
        analyze_data()

if __name__ == "__main__":
    main()