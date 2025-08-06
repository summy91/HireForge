from langchain_core.embeddings import Embeddings
from typing import List, Optional
import requests
from dotenv import load_dotenv
import os
import json

load_dotenv(override=True)
config = os.environ

class CustomEmbeddings(Embeddings):
    """Custom Embeddings wrapper for LangChain using a REST API."""

    dimensions: Optional[int] = 746
    endpoint_url: str = "https://quasarmarket.coforge.com/aistudio-llmrouter-api/api/v2/text/embeddings"
    headers: dict = {
        "Content-Type": "application/json",
        "X-API-KEY": config["API_KEY"]
    }

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents."""
        payload = {
            "texts": texts,
            "dimensions": 736
        }
        # print("Payload:", json.dumps(payload, indent=2))

        try:
            response = requests.post(self.endpoint_url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()

            # Debug print
            # print("Response:", json.dumps(data, indent=2))
            return data["embeddings"]

        except Exception as e:
            print(f"Embedding API failed: {e}")
            return [[0.0] * 746 for _ in texts]  # Fallback dummy embedding

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query/document."""
        return self.embed_documents([text])[0]

# === Example Usage ===
if __name__ == "__main__":
    embeddings = CustomEmbeddings()
    texts = ['hi', 'there'] #Feed text to embed in array format
    embedding_vector = embeddings.embed_documents(texts)
    print("Embedding:", embedding_vector)