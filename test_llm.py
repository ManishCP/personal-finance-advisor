import os
from dotenv import load_dotenv
from utils.llm_interface import LLMInterface

load_dotenv()

api_key = os.getenv('ANTHROPIC_API_KEY')
llm = LLMInterface(api_key)

# Test simple call
response = llm.make_call("Say hello!")
print(f"Claude said: {response}")
print(f"Metrics: {llm.get_metrics()}")