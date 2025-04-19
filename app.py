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

# Initialize session state
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'show_analysis' not in st.session_state:
    st.session_state.show_analysis = False
if 'monthly_income' not in st.session_state:
    st.session_state.monthly_income = 5000.0
if 'savings_goal' not in st.session_state:
    st.session_state.savings_goal = 10000.0

# Database schema constants (for future implementation)
SCHEMA = {
    'transaction_date': 'DATE',
    'amount': 'DECIMAL(16,2)',
    'category': 'VARCHAR(100)'
}

CATEGORIES = {
    'Housing': ['rent', 'mortgage', 'property tax', 'home insurance', 'maintenance', 'repairs'],
    'Transportation': ['gas', 'fuel', 'car payment', 'car insurance', 'parking', 'public transit', 'uber', 'lyft'],
    'Food': ['groceries', 'restaurant', 'takeout', 'delivery', 'coffee'],
    'Utilities': ['electricity', 'water', 'gas', 'internet', 'phone', 'cable'],
    'Healthcare': ['medical', 'dental', 'vision', 'prescription', 'insurance'],
    'Entertainment': ['movies', 'music', 'streaming', 'hobbies', 'sports'],
    'Shopping': ['clothing', 'electronics', 'home goods', 'amazon', 'target', 'walmart'],
    'Personal': ['haircut', 'gym', 'beauty', 'spa'],
    'Education': ['tuition', 'books', 'courses', 'supplies'],
    'Savings': ['investment', '401k', 'ira', 'savings deposit'],
    'Income': ['salary', 'bonus', 'interest', 'dividend', 'refund'],
    'Other': []
}

# Set page configuration
st.set_page_config(
    page_title="Personal Finance Insights 💰",
    layout="wide",
    initial_sidebar_state="expanded"
)



def categorize_transaction(description: str) -> str:
    """Categorize transaction based on description"""
    description = description.lower()
    
    for category, keywords in CATEGORIES.items():
        if any(keyword in description for keyword in keywords):
            return category
    
    return 'Other'

def process_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """Process transactions dataframe to match database schema"""
    try:
        # Standardize column names
        df.columns = [col.strip() for col in df.columns]
        
        # Map common column names
        column_mapping = {
            'date': 'transaction_date',
            'description': 'description',
            'amount': 'amount',
            'category': 'category'
        }
        df = df.rename(columns=column_mapping)
        
        # Ensure required columns exist
        required_cols = {'transaction_date', 'description', 'amount'}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            st.error(f"Missing columns: {missing_cols}")
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Convert dates to datetime
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        
        # Add category if not present
        if 'category' not in df.columns:
            df['category'] = df['description'].apply(categorize_transaction)
        
        # Add month for analysis
        df['month'] = df['transaction_date'].dt.to_period('M')
        
        # Sort by date
        df = df.sort_values('transaction_date')
        
        return df
    
    except Exception as e:
        st.error(f"Error processing transactions: {str(e)}")
        return None

