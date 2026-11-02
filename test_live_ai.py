
import os

from dotenv import load_dotenv
from app.agents.triage_agent import classify_with_ai

load_dotenv()

print("Provider:", os.getenv("LLM_PROVIDER"))

result = classify_with_ai(
    "Candidate synchronization failed. "
    "Production API returns HTTP 500."
)

print("Category:", result.category)
print("Priority:", result.priority)
print("Reasoning:", result.reasoning)
