
import os
import requests
from dotenv import load_dotenv

load_dotenv()

SYSTEM = (
    "You are Apnar Mentor AI, a friendly personal mentor for a student in Bangladesh. "
    "Reply in the same language the user writes in (Bengali, Banglish or English). "
    "Keep replies short (2-5 sentences), practical and encouraging. "
    "Use the user data below when relevant, never invent numbers."
)


def generate_response(prompt: str, context: str = "", history=None) -> str:
    provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
    model = os.getenv("OLLAMA_MODEL", "qwen3.5:2b").strip()
    ollama_url = os.getenv(
        "OLLAMA_URL", "http://127.0.0.1:11434"
    ).rstrip("/")
    timeout = int(os.getenv("OLLAMA_TIMEOUT", "300"))

    if provider != "ollama":
        raise RuntimeError(f"Unsupported LLM provider: {provider}")

    system = SYSTEM
    if context:
        system += "\n\nUSER DATA:\n" + context

    messages = [{"role": "system", "content": system}]

    for m in (history or [])[-8:]:
        if m.get("role") in ("user", "assistant"):
            messages.append({
                "role": m["role"],
                "content": str(m.get("content", ""))
            })

    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "think": False,
        "keep_alive": "30m",
        "options": {
            "num_predict": 200,
            "num_ctx": 2048
        }
    }

    try:
        response = requests.post(
            f"{ollama_url}/api/chat",
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()

        data = response.json()
        reply = data.get("message", {}).get("content", "").strip()

        if not reply:
            raise RuntimeError(
                f"Ollama returned empty content. Response: {data}"
            )

        return reply

    except requests.exceptions.Timeout as e:
        raise RuntimeError(
            f"Ollama timeout after {timeout}s. Check whether the model is loading."
        ) from e

    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(
            f"Cannot connect to Ollama at {ollama_url}. "
            "Check whether Ollama is running."
        ) from e

    except requests.exceptions.HTTPError as e:
        raise RuntimeError(
            f"Ollama HTTP error: {e}. "
            f"Response: {response.text[:500]}"
        ) from e

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Ollama request failed: {e}") from e