def analyze_data():
    """Analyze the processed data and show results"""
    if st.session_state.processed_data is not None:
        df = st.session_state.processed_data
        
        # Calculate basic metrics
        expenses_df = df[df['amount'] < 0].copy()
        expenses_df['amount'] = expenses_df['amount'].abs()
        
        # Use monthly income from input instead of transactions
        monthly_income = st.session_state.monthly_income
        total_income = monthly_income * df['month'].nunique()  # Calculate total income for the period
        
        total_exp = expenses_df['amount'].sum()
        months_count = df['month'].nunique()
        avg_monthly = total_exp / months_count if months_count > 0 else total_exp
        
        # Monthly trends
        monthly_exp = expenses_df.groupby('month')['amount'].sum().reset_index()
        monthly_exp['month'] = monthly_exp['month'].dt.strftime('%b %Y')
        
        # Category analysis
        by_cat = expenses_df.groupby('category')['amount'].sum().reset_index()
        by_cat['percentage'] = by_cat['amount'] / total_exp * 100
        by_cat['monthly_avg'] = by_cat['amount'] / months_count
        
        # Show results in tabs
        tabs = st.tabs([
            "Overview 📋",
            "Trend 📈",
            "Categories 🗂️",
            "Benchmark ⚖️",
            "Tips 💡"
        ])
        
        # Overview tab
        with tabs[0]:
            st.subheader("💼 Financial Overview")
            
            # Key metrics
            c1, c2, c3, c4 = st.columns(4)
            c1.metric(
                "Total Income",
                f"${total_income:,.2f}",
                help="Total income for the period"
            )
            c2.metric(
                "Total Spending",
                f"${total_exp:,.2f}",
                help="Total expenses for the period"
            )
            c3.metric(
                "Net Savings",
                f"${(total_income - total_exp):,.2f}",
                f"{((total_income - total_exp) / total_income * 100):.1f}%",
                help="Total savings and savings rate"
            )
            c4.metric(
                "Months Analyzed",
                f"{months_count}",
                help="Number of months in the data"
            )
            
            # Monthly averages
            st.subheader("Monthly Averages")
            c1, c2, c3 = st.columns(3)
            c1.metric("Avg Income", f"${total_income/months_count:,.2f}/mo")
            c2.metric("Avg Spending", f"${avg_monthly:,.2f}/mo")
            c3.metric("Avg Savings", f"${(total_income - total_exp)/months_count:,.2f}/mo")
        
        # Trend tab
        with tabs[1]:
            st.subheader("📈 Spending Trends")
            
            # Monthly trend
            fig_line = px.line(
                monthly_exp,
                x="month",
                y="amount",
                markers=True,
                labels={"amount": "Spending ($)", "month": "Month"},
                title="Monthly Spending Trend"
            )
            st.plotly_chart(fig_line, use_container_width=True)
            
            # Category trends
            st.subheader("Category Trends")
            monthly_cat = expenses_df.groupby(['month', 'category'])['amount'].sum().reset_index()
            monthly_cat['month'] = monthly_cat['month'].dt.strftime('%b %Y')
            
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
            st.subheader("🗂️ Spending Categories")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Pie chart
                fig_pie = px.pie(
                    by_cat,
                    values="amount",
                    names="category",
                    title="Spending Distribution",
                    hole=0.4
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Category details
                st.subheader("Category Details")
                cat_details = pd.DataFrame({
                    'Total': by_cat['amount'],
                    'Monthly Avg': by_cat['monthly_avg'],
                    '% of Spending': by_cat['percentage']
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
            st.subheader("⚖️ Benchmark Comparison")
            
            # Get appropriate benchmark
            if monthly_income < 50000:
                benchmark = BENCHMARKS['low_income']
            elif monthly_income < 100000:
                benchmark = BENCHMARKS['medium_income']
            else:
                benchmark = BENCHMARKS['high_income']
            
            # Prepare comparison data
            user_pct = by_cat.reset_index()[["category", "percentage"]].rename(columns={"percentage": "You"})
            bench_pct = pd.DataFrame(benchmark.items(), columns=["category", "Benchmark"])
            
            comp = pd.merge(user_pct, bench_pct, on="category", how="left")
            comp_melt = comp.melt(
                id_vars="category",
                value_vars=["You", "Benchmark"],
                var_name="Who",
                value_name="Percentage"
            )
            
            # Bar chart
            fig_bar = px.bar(
                comp_melt,
                x="category",
                y="Percentage",
                color="Who",
                barmode="group",
                title="Your Spending vs Benchmark"
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
            # Comparison table
            comp["Difference"] = comp["You"] - comp["Benchmark"]
            st.dataframe(
                comp.style.format({
                    "You": "{:.1f}%",
                    "Benchmark": "{:.1f}%",
                    "Difference": "{:+.1f}%"
                }).map(
                    lambda x: 'color: red' if x > 0 else 'color: green',
                    subset=["Difference"]
                ),
                use_container_width=True
            )
        
       # Tips tab
        with tabs[4]:
            st.header("💡 Savings Tips")

            # ─── Progress to goal ──────────────────────────────────────────────────────
            current_savings = (monthly_income/12 * months_count) - total_exp
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

            # ─── Category‑Specific Tips ─────────────────────────────────────────────────
            st.subheader("🗂️ Category‑Specific Tips")

            # Pick your benchmark based on income bracket
            if monthly_income < 50000:
                benchmark = BENCHMARKS['low_income']
            elif monthly_income < 100000:
                benchmark = BENCHMARKS['medium_income']
            else:
                benchmark = BENCHMARKS['high_income']

            focus_categories = ['Food', 'Transportation', 'Shopping', 'Entertainment']
            cols = st.columns(2)

            for idx, cat in enumerate(focus_categories):
                col = cols[idx % 2]
                
                # Get actual spending amount from by_cat DataFrame
                cat_data = by_cat[by_cat['category'] == cat]
                if not cat_data.empty:
                    user_amt = cat_data['monthly_avg'].iloc[0]
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
                            "Try batch‑cooking and cutting takeout days." 
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
                            "Implement a 24‑hour rule before impulse buys."
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

# Generate sample data
def generate_sample_data():
    # Generate dates for last 6 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Categories and their typical amounts and frequencies
    categories = {
        'Housing': {
            'amount_range': (1500, 2000),
            'frequency': 1,  # Monthly
            'descriptions': ['Rent Payment', 'Mortgage Payment', 'Property Tax', 'Home Insurance']
        },
        'Food': {
            'amount_range': (50, 200),
            'frequency': 15,  # Multiple times per month
            'descriptions': ['Grocery Store', 'Restaurant', 'Coffee Shop', 'Food Delivery']
        },
        'Transportation': {
            'amount_range': (30, 100),
            'frequency': 10,
            'descriptions': ['Gas Station', 'Public Transit', 'Ride Share', 'Car Insurance']
        },
        'Entertainment': {
            'amount_range': (20, 150),
            'frequency': 8,
            'descriptions': ['Movie Theater', 'Streaming Service', 'Concert', 'Sports Event']
        },
        'Shopping': {
            'amount_range': (50, 300),
            'frequency': 6,
            'descriptions': ['Clothing Store', 'Electronics', 'Home Goods', 'Online Shopping']
        },
        'Utilities': {
            'amount_range': (100, 300),
            'frequency': 1,
            'descriptions': ['Electric Bill', 'Water Bill', 'Internet Service', 'Phone Bill']
        },
        'Healthcare': {
            'amount_range': (50, 500),
            'frequency': 2,
            'descriptions': ['Doctor Visit', 'Pharmacy', 'Dental Care', 'Health Insurance']
        },
        'Income': {
            'amount_range': (4000, 6000),
            'frequency': 1,
            'descriptions': ['Salary Deposit', 'Freelance Payment', 'Investment Income']
        },
        'Other': {
            'amount_range': (20, 200),
            'frequency': 4,
            'descriptions': ['ATM Withdrawal', 'Bank Fee', 'Charity Donation', 'Gift']
        }
    }
    
    # Generate transactions
    data = []
    for date in dates:
        for category, details in categories.items():
            # Check if we should generate a transaction for this category on this date
            if np.random.random() < (details['frequency'] / 30):  # Convert monthly frequency to daily probability
                # Generate amount
                min_amt, max_amt = details['amount_range']
                amount = round(np.random.uniform(min_amt, max_amt), 2)
                
                # Make expenses negative
                if category != 'Income':
                    amount = -amount
                
                # Select random description
                description = np.random.choice(details['descriptions'])
                
                data.append({
                    'date': date,
                    'description': description,
                    'amount': amount,
                    'category': category
                })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Sort by date
    df = df.sort_values('date')
    
    # Add some random variation to make it more realistic
    df['amount'] = df['amount'] * np.random.normal(1, 0.1, len(df))
    df['amount'] = df['amount'].round(2)
    
    return df

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

def main():
    st.markdown('<div class="main-header">Personal Finance Insights</div>', unsafe_allow_html=True)
    
    with st.expander("How to use this app", expanded=False):
        st.write("""
        1. Enter your monthly income after taxes
        2. Set your savings goal
        3. Click "Generate Sample Data" to see insights
        4. Review your spending analysis and personalized insights
        
        This demo uses realistic sample data to showcase the app's features.
        """)
    
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
