import os
from typing import Dict, List

from openai import OpenAI

API_KEY = os.getenv("MY_API_KEY")
if not API_KEY:
    raise ValueError("API key not found. Please set the MY_API_KEY environment variable.")

client = OpenAI(api_key=API_KEY)

def call_llm(model_name: str, prompt_text: str, max_tokens: int = 1200, temperature: float = 0.7) -> str:
    # Safety cap to avoid context_length_exceeded
    if len(prompt_text) > 12000:
        prompt_text = prompt_text[:12000]

    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt_text}],
        max_tokens=max_tokens,
        temperature=temperature,
    )

    return response.choices[0].message.content.strip()
