import requests


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "qwen2.5:1.5b"

# Keep interactive dashboard requests short.
OLLAMA_TIMEOUT = 45


def generate_insight(prompt):
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 80,
        },
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=OLLAMA_TIMEOUT,
        )

        response.raise_for_status()

        result = response.json()

        answer = result.get("response", "").strip()

        if not answer:
            raise RuntimeError("Ollama returned an empty response.")

        return answer

    except requests.exceptions.Timeout:
        raise RuntimeError(
            "Local GenAI inference timed out. "
            "The analytical insight engine can still answer supported questions."
        )

    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Ollama is not running. "
            "Start Ollama before using GenAI fallback questions."
        )

    except requests.exceptions.RequestException as exc:
        raise RuntimeError(
            f"Ollama request failed: {exc}"
        )
