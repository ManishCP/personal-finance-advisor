import re

"""
Merchant Database for Deterministic Categorization
This handles OBVIOUS transactions that don't need LLM analysis.
"""

class MerchantDatabase:
    """
    Keyword-based categorization for obvious merchants
    NO LLM CALLS - pure pattern matching
    """
    
    def __init__(self):
        print("🏪 Initializing Merchant Database...")
        
        # Extensive keyword database (professor emphasized this)
        self.merchant_keywords = {
            'food_dining': [
                # Coffee & Fast Food
                'starbucks', 'dunkin', 'dunkin donuts', 'coffee', 'cafe',
                'mcdonalds', 'burger king', 'subway', 'kfc', 'taco bell',
                'chipotle', 'panera', 'panda express', 'pizza hut', 'dominos',
                
                # Restaurants
                'restaurant', 'bistro', 'grill', 'kitchen', 'diner', 'eatery',
                'food truck', 'catering', 'bakery',
                
                # Food Delivery
                'uber eats', 'doordash', 'grubhub', 'postmates', 'food delivery'
            ],
            
            'groceries': [
                'walmart', 'target', 'costco', 'sams club', 'sam\'s club',
                'kroger', 'safeway', 'publix', 'wegmans', 'giant', 'stop shop',
                'whole foods', 'trader joe', 'aldi', 'food lion', 'harris teeter',
                'market', 'grocery', 'supermarket', 'supercenter', 'food store'
            ],
            
            'transportation': [
                # Gas Stations
                'shell', 'exxon', 'chevron', 'bp', 'mobil', 'citgo', 'arco',
                'gas station', 'fuel', 'gasoline', 'petrol',
                
                # Rideshare & Transit
                'uber', 'lyft', 'taxi', 'cab', 'rideshare',
                'metro', 'mta', 'transit', 'bus', 'train', 'subway',
                'parking', 'garage', 'meter',
                
                # Travel
                'airline', 'airport', 'flight', 'car rental', 'hertz', 'enterprise'
            ],
            
            'shopping': [
                'amazon', 'ebay', 'etsy', 'best buy', 'apple store', 'microsoft',
                'home depot', 'lowes', 'macys', 'kohls', 'tj maxx', 'marshalls',
                'ross', 'old navy', 'gap', 'nike', 'adidas', 'mall', 'outlet'
            ],
            
            'bills_utilities': [
                'electric', 'power', 'energy', 'utility', 'water', 'sewer',
                'gas bill', 'internet', 'cable', 'phone', 'wireless',
                'verizon', 'att', 'at&t', 'comcast', 'spectrum', 'xfinity',
                'municipal', 'city of', 'county of'
            ],
            
            'entertainment': [
                'netflix', 'spotify', 'hulu', 'disney', 'amazon prime',
                'apple music', 'youtube', 'gaming', 'steam', 'playstation',
                'xbox', 'nintendo', 'movie', 'theater', 'cinema', 'concert'
            ],
            
            'healthcare': [
                'cvs', 'walgreens', 'rite aid', 'pharmacy', 'medical',
                'doctor', 'dentist', 'hospital', 'clinic', 'health'
            ],
            
            'atm_cash': [
                'atm', 'withdrawal', 'cash advance', 'cash back', 'cashout'
            ],
            
            'income': [
                'direct deposit', 'salary', 'payroll', 'interest', 'dividend',
                'refund', 'tax refund', 'deposit', 'credit'
            ],
            
            'fees': [
                'fee', 'charge', 'penalty', 'overdraft', 'maintenance',
                'service charge', 'foreign', 'atm fee'
            ]
        }
        
        categories_count = sum(len(keywords) for keywords in self.merchant_keywords.values())
        print(f"   📚 Loaded {len(self.merchant_keywords)} categories")
        print(f"   🔑 Total keywords: {categories_count}")
    
    def categorize_transaction(self, description: str) -> tuple:
        """
        Categorize transaction based on merchant description
        Returns: (category, confidence) or ('uncategorized', 0.0)
        """
        desc_lower = description.lower().strip()
        
        # Remove common prefixes/suffixes that don't help categorization
        desc_clean = self._clean_description_for_matching(desc_lower)
        
        # Check each category's keywords
        for category, keywords in self.merchant_keywords.items():
            for keyword in keywords:
                if keyword in desc_clean:
                    confidence = self._calculate_confidence(keyword, desc_clean)
                    return category, confidence
        
        # No match found - will need LLM
        return 'uncategorized', 0.0
    
    def _clean_description_for_matching(self, description: str) -> str:
        """Clean description to improve keyword matching"""
        # Remove common noise
        desc = re.sub(r'[#*]\w*', '', description)  # Remove reference codes
        desc = re.sub(r'\d{4,}', '', desc)  # Remove long numbers
        desc = re.sub(r'\s+', ' ', desc)    # Normalize spaces
        return desc.strip()
    
    def _calculate_confidence(self, matched_keyword: str, description: str) -> float:
        """Calculate confidence based on keyword match quality"""
        
        # Exact brand matches get high confidence
        if matched_keyword in ['starbucks', 'walmart', 'amazon', 'netflix']:
            return 0.95
        
        # Specific store types get high confidence  
        if matched_keyword in ['gas station', 'grocery', 'pharmacy']:
            return 0.90
        
        # Generic keywords get medium confidence
        if matched_keyword in ['restaurant', 'cafe', 'market']:
            return 0.75
        
        # Default confidence for keyword matches
        return 0.80
    
    def get_statistics(self) -> dict:
        """Return database statistics"""
        return {
            'total_categories': len(self.merchant_keywords),
            'total_keywords': sum(len(keywords) for keywords in self.merchant_keywords.values()),
            'categories': list(self.merchant_keywords.keys())
        }