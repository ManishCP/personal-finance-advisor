import anthropic
import json
from typing import List, Dict, Optional

class LLMInterface:
    """
    Centralized Anthropic Claude management
    Tracks every call for cost analysis
    """

    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.call_count = 0    # Track total calls
        self.total_cost = 0.0  # Track estimated cost

    def make_call(self, prompt: str, system_prompt: str = None) -> Optional[str]:
        """
        Single point for ALL LLM calls in your system
        Every agent must use this method
        """
        self.call_count += 1
        print(f"🤖 LLM Call #{self.call_count} - Claude API")

        try:
            # Build message
            messages = []
            if system_prompt:
                messages.append({"role": "user", "content": f"System: {system_prompt}\n\nUser: {[prompt]}"})
            else:
                messages.append({"role": "user", "content": prompt})

            # Make Claude API call
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                messages=messages
            )

            # Track cost (using project estimate)
            self.total_cost += 0.002

            return response.content[0].text
        
        except Exception as e:
            print(f"❌ Claude API call failed: {e}")
            return None
        
    def get_metrics(self) -> Dict:
        """Report usage statistics"""
        return {
            'total_calls': self.call_count,
            'estimated_cost': self.total_cost,
            'average_cost_per_call': 0.002
        }
        
    def reset_counters(self):
        """Reset for new analysis session"""
        self.call_count = 0
        self.total_cost = 0.0