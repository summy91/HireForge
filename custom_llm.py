# custom_llms.py

import os
import requests
from typing import List, Optional
from dotenv import load_dotenv
from langchain_core.language_models import LLM
import  json

load_dotenv(override=True)
config = os.environ

class CustomLLM(LLM):
    """Custom LLM wrapper for LangChain using a REST API."""
    model: str
    endpoint_url: str
    headers: dict = {
        "Content-Type": "application/json",
        "X-API-KEY":  config["API_KEY"]
    }
    temperature: float = 0.7
    top_p: float = 1.0
    max_tokens: int = 2000
    stream: bool = False
    stop: Optional[List[str]] = None

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
        }
        if stop:
            payload["stop"] = stop

        response = requests.post(self.endpoint_url, headers=self.headers, json=payload)
        response.raise_for_status()
        data = response.json()
        print("aah:", json.dumps(data, indent=2))

        return data['choices'][0]['message']['content']

    @property
    def _llm_type(self) -> str:
        return "custom-llm"

# Load one or more models as needed
custom_claude = CustomLLM(
    model="claude-opus-4",
    endpoint_url="https://quasarmarket.coforge.com/aistudio-llmrouter-api/api/v2/chat/completions",
    temperature=0.5,
    top_p=0.9,
    max_tokens=1000
)

custom_gpt = CustomLLM(
    model="gpt-4o",
    endpoint_url="https://quasarmarket.coforge.com/aistudio-llmrouter-api/api/v2/chat/completions",
    temperature=0.5,
    top_p=0.9,
    max_tokens=1000
)

