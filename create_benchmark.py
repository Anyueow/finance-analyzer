import pandas as pd
import numpy as np

# Define income brackets and their midpoints
income_brackets = {
    'Under_30k': 25000,
    '30k-50k': 40000,
    '50k-75k': 62500,
    '75k-100k': 87500,
    '100k-150k': 125000,
    'Over_150k': 150000
}

# Define spending categories and their typical percentages
data = {
    'Category': [
        'Income', 'Income', 'Income', 'Income',
        'Taxes', 'Taxes', 'Taxes',
        'Housing', 'Housing', 'Housing', 'Housing',
        'Transportation', 'Transportation', 'Transportation', 'Transportation', 'Transportation', 'Transportation',
        'Food', 'Food',
        'Insurance', 'Insurance', 'Insurance', 'Insurance',
        'Health & Wellness', 'Health & Wellness', 'Health & Wellness', 'Health & Wellness',
        'Debt', 'Debt', 'Debt', 'Debt',
        'Savings & Investments', 'Savings & Investments', 'Savings & Investments', 'Savings & Investments',
        'Education', 'Education', 'Education',
        'Entertainment', 'Entertainment', 'Entertainment', 'Entertainment', 'Entertainment', 'Entertainment',
        'Shopping', 'Shopping', 'Shopping', 'Shopping',
        'Miscellaneous', 'Miscellaneous', 'Miscellaneous', 'Miscellaneous', 'Miscellaneous'
    ],
    'Subcategory': [
        'Gross Pay', 'Bonuses/Commissions', 'Interest/Dividends', 'Other Income',
        'Federal Income Tax', 'State Income Tax', 'Social Security and Medicare',
        'Rent', 'Renters Insurance', 'Utilities', 'Internet',
        'Auto Payment', 'Vehicle Insurance', 'Gas/Fuel', 'Maintenance/Repairs', 'Public Transportation/Ride Share', 'Parking/Tolls',
        'Groceries', 'Dining Out/Takeaway',
        'Health Insurance Premiums', 'Dental/Vision Insurance', 'Life Insurance', 'Disability Insurance',
        'Healthcare Out-of-Pocket', 'Prescriptions', 'Gym/Fitness', 'Personal Care',
        'Credit Card Payments', 'Student Loan Payments', 'Personal Loan Payments', 'Other Loan Payments',
        'Emergency Fund Contributions', 'Retirement Contributions', 'Investment Contributions', 'Other Savings Goals',
        'Tuition/Fees', 'Books/Supplies', 'Student Loan Interest Paid',
        'Streaming Services', 'Movies/Concerts/Events', 'Hobbies', 'Bars/Nightlife', 'Vacation/Travel', 'Fitness Classes/Sports Leagues',
        'Apparel & Accessories', 'Electronics & Gadgets', 'Home Goods/Decor', 'Other Shopping',
        'Pet Care', 'Charitable Contributions', 'Gifts', 'Bank Fees', 'Other Expenses'
    ],
    # Define typical spending percentages for each category
    'Under_30k': [
        100, 0, 0.02, 0.8,  # Income
        6, 2, 7.65,  # Taxes
        24, 0.5, 4.8, 1.9,  # Housing
        0, 4, 2.8, 0.4, 2.4, 0.2,  # Transportation
        11.2, 4,  # Food
        3.2, 0.3, 0, 0,  # Insurance
        1.6, 0.6, 0.8, 1.2,  # Health & Wellness
        3.2, 0, 0, 0,  # Debt
        0.2, 0, 0, 0,  # Savings & Investments
        0, 0.4, 0,  # Education
        1, 0.8, 0.6, 1.2, 0, 0.4,  # Entertainment
        1.6, 0.8, 0.4, 0.8,  # Shopping
        0, 0, 0.6, 0.1, 0.6  # Miscellaneous
    ],
    '30k-50k': [
        100, 0.75, 0.075, 1,  # Income
        10, 3, 7.65,  # Taxes
        22.5, 0.4, 3.8, 1.5,  # Housing
        3, 3.8, 2.8, 0.8, 1.3, 0.3,  # Transportation
        9.5, 5,  # Food
        3.8, 0.4, 0.1, 0.1,  # Insurance
        2, 0.6, 1, 1.3,  # Health & Wellness
        3, 3.8, 0.5, 0.1,  # Debt
        0.8, 1.3, 0, 0.3,  # Savings & Investments
        0, 0.4, 0.4,  # Education
        0.8, 1, 0.8, 1.3, 2, 0.5,  # Entertainment
        1.8, 1, 0.5, 1,  # Shopping
        0.3, 0.1, 0.6, 0.1, 0.9  # Miscellaneous
    ],
    '50k-75k': [
        100, 1.6, 0.13, 1,  # Income
        12.8, 4, 7.65,  # Taxes
        19.2, 0.3, 2.9, 1.2,  # Housing
        4, 2.9, 2.2, 0.8, 0.6, 0.2,  # Transportation
        8, 5.6,  # Food
        3.5, 0.4, 0.2, 0.1,  # Insurance
        1.9, 0.6, 1, 1.1,  # Health & Wellness
        2.9, 4, 0.6, 0.2,  # Debt
        1.3, 3.2, 0.5, 0.5,  # Savings & Investments
        0.5, 0.3, 0.8,  # Education
        0.6, 1, 0.8, 1.1, 3.2, 0.5,  # Entertainment
        1.9, 1, 0.5, 1,  # Shopping
        0.5, 0.2, 0.6, 0.1, 0.9  # Miscellaneous
    ],
    '75k-100k': [
        100, 2.8, 0.23, 0.9,  # Income
        17.1, 4.6, 7.65,  # Taxes
        17.1, 0.3, 2.4, 1,  # Housing
        4.6, 2.3, 1.9, 0.8, 0.3, 0.2,  # Transportation
        7.4, 5.7,  # Food
        3.2, 0.4, 0.2, 0.2,  # Insurance
        1.8, 0.5, 0.9, 1.1,  # Health & Wellness
        2.5, 4, 0.7, 0.2,  # Debt
        1.4, 4.6, 0.9, 0.9,  # Savings & Investments
        0.9, 0.3, 1.1,  # Education
        0.5, 1, 0.8, 1, 4.6, 0.5,  # Entertainment
        2.1, 1, 0.5, 0.9,  # Shopping
        0.6, 0.3, 0.5, 0.1, 0.9  # Miscellaneous
    ],
    '100k-150k': [
        100, 4.8, 0.4, 0.8,  # Income
        20, 5.6, 7.65,  # Taxes
        14.4, 0.2, 1.9, 0.8,  # Housing
        4.4, 1.8, 1.5, 0.8, 0.2, 0.2,  # Transportation
        6.4, 5.6,  # Food
        2.7, 0.4, 0.3, 0.2,  # Insurance
        1.6, 0.4, 0.8, 1,  # Health & Wellness
        2.2, 3.6, 0.6, 0.2,  # Debt
        1.4, 5.6, 1.6, 1.2,  # Savings & Investments
        1.2, 0.2, 1.2,  # Education
        0.4, 1, 0.7, 0.9, 5.6, 0.4,  # Entertainment
        2, 1, 0.4, 0.8,  # Shopping
        0.6, 0.5, 0.5, 0.1, 0.9  # Miscellaneous
    ],
    'Over_150k': [
        100, 9, 1, 0.75,  # Income
        25, 7.5, 7.65,  # Taxes
        12, 0.2, 1.4, 0.5,  # Housing
        3.5, 1.2, 1.1, 0.8, 0.1, 0.2,  # Transportation
        5, 6,  # Food
        2, 0.3, 0.4, 0.3,  # Insurance
        1.3, 0.3, 0.6, 0.9,  # Health & Wellness
        1.8, 2.8, 0.5, 0.2,  # Debt
        1.3, 6, 4, 2,  # Savings & Investments
        1.5, 0.2, 1,  # Education
        0.3, 0.9, 0.6, 0.7, 7.5, 0.3,  # Entertainment
        1.8, 0.9, 0.4, 0.8,  # Shopping
        0.5, 0.8, 0.5, 0.1, 0.9  # Miscellaneous
    ]
}

# Create DataFrame
df = pd.DataFrame(data)

# Save to CSV
df.to_csv('benchmark.csv', index=False)
print("Benchmark data has been created successfully!") 