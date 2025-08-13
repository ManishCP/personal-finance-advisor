import pdfplumber
import re
from datetime import datetime
from typing import List, Dict, Optional
from .base_agent import BaseAgent
from utils.merchant_database import MerchantDatabase

class DocumentProcessorAgent(BaseAgent):
    """
    Agent 1: Pure deterministic document processing
    NO LLM CALLS - extracts and parses transaction data
    """

    def __init__(self):
        super().__init__("Document Processor", uses_llm=False)
        self.merchant_db = MerchantDatabase()
        print(f"🏗️ {self.name} initialized - 0 LLM calls")

    def process(self, pdf_path: str) -> Dict:
        """Main entry point: PDF → Structured transaction data"""
        print(f"\n📄 {self.name} processing: {pdf_path}")
        
        try:
            # Step 1: Extract raw text
            raw_text = self._extract_text_from_pdf(pdf_path)
            
            if not raw_text.strip():
                return {'success': False, 'error': 'No text in PDF', 'transactions': []}
            
            print(f"   ✅ Extracted {len(raw_text)} characters")
            
            # Step 2: Find transaction lines
            transaction_lines = self._find_transaction_lines(raw_text)
            
            if not transaction_lines:
                return {
                    'success': True, 
                    'transactions': [],
                    'raw_text': raw_text,
                    'message': 'No transaction lines found - might need different parsing approach'
                }
            
            # NEW Step 3: Parse transaction lines into structured data
            parsed_transactions = self._parse_transaction_lines(transaction_lines)
            
            categorized_transactions = self._apply_basic_categorization(parsed_transactions)

            return {
                'success': True,
                'transactions': categorized_transactions,  # Changed from parsed_transactions
                'total_transactions': len(categorized_transactions),
                'raw_transaction_lines': transaction_lines,
                'parsing_stats': {
                    'lines_found': len(transaction_lines),
                    'successfully_parsed': len(parsed_transactions),
                    'parse_success_rate': len(parsed_transactions) / len(transaction_lines) if transaction_lines else 0,
                    'categorized_deterministically': len([t for t in categorized_transactions if t['category'] != 'uncategorized']),
                    'needs_llm': len([t for t in categorized_transactions if t['category'] == 'uncategorized'])
                }
            }

            
        except Exception as e:
            return {'success': False, 'error': str(e), 'transactions': []}
        
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Enhanced PDF extraction - handles both text and tables
        """
        full_text = ""
        
        with pdfplumber.open(pdf_path) as pdf:
            print(f"   📖 PDF has {len(pdf.pages)} pages")
            
            for page_num, page in enumerate(pdf.pages, 1):
                print(f"   📄 Processing page {page_num}...")
                
                # Method 1: Try table extraction first (for structured data)
                tables = page.extract_tables()
                if tables:
                    print(f"   📊 Found {len(tables)} tables on page {page_num}")
                    
                    for table_num, table in enumerate(tables, 1):
                        full_text += f"\n--- PAGE {page_num} TABLE {table_num} ---\n"
                        
                        for row_num, row in enumerate(table):
                            if row and any(cell for cell in row if cell and str(cell).strip()):
                                # Join non-empty cells with tabs
                                row_text = '\t'.join(str(cell).strip() if cell else '' for cell in row)
                                full_text += f"ROW_{row_num}: {row_text}\n"
                        
                        full_text += f"--- END TABLE {table_num} ---\n"
                
                # Method 2: Regular text extraction as backup
                page_text = page.extract_text()
                if page_text:
                    full_text += f"\n--- PAGE {page_num} TEXT ---\n"
                    full_text += page_text
                    full_text += f"\n--- END PAGE {page_num} TEXT ---\n"
                
                # Method 3: Character-level extraction for stubborn PDFs
                if not tables and not page_text:
                    print(f"   ⚠️  Trying character-level extraction...")
                    chars = page.chars
                    if chars:
                        full_text += f"\n--- PAGE {page_num} CHARS ---\n"
                        for char in chars[:100]:  # First 100 characters for debugging
                            full_text += char.get('text', '')
                        full_text += f"\n--- END CHARS ---\n"
            
            return full_text
    
    def _find_transaction_lines(self, text: str) -> List[str]:
        """
        Find Lines that actually contain transactions
        """
        lines = text.split('\n')
        potential_transactions = []

        print(f"   🔍 Scanning {len(lines)} lines for transactions...")

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Skip obvious non-transaction lines
            if self._is_header_or_footer(line):
                continue

            # Check if this looks like a transaction
            if self._looks_like_transaction(line):
                potential_transactions.append(line)
                print(f"   ✅ Line {line_num}: {line[:50]}...")

        print(f"   📊 Found {len(potential_transactions)} potential transaction lines")
        return potential_transactions
    
    def _is_header_or_footer(self, line: str) -> bool:
        """Skip lines that are obviously NOT transactions"""
        line_lower = line.lower()
        
        # Skip header/footer patterns
        skip_patterns = [
            r'^(account|statement|balance|date|description|amount)',
            r'^(page \d+|statement period|issue date)',
            r'^(previous balance|ending balance|current balance)',
            r'^(note:|total|summary)',
            r'^(paid in|paid out|detail|payment type)',
            r'^\s*$',  # Empty lines
            r'^-+$',   # Separator lines like "----------"
            r'^=+$'    # Separator lines like "=========="
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, line_lower):
                return True
        
        return False
    
    def _looks_like_transaction(self, line: str) -> bool:
        """
        Check if line has the pattern of a real transaction
        Must have: date + description + amount
        """
        # Must have a date pattern
        has_date = bool(re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{4}', line))
        
        # Must have an amount pattern  
        has_amount = bool(re.search(r'\$?[\d,]+\.?\d*', line))
        
        # Must have some description text (not just numbers/symbols)
        has_description = bool(re.search(r'[A-Za-z]{3,}', line))
        
        return has_date and has_amount and has_description
    
    def _parse_transaction_lines(self, transaction_lines: List[str]) -> List[Dict]:
        """
        Parse each transaction line into structured data
        """
        print(f"   🔧 Parsing {len(transaction_lines)} transaction lines...")
        
        parsed_transactions = []
        failed_parses = 0
        
        for line_num, line in enumerate(transaction_lines, 1):
            try:
                parsed = self._parse_single_transaction(line)
                if parsed:
                    parsed['transaction_id'] = f"txn_{len(parsed_transactions) + 1}"
                    parsed_transactions.append(parsed)
                    if line_num <= 3:  # Show first 3 for debugging
                        print(f"   ✅ Parsed line {line_num}: {parsed['description'][:30]}... = ${parsed['amount']}")
                else:
                    failed_parses += 1
                    if failed_parses <= 2:  # Show first 2 failures
                        print(f"   ❌ Failed to parse: {line[:50]}...")
                        
            except Exception as e:
                failed_parses += 1
                if failed_parses <= 2:
                    print(f"   ❌ Parse error: {line[:30]}... → {e}")

        success_rate = len(parsed_transactions) / len(transaction_lines) if transaction_lines else 0
        print(f"   📊 Parsing success: {len(parsed_transactions)}/{len(transaction_lines)} ({success_rate:.1%})")

        return parsed_transactions

    def _parse_single_transaction(self, line: str) -> Optional[Dict]:
        """
        Parse one transaction line using multiple regex patterns
        Returns None if no pattern matches
        """
        
        # Define regex patterns for different bank formats
        patterns = [
            # Pattern 1: Chase format "02/01/2024 DUNKIN DONUTS 8901 -$4.50 $1,851.92"
            {
                'regex': r'(\d{1,2}/\d{1,2}/\d{4})\s+([^-+$\d]+?)\s+([-+]?\$?[\d,]+\.?\d*)\s+\$?([\d,]+\.?\d*)',
                'groups': {'date': 1, 'description': 2, 'amount': 3, 'balance': 4},
                'name': 'Chase Format'
            },
            
            # Pattern 2: Wells Fargo format "03-01-2024 BURGER KING #4521 $8.99 $2,136.68"
            {
                'regex': r'(\d{1,2}-\d{1,2}-\d{4})\s+([^$\d]+?)\s+\$?([\d,]+\.?\d*)\s+\$?([\d,]+\.?\d*)',
                'groups': {'date': 1, 'description': 2, 'amount': 3, 'balance': 4},
                'name': 'Wells Fargo Format'
            },
            
            # Pattern 3: Generic format "01/02/2024 STARBUCKS STORE 1234 -$5.67 $2,494.33"
            {
                'regex': r'(\d{1,2}/\d{1,2}/\d{4})\s+([A-Za-z][^-+$\d]*?)\s+([-+]?\$?[\d,]+\.?\d*)\s+\$?([\d,]+\.?\d*)',
                'groups': {'date': 1, 'description': 2, 'amount': 3, 'balance': 4},
                'name': 'Generic Format'
            }
        ]
        
        # Try each pattern
        for pattern in patterns:
            match = re.search(pattern['regex'], line)
            if match:
                try:
                    return self._extract_transaction_data(match, pattern, line)
                except Exception as e:
                    continue  # Try next pattern
        
        return None  # No pattern matched

    def _extract_transaction_data(self, match, pattern: Dict, original_line: str) -> Dict:
        """Extract structured data from successful regex match"""
        
        groups = match.groups()
        group_map = pattern['groups']
        
        # Extract date
        date_str = groups[group_map['date'] - 1]
        parsed_date = self._parse_date(date_str)
        
        # Extract description (clean it up)
        description = groups[group_map['description'] - 1].strip()
        description = re.sub(r'\s+', ' ', description)  # Remove extra spaces
        description = re.sub(r'[#*]\w*', '', description)  # Remove reference codes
        description = description.strip()
        
        # Extract amount
        amount_str = groups[group_map['amount'] - 1]
        amount = self._parse_amount(amount_str)
        is_debit = self._is_debit_transaction(amount_str, original_line)
        
        # Extract balance (if available)
        balance = 0.0
        if 'balance' in group_map and len(groups) >= group_map['balance']:
            balance_str = groups[group_map['balance'] - 1]
            balance = self._parse_amount(balance_str)
        
        return {
            'date': parsed_date.strftime('%Y-%m-%d'),
            'description': description,
            'amount': abs(amount),  # Always positive, use is_debit flag
            'is_debit': is_debit,
            'balance': balance,
            'category': 'uncategorized',  # Will be set later
            'confidence': 0.0,
            'source': 'deterministic',
            'original_line': original_line,
            'pattern_used': pattern['name']
        }

    # Helper methods for parsing components
    def _parse_date(self, date_str: str) -> datetime:
        """Handle different date formats"""
        from datetime import datetime
        
        date_formats = [
            '%m/%d/%Y',     # 02/01/2024
            '%m-%d-%Y',     # 03-01-2024  
            '%Y-%m-%d',     # 2024-02-01
            '%d-%b-%Y',     # 01-FEB-2024
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        
        # Fallback to current date if parsing fails
        print(f"   ⚠️  Couldn't parse date: {date_str}")
        return datetime.now()

    def _parse_amount(self, amount_str: str) -> float:
        """Clean and parse amount string"""
        # Remove $ signs and commas
        clean_amount = re.sub(r'[$,]', '', amount_str)
        
        try:
            return float(clean_amount)
        except:
            print(f"   ⚠️  Couldn't parse amount: {amount_str}")
            return 0.0

    def _is_debit_transaction(self, amount_str: str, line: str) -> bool:
        """Determine if transaction is debit (money going out)"""
        
        # Check for explicit negative signs
        if amount_str.startswith('-') or amount_str.startswith('+'):
            return amount_str.startswith('-')
        
        # Check for debit indicators in the line
        debit_keywords = ['withdrawal', 'purchase', 'payment', 'fee', 'charge']
        line_lower = line.lower()
        
        for keyword in debit_keywords:
            if keyword in line_lower:
                return True
        
        # Check for credit indicators
        credit_keywords = ['deposit', 'interest', 'refund', 'credit', 'salary']
        for keyword in credit_keywords:
            if keyword in line_lower:
                return False
        
        # Default to debit for most transactions
        return True
    
    def _apply_basic_categorization(self, transactions: List[Dict]) -> List[Dict]:
        """
        Step 4: Apply deterministic categorization using merchant database
        NO LLM CALLS - pure keyword matching
        """
        print(f"   🏷️ Applying basic categorization to {len(transactions)} transactions...")
        
        categorized_count = 0
        
        for txn in transactions:
            category, confidence = self.merchant_db.categorize_transaction(txn['description'])
            
            if category != 'uncategorized':
                txn['category'] = category
                txn['confidence'] = confidence
                txn['source'] = 'deterministic'
                categorized_count += 1
            # else: remains 'uncategorized' for Agent 2
        
        categorization_rate = categorized_count / len(transactions) if transactions else 0
        print(f"   📊 Deterministic categorization: {categorized_count}/{len(transactions)} ({categorization_rate:.1%})")
        print(f"   🤖 Will need LLM for: {len(transactions) - categorized_count} transactions")
        
        return transactions