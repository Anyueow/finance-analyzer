import pandas as pd
import logging
from typing import Optional, List, Dict
import io
from pdf2image import convert_from_path
import os
import tempfile
import pytesseract
import camelot
import numpy as np
from PIL import Image

class BankStatementProcessor:
    def __init__(self):
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        
        # Transaction categories
        self.categories = {
            'Food & Dining': ['restaurant', 'food', 'grocery', 'cafe', 'coffee', 'doordash', 'uber eats'],
            'Transportation': ['gas', 'uber', 'lyft', 'transit', 'parking', 'transport'],
            'Shopping': ['amazon', 'target', 'walmart', 'store', 'shop'],
            'Entertainment': ['netflix', 'spotify', 'movie', 'entertainment'],
            'Utilities': ['electric', 'water', 'gas', 'internet', 'phone', 'utility'],
            'Housing': ['rent', 'mortgage', 'home', 'apartment', 'housing'],
            'Healthcare': ['medical', 'doctor', 'pharmacy', 'health'],
            'Income': ['salary', 'deposit', 'payroll', 'direct dep', 'interest']
        }

    def _convert_pdf_to_images(self, pdf_path: str) -> List[Image.Image]:
        """Convert PDF pages to images"""
        self.logger.info("Converting PDF to images...")
        try:
            pages = convert_from_path(pdf_path, 500)  # 500 DPI for good quality
            self.logger.info(f"Converted {len(pages)} pages")
            return pages
        except Exception as e:
            self.logger.error(f"Error converting PDF to images: {e}")
            raise

    def _extract_tables_from_image(self, image: Image.Image) -> List[pd.DataFrame]:
        """Extract tables from image using OCR"""
        self.logger.info("Extracting tables from image using OCR...")
        try:
            # Convert PIL Image to string using pytesseract
            text = pytesseract.image_to_string(image)
            
            # Convert text to DataFrame
            lines = text.split('\n')
            transactions = []
            
            for line in lines:
                if not line.strip():
                    continue
                
                # Split line into columns
                parts = line.split()
                if len(parts) >= 3:  # Assuming at least date, description, amount
                    try:
                        # Try to parse date and amount
                        date = parts[0]
                        amount = parts[-1].replace('$', '').replace(',', '')
                        description = ' '.join(parts[1:-1])
                        
                        transactions.append({
                            'date': date,
                            'description': description,
                            'amount': float(amount)
                        })
                    except (ValueError, IndexError):
                        continue
            
            if transactions:
                return [pd.DataFrame(transactions)]
            return []
            
        except Exception as e:
            self.logger.error(f"Error extracting tables from image: {e}")
            raise

    def _extract_tables_from_pdf(self, pdf_path: str) -> List[pd.DataFrame]:
        """Extract tables from PDF using camelot"""
        self.logger.info("Extracting tables from PDF using camelot...")
        try:
            # Read tables using camelot
            tables = camelot.read_pdf(pdf_path, pages='all', flavor='stream')
            self.logger.info(f"Found {len(tables)} tables")
            
            return [table.df for table in tables if table.df.size > 0]
        except Exception as e:
            self.logger.error(f"Error extracting tables from PDF: {e}")
            return []

    def _categorize_transaction(self, description: str) -> str:
        """Categorize transaction based on description"""
        description = description.lower()
        
        for category, keywords in self.categories.items():
            if any(keyword in description for keyword in keywords):
                return category
        
        return 'Other'

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize the transaction DataFrame"""
        try:
            # Standardize column names
            df.columns = [col.lower().strip() for col in df.columns]
            
            # Ensure required columns exist
            required_cols = {'date', 'description', 'amount'}
            if not required_cols.issubset(df.columns):
                missing = required_cols - set(df.columns)
                raise ValueError(f"Missing required columns: {missing}")
            
            # Convert dates to datetime
            df['date'] = pd.to_datetime(df['date'], format='%m/%d/%Y')
            
            # Clean amounts
            df['amount'] = pd.to_numeric(
                df['amount'].astype(str).str.replace('[$,]', '', regex=True),
                errors='coerce'
            )
            
            # Add categories
            df['category'] = df['description'].apply(self._categorize_transaction)
            
            # Sort by date
            df.sort_values('date', inplace=True)
            
            return df
        except Exception as e:
            self.logger.error(f"Error cleaning DataFrame: {e}")
            raise

    def process_file(self, file) -> Optional[pd.DataFrame]:
        """Process uploaded file (PDF or CSV)"""
        try:
            if file.name.endswith('.pdf'):
                # Save uploaded file to temporary location
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
                    temp_pdf.write(file.getvalue())
                    temp_pdf_path = temp_pdf.name
                
                try:
                    # Try to extract tables directly from PDF first
                    tables = self._extract_tables_from_pdf(temp_pdf_path)
                    
                    if not tables:
                        # If no tables found, try OCR approach
                        pages = self._convert_pdf_to_images(temp_pdf_path)
                        
                        all_transactions = []
                        for i, page in enumerate(pages):
                            self.logger.info(f"Processing page {i+1}/{len(pages)}")
                            
                            # Extract tables from image
                            tables = self._extract_tables_from_image(page)
                            all_transactions.extend(tables)
                    
                    if tables:
                        # Combine all tables
                        df = pd.concat(tables, ignore_index=True)
                        
                        # Clean and standardize data
                        df = self._clean_dataframe(df)
                        
                        self.logger.info(f"Successfully processed {len(df)} transactions")
                        return df
                    else:
                        self.logger.warning("No transactions found in PDF")
                        return None
                
                finally:
                    # Clean up temporary file
                    os.unlink(temp_pdf_path)
            
            elif file.name.endswith('.csv'):
                df = pd.read_csv(file)
                return self._clean_dataframe(df)
            
            else:
                raise ValueError("Unsupported file format. Please upload a PDF or CSV file.")
        
        except Exception as e:
            self.logger.error(f"Error processing file: {e}")
            raise 