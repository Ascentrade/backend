import os
import json
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Try importing Google Gemini (optional dependency)
try:
    import google.genai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class LLMProvider:

    def __init__(self):
        raw_provider = os.getenv("AI_PROVIDER", "openai")
        self.provider = (raw_provider or "openai").strip().lower()

        if self.provider in {"openai", "openai_api"}:
            self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.client_type = "openai"
        elif self.provider == "gemini":
            if not GEMINI_AVAILABLE:
                raise ImportError(
                    "Google Gemini is not installed. Install it with: pip install google-genai"
                )
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            if not gemini_api_key:
                raise ValueError("GEMINI_API_KEY environment variable is required")
            self.client = genai.Client(api_key=gemini_api_key)
            self.client_type = "gemini"
        elif self.provider in {"local", "openai_compatible", "openai-compatible"}:
            # Local LLM via OpenAI-compatible endpoint
            self.client = AsyncOpenAI(
                api_key="local",
                base_url=os.getenv("LOCAL_LLM_URL", "http://localhost:11434/v1"),
            )
            self.client_type = "openai_compatible"
        else:
            raise ValueError(
                f"Unknown AI_PROVIDER={raw_provider!r}. Expected 'openai', 'gemini', or 'local'."
            )


    async def chat(self, system_prompt: str, user_prompt: str) -> dict:
        temperature = float(os.getenv("AI_TEMPERATURE", "0.2"))
        timeout = int(os.getenv("AI_TIMEOUT", "30"))

        if self.client_type == "gemini":
            # Use Google Gemini API
            model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
            
            # Combine system and user prompts for Gemini
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Use the new google.genai API
            response = await self.client.models.generate_content(
                model=model_name,
                contents=full_prompt,
                config={
                    "temperature": temperature,
                }
            )
            
            content = response.text
            
        elif self.client_type == "openai" or self.client_type == "openai_compatible":
            # Use OpenAI or OpenAI-compatible API
            model = (
                os.getenv("OPENAI_MODEL", "gpt-4.1")
                if self.client_type == "openai"
                else os.getenv("LOCAL_LLM_MODEL", "llama3")
            )

            response = await self.client.chat.completions.create(
                model=model,
                temperature=temperature,
                timeout=timeout,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

            content = response.choices[0].message.content
        else:
            raise ValueError(f"Unknown client type: {self.client_type}")

        return json.loads(content)
