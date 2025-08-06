import os
from custom_embeddings import CustomEmbeddings
from typing import List, Dict
from custom_llm import custom_gpt
import json
import time

def get_embedding(texts: List[str]):
    embedder = CustomEmbeddings()
    vectors = []

    for text in texts:
        # Wrap text in list since embed_documents expects a list
        embedding = embedder.embed_documents([text])

        # embedding will be a single vector (not a list of vectors), so just append it
        if isinstance(embedding, list) and all(isinstance(x, float) for x in embedding):
            vectors.append(embedding)
        else:
            raise ValueError(f"Invalid embedding format: {embedding}")

    return vectors

from typing import List, Dict
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def rank_resumes_by_job_description(
    resumes: List[Dict],
    job_description: str,
    job_embedding: List[float],
    top_k: int = 3,
) -> List[Dict]:
    """
    Ranks resumes by cosine similarity with the job description embedding.
    """

# Filter out resumes that failed to embed
    valid_resumes = [r for r in resumes if "embedding" in r]

    if not valid_resumes:
        return resumes

    # Convert embeddings to NumPy arrays
    resume_vectors = np.array([r["embedding"] for r in valid_resumes])
    job_vector = np.array(job_embedding).reshape(1, -1)

    # Compute cosine similarities
    similarities = cosine_similarity(resume_vectors, job_vector).flatten()

    # Attach similarity scores
    for resume, score in zip(valid_resumes, similarities):
        resume["similarity_score"] = round(float(score), 4)  # Round for readability

    # Sort by similarity
    ranked = sorted(valid_resumes, key=lambda r: r["similarity_score"], reverse=True)

    # Optional: return top_k resumes
    return ranked[:top_k]


def score_resumes_by_job_description(resumes, job_description):
    scored = []

    for r in resumes:
        resume_text = r.get("text", "")
        prompt = f"""
        You are a hiring expert. Score how well this resume matches the following job description from 0 to 100.
        Return only a **raw JSON object** (no markdown, no explanation), like:
        {{
          "name": "...",
          "email": "...",
          "score": "...",
          "skills": ["...", "..."],
          "justification": "..."
        }}

        Job Description:
        {job_description}

        Resume:
        {resume_text}
        """

        try:
            time.sleep(1)
            response = custom_gpt.invoke(prompt)
            print("response:", json.dumps(response, indent=2))

            import re
            content = re.sub(r"```(?:json)?\n?", "", response).strip("` \n")

            parsed = json.loads(content)

            scored.append({
                "name": parsed.get("name", ""),
                "email": parsed.get("email", ""),
                "score": parsed.get("score", 0),
                "skills":parsed.get("skills", []),
                "justification": parsed.get("justification", "")
            })
        except Exception as e:
            scored.append({
                "name": r,
                "score": 0,
                "error": str(e)
            })

    return scored
