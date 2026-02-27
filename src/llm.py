from __future__ import annotations

import os
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel


def get_chat_model() -> BaseChatModel:
    """
    Return a chat model based on environment configuration.

    Supported providers (set AUDITOR_LLM_PROVIDER):
    - openai (default if OPENAI_API_KEY exists)
    - groq
    - gemini
    """
    provider = (os.getenv("AUDITOR_LLM_PROVIDER") or "").strip().lower()

    if not provider:
        if os.getenv("OPENAI_API_KEY"):
            provider = "openai"
        elif os.getenv("GROQ_API_KEY"):
            provider = "groq"
        elif os.getenv("GOOGLE_API_KEY"):
            provider = "gemini"
        else:
            raise RuntimeError(
                "No LLM provider configured. Set AUDITOR_LLM_PROVIDER and the matching API key "
                "(OPENAI_API_KEY, GROQ_API_KEY, or GOOGLE_API_KEY)."
            )

    model_name: Optional[str] = os.getenv("AUDITOR_LLM_MODEL")

    if provider == "openai":
        from langchain_openai import ChatOpenAI  # type: ignore[import]

        # Recommended: gpt-4o (best general-purpose, supports structured output well)
        return ChatOpenAI(model=model_name or "gpt-4o")

    if provider == "groq":
        from langchain_groq import ChatGroq  # type: ignore[import]

        # Recommended free-tier model: Llama 3.1 70B Versatile
        return ChatGroq(model=model_name or "llama-3.1-70b-versatile")

    if provider in {"gemini", "google"}:
        from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore[import]

        # Recommended free-tier model: gemini-1.5-flash (fast, good for tool/JSON)
        return ChatGoogleGenerativeAI(model=model_name or "gemini-1.5-flash")

    raise RuntimeError(f"Unsupported AUDITOR_LLM_PROVIDER='{provider}'.")

