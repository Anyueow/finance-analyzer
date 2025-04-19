# Personal Finance Insights

A Streamlit application that analyzes your bank statements and provides insights into your spending patterns compared to benchmark data.

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Start the Streamlit app:
```bash
streamlit run app.py
```

2. Upload your bank statement CSV file with the following columns:
   - date
   - description
   - amount
   - category (optional)

3. Select your income bracket to compare your spending patterns with benchmark data.

## Features

- Transaction categorization using AI
- Monthly spending trends visualization
- Category-wise spending analysis
- Benchmark comparison with similar income groups
- Personalized savings recommendations
