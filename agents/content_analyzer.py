"""
Agent 2: Content Analyzer - Smart categorization for ambiguous transactions
============================================================================

This agent uses LLM (Claude) to categorize transactions that the 
deterministic approach couldn't handle.

EXACTLY 1 LLM call per batch of uncategorized transactions.
"""

import json
import re
from typing import List, Dict
from pydantic import BaseModel, Field
from .base_agent import BaseAgent

# Pydantic models for LLM response validation
class TransactionCategory(BaseModel):
    """Single transaction categorization result"""
    transaction_id: str
    category: str
    confidence: float = Field(ge=0, le=1)  # Must be between 0 and 1
    reasoning: str

class BatchCategorizationResponse(BaseModel):
    """Validate batch LLM response structure"""
    categorizations: List[TransactionCategory]

class ContentAnalyzerAgent(BaseAgent):
    """
    Agent 2: Smart categorization for ambiguous transactions
    Uses EXACTLY 1 LLM call per batch of uncategorized transactions
    """
    
    def __init__(self, llm_interface):
        super().__init__("Content Analyzer", uses_llm=True)
        self.llm = llm_interface
        
        # Define categories that LLM can choose from
        self.valid_categories = {
            'food_dining': 'Restaurants, coffee shops, food delivery, dining out',
            'groceries': 'Grocery stores, supermarkets, food shopping',
            'transportation': 'Gas stations, rideshare, public transit, car expenses',
            'shopping': 'Retail purchases, online shopping, clothing, electronics',
            'bills_utilities': 'Electric, water, internet, phone bills, utilities',
            'entertainment': 'Streaming services, movies, games, events, recreation',
            'healthcare': 'Medical, dental, pharmacy, health-related expenses',
            'income': 'Salary deposits, interest, refunds, incoming transfers',
            'fees': 'Bank fees, penalties, service charges, maintenance fees',
            'other': 'Transactions that don\'t clearly fit other categories'
        }
        
        print(f"🧠 {self.name} initialized - Will use LLM for unclear transactions")
    
    def process(self, transactions: List[Dict]) -> List[Dict]:
        """
        Process transactions - only LLM call for uncategorized ones
        """
        
        # Separate already categorized vs needs LLM
        already_categorized = [t for t in transactions if t['category'] != 'uncategorized']
        needs_llm = [t for t in transactions if t['category'] == 'uncategorized']
        
        print(f"\n🧠 {self.name} processing:")
        print(f"   ✅ Already categorized: {len(already_categorized)}")
        print(f"   🤖 Needs LLM analysis: {len(needs_llm)}")
        
        if not needs_llm:
            print("   🎉 No LLM call needed - all transactions already categorized!")
            return already_categorized
        
        # SINGLE LLM CALL for all unclear transactions
        print(f"   🚀 Making 1 LLM call to categorize {len(needs_llm)} transactions...")
        llm_categorized = self._batch_categorize_with_llm(needs_llm)
        self.llm_calls_made += 1
        
        print(f"   ✅ LLM categorization complete!")
        
        return already_categorized + llm_categorized
    
    def _batch_categorize_with_llm(self, transactions: List[Dict]) -> List[Dict]:
        """
        Use Claude to categorize unclear transactions in ONE call
        This is the only LLM call in Agent 2
        """
        
        # Prepare batch data for Claude
        transaction_data = []
        for i, txn in enumerate(transactions):
            transaction_data.append({
                'id': f"txn_{i}",
                'description': txn['description'],
                'amount': txn['amount'],
                'is_debit': txn['is_debit'],
                'date': txn['date']
            })
        
        # Create comprehensive prompt for Claude
        system_prompt = f"""You are a financial transaction categorizer. 
        
Categorize transactions into these categories ONLY:
{json.dumps(self.valid_categories, indent=2)}

Rules:
1. Choose the MOST APPROPRIATE category from the list above
2. If unclear, use 'other' category
3. Provide confidence score 0-1 (1 = very confident, 0.5 = uncertain)
4. Give brief reasoning for your choice

Return ONLY valid JSON with this exact structure:
{{"categorizations": [{{"transaction_id": "txn_0", "category": "food_dining", "confidence": 0.85, "reasoning": "Coffee shop purchase"}}]}}"""

        user_prompt = f"Categorize these unclear transactions:\n{json.dumps(transaction_data, indent=2)}"
        
        try:
            # Make the LLM call
            response = self.llm.make_call(user_prompt, system_prompt)
            
            if response:
                # Validate response structure using Pydantic
                result = BatchCategorizationResponse(**json.loads(response))
                return self._apply_llm_categorization(transactions, result.categorizations)
            else:
                print("   ❌ LLM call failed - applying fallback categorization")
                return self._apply_fallback_categorization(transactions)
                
        except Exception as e:
            print(f"   ❌ LLM categorization error: {e}")
            return self._apply_fallback_categorization(transactions)
    
    def _apply_llm_categorization(self, transactions: List[Dict], categorizations: List[TransactionCategory]) -> List[Dict]:
        """Apply Claude's categorizations to transactions"""
        
        # Create lookup dict for fast matching
        cat_lookup = {cat.transaction_id: cat for cat in categorizations}
        
        for i, txn in enumerate(transactions):
            txn_id = f"txn_{i}"
            if txn_id in cat_lookup:
                cat = cat_lookup[txn_id]
                txn['category'] = cat.category
                txn['confidence'] = cat.confidence
                txn['source'] = 'llm'
                txn['reasoning'] = cat.reasoning
                print(f"   🤖 {txn['description'][:25]}... → {cat.category} ({cat.confidence:.1%})")
            else:
                # Fallback if LLM didn't categorize this one
                txn['category'] = 'other'
                txn['confidence'] = 0.5
                txn['source'] = 'fallback'
                txn['reasoning'] = 'LLM response incomplete'
        
        return transactions
    
    def _apply_fallback_categorization(self, transactions: List[Dict]) -> List[Dict]:
        """Fallback when LLM completely fails"""
        print("   🛟 Applying fallback categorization...")
        
        for txn in transactions:
            txn['category'] = 'other'
            txn['confidence'] = 0.3
            txn['source'] = 'fallback'
            txn['reasoning'] = 'LLM unavailable'
        
        return transactions