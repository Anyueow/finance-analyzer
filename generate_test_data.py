import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_transaction_description(category):
    descriptions = {
        'Housing': [
            'Rent Payment', 'Electric Bill', 'Water Bill', 'Internet Service',
            'Gas Bill', 'Home Insurance', 'Property Tax'
        ],
        'Food': [
            'Walmart Grocery', 'Trader Joes', 'Whole Foods', 'Starbucks',
            'McDonalds', 'Chipotle', 'Local Restaurant', 'Uber Eats'
        ],
        'Transportation': [
            'Shell Gas Station', 'Exxon Gas', 'Uber Ride', 'Lyft Ride',
            'MBTA Monthly Pass', 'Car Insurance', 'Car Maintenance'
        ],
        'Entertainment': [
            'Netflix Subscription', 'Spotify Premium', 'Movie Theater',
            'Concert Tickets', 'Gym Membership', 'Amazon Prime'
        ],
        'Shopping': [
            'Amazon Purchase', 'Target', 'Best Buy', 'Apple Store',
            'Clothing Store', 'Home Depot'
        ],
        'Health & Wellness': [
            'Doctor Visit', 'Dentist', 'Pharmacy', 'Health Insurance',
            'Gym Membership', 'Yoga Class'
        ],
        'Utilities': [
            'Electric Bill', 'Water Bill', 'Gas Bill', 'Internet Service',
            'Phone Bill', 'Cable TV'
        ],
        'Savings & Investments': [
            '401k Contribution', 'Roth IRA', 'Brokerage Transfer',
            'Emergency Fund', 'Savings Account'
        ]
    }
    return random.choice(descriptions.get(category, ['Unknown Transaction']))

def generate_monthly_pattern(month, category):
    # Base amounts for different categories
    base_amounts = {
        'Housing': 2000,
        'Food': 800,
        'Transportation': 400,
        'Entertainment': 300,
        'Shopping': 500,
        'Health & Wellness': 200,
        'Utilities': 300,
        'Savings & Investments': 1000
    }
    
    # Add some monthly variation
    variation = random.uniform(0.8, 1.2)
    # Add some seasonal variation
    seasonal_factor = 1.0
    if month in [11, 12]:  # Holiday season
        seasonal_factor = 1.3 if category in ['Shopping', 'Entertainment'] else 1.0
    elif month in [6, 7, 8]:  # Summer
        seasonal_factor = 1.2 if category in ['Transportation', 'Entertainment'] else 1.0
    
    return base_amounts[category] * variation * seasonal_factor

def generate_test_data(start_date, end_date):
    categories = [
        'Housing', 'Food', 'Transportation', 'Entertainment',
        'Shopping', 'Health & Wellness', 'Utilities', 'Savings & Investments'
    ]
    
    transactions = []
    current_date = start_date
    
    while current_date <= end_date:
        month = current_date.month
        
        # Generate transactions for each category
        for category in categories:
            # Determine number of transactions for this category this month
            num_transactions = random.randint(1, 5)
            
            for _ in range(num_transactions):
                amount = generate_monthly_pattern(month, category)
                # Add some random variation to the amount
                amount *= random.uniform(0.8, 1.2)
                
                # Generate transaction date within the month
                day = random.randint(1, 28)  # Avoid month-end issues
                transaction_date = current_date.replace(day=day)
                
                transactions.append({
                    'date': transaction_date,
                    'description': generate_transaction_description(category),
                    'amount': round(amount, 2),
                    'category': category
                })
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    # Create DataFrame
    df = pd.DataFrame(transactions)
    df = df.sort_values('date')
    
    # Add some random uncategorized transactions
    uncategorized = [
        'ATM Withdrawal', 'Bank Fee', 'Interest Payment',
        'Transfer', 'Payment Received', 'Refund'
    ]
    num_uncategorized = len(df) // 10  # 10% of transactions
    for _ in range(num_uncategorized):
        idx = random.randint(0, len(df) - 1)
        df.at[idx, 'description'] = random.choice(uncategorized)
        df.at[idx, 'category'] = 'Uncategorized'
    
    return df

def main():
    # Generate one year of test data
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 31)
    
    df = generate_test_data(start_date, end_date)
    
    # Save to CSV
    df.to_csv('test_bank_statement.csv', index=False)
    print(f"Generated {len(df)} transactions from {start_date.date()} to {end_date.date()}")
    
    # Print summary
    print("\nMonthly Summary:")
    monthly_summary = df.groupby([df['date'].dt.to_period('M'), 'category'])['amount'].sum().unstack()
    print(monthly_summary)

if __name__ == "__main__":
    main() 