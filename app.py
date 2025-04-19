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
import time

# Load environment variables
load_dotenv()

# AWS Configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
RAW_BUCKET = os.getenv('RAW_BUCKET', 'first-bucket-raw')
PROCESSED_BUCKET = os.getenv('CLEANED_BUCKET', 'processed-data-finance-analyzer')

# Initialize AWS clients
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
    'port': int(os.getenv('RDS_PORT', 3306))
}

# Set page configuration
st.set_page_config(
    page_title="Personal Finance Insights 💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sample benchmark data
BENCHMARKS = {
    'low_income': {  # <50k
        'Housing': 35,
        'Food': 15,
        'Transportation': 15,
        'Entertainment': 5,
        'Shopping': 10,
        'Utilities': 10,
        'Healthcare': 5,
        'Other': 5
    },
    'medium_income': {  # 50k-100k
        'Housing': 30,
        'Food': 12,
        'Transportation': 12,
        'Entertainment': 8,
        'Shopping': 15,
        'Utilities': 8,
        'Healthcare': 8,
        'Other': 7
    },
    'high_income': {  # >100k
        'Housing': 25,
        'Food': 10,
        'Transportation': 10,
        'Entertainment': 12,
        'Shopping': 18,
        'Utilities': 7,
        'Healthcare': 10,
        'Other': 8
    }
}

def upload_to_s3(file_obj, filename):
    """Upload file to S3 and return the key"""
    try:
        unique_key = f"{uuid.uuid4()}_{filename}"
        s3_client.upload_fileobj(file_obj, RAW_BUCKET, unique_key)
        return unique_key
    except Exception as e:
        st.error(f"Error uploading to S3: {str(e)}")
        return None

def wait_for_processing(key, max_wait=30):
    """Wait for Lambda to process the file"""
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            # Check if file exists in processed bucket
            s3_client.head_object(Bucket=PROCESSED_BUCKET, Key=key)
            return True
        except:
            time.sleep(2)  # Wait 2 seconds before checking again
    return False

def get_processed_data(key):
    """Get processed data from S3"""
    try:
        response = s3_client.get_object(Bucket=PROCESSED_BUCKET, Key=key)
        df = pd.read_csv(io.BytesIO(response['Body'].read()))
        return df
    except Exception as e:
        st.error(f"Error fetching processed data: {str(e)}")
        return None

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

def process_transactions(df):
    """Process the transactions dataframe"""
    try:
        # Convert date column to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Ensure amount is numeric
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        
        # Drop any rows with NaN values
        df = df.dropna()
        
        # Sort by date
        df = df.sort_values('date')
        
        return df
    except Exception as e:
        st.error(f"Error processing transactions: {str(e)}")
        return None

def generate_sample_data(num_months=6):
    """Generate sample transaction data"""
    np.random.seed(42)  # For reproducible results
    
    # Define categories and their typical ranges
    categories = {
        'Groceries': (200, 600),
        'Rent': (1000, 1500),
        'Utilities': (100, 300),
        'Entertainment': (50, 300),
        'Shopping': (100, 500),
        'Transportation': (50, 200),
        'Income': (3000, 6000)
    }
    
    # Generate dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30*num_months)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    transactions = []
    
    # Generate monthly recurring transactions
    for month in pd.date_range(start=start_date, end=end_date, freq='M'):
        # Rent (monthly)
        transactions.append({
            'date': month + timedelta(days=1),
            'description': 'Monthly Rent',
            'amount': -np.random.uniform(*categories['Rent']),
            'category': 'Rent'
        })
        
        # Income (monthly)
        transactions.append({
            'date': month + timedelta(days=15),
            'description': 'Salary Deposit',
            'amount': np.random.uniform(*categories['Income']),
            'category': 'Income'
        })
    
    # Generate random transactions
    for _ in range(num_months * 30):  # Average 1 transaction per day
        date = np.random.choice(dates)
        category = np.random.choice([k for k in categories.keys() if k not in ['Rent', 'Income']])
        amount = -np.random.uniform(*categories[category])  # Negative for expenses
        
        transactions.append({
            'date': date,
            'description': f'{category} Transaction',
            'amount': amount,
            'category': category
        })
    
    df = pd.DataFrame(transactions)
    df = df.sort_values('date')
    return df

def analyze_data():
    """Analyze and display financial insights"""
    df = st.session_state.processed_data
    
    # Create tabs for different analysis views
    tabs = st.tabs([
        "Overview 📋",
        "Trend 📈",
        "Categories 🗂️",
        "Benchmark ⚖️",
        "Tips 💡"
    ])
    
    # Overview tab
    with tabs[0]:
        st.markdown("## 📊 Financial Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        # Total Income
        total_income = df[df['amount'] > 0]['amount'].sum()
        with col1:
            st.metric("Total Income", f"${total_income:,.2f}")
        
        # Total Expenses
        total_expenses = abs(df[df['amount'] < 0]['amount'].sum())
        with col2:
            st.metric("Total Expenses", f"${total_expenses:,.2f}")
        
        # Net Savings
        net_savings = total_income - total_expenses
        with col3:
            st.metric("Net Savings", f"${net_savings:,.2f}")
        
        # Savings Rate
        savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0
        with col4:
            st.metric("Savings Rate", f"{savings_rate:.1f}%")
        
        # Monthly averages
        st.subheader("Monthly Averages")
        months_count = df['date'].dt.to_period('M').nunique()
        c1, c2, c3 = st.columns(3)
        c1.metric("Avg Income", f"${total_income/months_count:,.2f}/mo")
        c2.metric("Avg Spending", f"${total_expenses/months_count:,.2f}/mo")
        c3.metric("Avg Savings", f"${net_savings/months_count:,.2f}/mo")
    
    # Trend tab
    with tabs[1]:
        st.markdown("## 📈 Monthly Trends")
        
        # Prepare monthly data
        df['month'] = df['date'].dt.to_period('M')
        monthly_data = df.groupby('month').agg({
            'amount': lambda x: (x[x > 0].sum(), abs(x[x < 0].sum()))
        }).reset_index()
        
        monthly_data[['income', 'expenses']] = pd.DataFrame(monthly_data['amount'].tolist())
        monthly_data['net'] = monthly_data['income'] - monthly_data['expenses']
        monthly_data['month'] = monthly_data['month'].astype(str)
        
        # Create monthly trends chart
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=monthly_data['month'],
            y=monthly_data['income'],
            name='Income',
            marker_color='green'
        ))
        fig.add_trace(go.Bar(
            x=monthly_data['month'],
            y=monthly_data['expenses'],
            name='Expenses',
            marker_color='red'
        ))
        fig.add_trace(go.Scatter(
            x=monthly_data['month'],
            y=monthly_data['net'],
            name='Net Savings',
            line=dict(color='blue', width=2)
        ))
        
        fig.update_layout(
            title='Monthly Income vs Expenses',
            barmode='group',
            xaxis_title='Month',
            yaxis_title='Amount ($)',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Category trends
        st.subheader("Category Trends")
        monthly_cat = df[df['amount'] < 0].groupby(['month', 'category'])['amount'].sum().abs().reset_index()
        monthly_cat['month'] = monthly_cat['month'].astype(str)
        
        fig_area = px.area(
            monthly_cat,
            x="month",
            y="amount",
            color="category",
            title="Monthly Spending by Category"
        )
        st.plotly_chart(fig_area, use_container_width=True)
    
    # Categories tab
    with tabs[2]:
        st.markdown("## 📊 Spending by Category")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Calculate category totals
            category_spending = df[df['amount'] < 0].groupby('category')['amount'].sum().abs()
            
            # Create pie chart
            fig = px.pie(
                values=category_spending,
                names=category_spending.index,
                title='Spending Distribution by Category'
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Category details
            st.subheader("Category Details")
            cat_details = pd.DataFrame({
                'Total': category_spending,
                'Monthly Avg': category_spending / months_count,
                '% of Spending': category_spending / total_expenses * 100
            }).round(2)
            
            st.dataframe(
                cat_details.style.format({
                    'Total': '${:,.2f}',
                    'Monthly Avg': '${:,.2f}',
                    '% of Spending': '{:.1f}%'
                }),
                use_container_width=True
            )
    
    # Benchmark tab
    with tabs[3]:
        st.markdown("## ⚖️ Benchmark Comparison")
        
        # Get appropriate benchmark based on income
        monthly_income = st.session_state.monthly_income
        if monthly_income < 50000:
            benchmark = BENCHMARKS['low_income']
        elif monthly_income < 100000:
            benchmark = BENCHMARKS['medium_income']
        else:
            benchmark = BENCHMARKS['high_income']
        
        # Prepare comparison data
        user_pct = pd.DataFrame({
            'category': category_spending.index.tolist(),
            'You': (category_spending / total_expenses * 100).tolist()
        })
        
        bench_pct = pd.DataFrame({
            'category': list(benchmark.keys()),
            'Benchmark': list(benchmark.values())
        })
        
        comp = pd.merge(user_pct, bench_pct, on='category', how='outer')
        comp = comp.fillna(0)  # Fill NaN values with 0
        
        comp_melt = comp.melt(
            id_vars='category',
            value_vars=['You', 'Benchmark'],
            var_name='Who',
            value_name='Percentage'
        )
        
        # Bar chart
        fig_bar = px.bar(
            comp_melt,
            x='category',
            y='Percentage',
            color='Who',
            barmode='group',
            title='Your Spending vs Benchmark'
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        
        # Comparison table
        comp['Difference'] = comp['You'] - comp['Benchmark']
        st.dataframe(
            comp.style.format({
                'You': '{:.1f}%',
                'Benchmark': '{:.1f}%',
                'Difference': '{:+.1f}%'
            }).map(
                lambda x: 'color: red' if x > 0 else 'color: green',
                subset=['Difference']
            ),
            use_container_width=True
        )
    
    # Tips tab
    with tabs[4]:
        st.markdown("## 💡 Financial Insights")
        
        # Calculate progress to goal
        current_savings = net_savings
        goal = st.session_state.savings_goal
        progress = max(0.0, min(1.0, current_savings / goal))
        
        # Display metrics side by side
        col1, col2, col3 = st.columns([2, 3, 2])
        col1.metric("Months Analyzed", f"{months_count}")
        col2.metric("Saved so far", f"${current_savings:,.2f}", delta=f"${goal-current_savings:,.2f} to go")
        col3.metric("Goal", f"${goal:,.2f}")
        
        # Progress bar
        st.progress(progress)
        
        # Feedback message
        if current_savings < 0:
            st.error("⚠️ You're spending more than you earn. Time to cut back!")
        else:
            achieved_pct = current_savings/goal * 100
            if achieved_pct < 50:
                st.warning(f"You've reached {achieved_pct:.0f}% of your goal—keep going!")
            else:
                st.success(f"Awesome! You've already hit {achieved_pct:.0f}% of your goal!")
        
        st.markdown("---")
        
        # Category-specific tips
        st.subheader("🗂️ Category-Specific Tips")
        
        focus_categories = ['Food', 'Transportation', 'Shopping', 'Entertainment']
        cols = st.columns(2)
        
        for idx, cat in enumerate(focus_categories):
            col = cols[idx % 2]
            
            # Get actual spending amount
            cat_data = category_spending[category_spending.index == cat]
            if not cat_data.empty:
                user_amt = cat_data.iloc[0] / months_count
            else:
                user_amt = 0
            
            bench_pct = benchmark.get(cat, 0)
            target_amt = monthly_income * (bench_pct/100)
            diff = user_amt - target_amt
            
            with col:
                st.write(f"#### 💰 {cat}")
                st.write(f"- **You:** ${user_amt:,.2f}/mo")
                st.write(f"- **Target:** ${target_amt:,.2f}/mo ({bench_pct}% of income)")
                if user_amt > target_amt:
                    st.write(f"  - 🔺 Over by ${diff:,.2f}")
                else:
                    st.write(f"  - ✅ Under by ${-diff:,.2f}")
                
                # Custom advice
                if cat == 'Food':
                    tip = (
                        "Try batch-cooking and cutting takeout days." 
                        if user_amt > target_amt 
                        else "You're on track—keep ordering in moderately!"
                    )
                elif cat == 'Entertainment':
                    tip = (
                        "Look for free local events or streaming bundles."
                        if user_amt > target_amt
                        else "Nice job! Reward yourself within budget."
                    )
                elif cat == 'Shopping':
                    tip = (
                        "Implement a 24-hour rule before impulse buys."
                        if user_amt > target_amt
                        else "Good discipline—keep tracking those wishlists!"
                    )
                else:  # Transportation
                    tip = (
                        "Consider monthly transit passes or carpooling."
                        if user_amt > target_amt
                        else "Great—optimize rides for even more savings!"
                    )
                
                st.info(tip)
        
        # Recent transactions
        st.markdown("## 📝 Recent Transactions")
        st.dataframe(
            df.sort_values('date', ascending=False)
            .head(10)
            [['date', 'description', 'amount', 'category']]
            .style.format({'amount': '${:,.2f}'})
        )

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
if 'upload_status' not in st.session_state:
    st.session_state.upload_status = None

def main():
    st.markdown('<div class="main-header">Personal Finance Insights</div>', unsafe_allow_html=True)
    
    with st.expander("How to use this app", expanded=False):
        st.write("""
        1. Choose your data source (Sample or AWS)
        2. If using AWS:
           - Upload your bank statement CSV
           - Click "Process Data" to upload to S3 and process
           - Wait for processing (up to 30 seconds)
           - Your data will be automatically loaded once processed
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
    
    # Create tabs
    tab1, tab2 = st.tabs(["Data Input", "Analysis"])
    
    with tab1:
        if data_source == "AWS (Upload & Process)":
            st.session_state.data_source = 'aws'
            
            # File uploader
            uploaded_file = st.file_uploader("Upload your bank statement (CSV)", type=["csv"])
            
            if uploaded_file:
                if st.button("Process Data"):
                    st.info("Uploading to AWS...")
                    key = upload_to_s3(uploaded_file, uploaded_file.name)
                    
                    if key:
                        st.session_state.upload_status = uploaded_file.name
                        with st.spinner("Processing your data..."):
                            if wait_for_processing(key):
                                df = get_processed_data(key)
                                if df is not None:
                                    processed_df = process_transactions(df)
                                    if processed_df is not None:
                                        st.session_state.processed_data = processed_df
                                        st.session_state.show_analysis = True
                                        st.success("✅ Data processed successfully!")
                                        st.rerun()
                            else:
                                st.warning("Processing is taking longer than expected. Please try fetching your data in a moment.")
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
            
            if st.button("Generate Sample Data"):
                with st.spinner("Generating sample data..."):
                    df = generate_sample_data()
                    processed_df = process_transactions(df)
                    if processed_df is not None:
                        st.session_state.processed_data = processed_df
                        st.session_state.show_analysis = True
                        st.success("✅ Successfully generated sample data!")
                        st.rerun()
    
    with tab2:
        # Show analysis if data is processed
        if st.session_state.show_analysis and st.session_state.processed_data is not None:
            analyze_data()
        else:
            st.info("Please upload and process your data or generate sample data to see the analysis.")

if __name__ == "__main__":
    main()