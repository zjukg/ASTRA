import json
import re
import time

import requests
from openai import OpenAI

from astra_config import get_local_model_base_url, require_openai_client_config


SYSTEM_PROMPT = (
    "You are a professional data analyst who specializes in structured table reasoning."
)


class OpenaimodelClient:
    def __init__(self, model: str, api_key: str = "", base_url: str = ""):
        resolved_api_key, resolved_base_url = require_openai_client_config(
            model=model,
            api_key=api_key,
            base_url=base_url,
        )
        self.model = model
        self.client = OpenAI(api_key=resolved_api_key, base_url=resolved_base_url)

    def generate(
        self,
        prompt: str,
        max_length: int = 16384,
        temperature: float = 0.3,
        timeout: int = 30000,
    ) -> str:
        max_tokens = 8192 if "deepseek-chat" in self.model else max_length
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
            timeout=timeout / 1000,
        )
        return response.choices[0].message.content or ""


class ModelClient:
    def __init__(self, base_url: str = ""):
        self.base_url = base_url or get_local_model_base_url()

    def _build_messages(self, prompt: str) -> list[dict]:
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

    def test_generate(
        self,
        prompt: str,
        max_length: int = 100,
        temperature: float = 0.7,
        timeout: int = 300,
    ):
        try:
            response = requests.post(
                f"{self.base_url}/generate",
                json={
                    "messages": self._build_messages(prompt),
                    "max_length": max_length,
                    "temperature": temperature,
                },
                timeout=timeout,
            )
            if response.status_code == 200:
                return response.json()
            return None
        except requests.exceptions.Timeout:
            return None
        except Exception:
            return None

    def test_generate_stream(
        self,
        prompt: str,
        max_length: int = 32768,
        temperature: float = 0.3,
        timeout: int = 600,
        stop_on_json_repeat: bool = True,
        json_repeat_count: int = 111,
    ) -> str | None:
        try:
            response = requests.post(
                f"{self.base_url}/generate_stream",
                json={
                    "messages": self._build_messages(prompt),
                    "max_length": max_length,
                    "temperature": temperature,
                },
                stream=True,
                timeout=timeout,
            )
            if response.status_code != 200:
                return None

            full_text = ""
            start_time = time.time()
            json_code_block_count = 0

            for line in response.iter_lines():
                if not line:
                    continue

                decoded = line.decode("utf-8")
                if not decoded.startswith("data: "):
                    continue

                data_str = decoded[6:]
                if data_str == "[DONE]":
                    break

                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                if data["type"] == "chunk":
                    full_text = data["full_text"]
                    if stop_on_json_repeat:
                        json_code_block_count += data["text"].count("```json")
                        if json_code_block_count >= json_repeat_count:
                            return full_text
                elif data["type"] == "end":
                    return full_text
                elif data["type"] == "error":
                    return None

            _ = time.time() - start_time
            return full_text
        except requests.exceptions.Timeout:
            return None
        except Exception:
            return None

    def test_generate_stream_advanced(
        self,
        prompt: str,
        max_length: int = 2048,
        temperature: float = 0.3,
        timeout: int = 600,
        stop_on_json_repeat: bool = True,
        json_repeat_count: int = 3,
    ) -> str | None:
        try:
            response = requests.post(
                f"{self.base_url}/generate_stream",
                json={
                    "prompt": prompt,
                    "max_length": max_length,
                    "temperature": temperature,
                },
                stream=True,
                timeout=timeout,
            )
            if response.status_code != 200:
                return None

            full_text = ""
            for line in response.iter_lines():
                if not line:
                    continue

                decoded = line.decode("utf-8")
                if not decoded.startswith("data: "):
                    continue

                data_str = decoded[6:]
                if data_str == "[DONE]":
                    break

                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                if data["type"] == "chunk":
                    full_text = data["full_text"]
                    if stop_on_json_repeat:
                        json_code_block_count = len(re.findall(r"```json", full_text))
                        if json_code_block_count >= json_repeat_count:
                            return self._clean_repeated_json_output(full_text, json_repeat_count)
                elif data["type"] == "end":
                    return full_text
                elif data["type"] == "error":
                    return None

            return full_text
        except requests.exceptions.Timeout:
            return None
        except Exception:
            return None

    def _clean_repeated_json_output(self, text: str, max_json_blocks: int = 2) -> str:
        json_block_starts = [match.start() for match in re.finditer(r"```json", text)]
        if len(json_block_starts) <= max_json_blocks:
            return text

        cutoff_position = json_block_starts[max_json_blocks - 1]
        remaining_text = text[cutoff_position:]
        end_match = re.search(r"```\s*$|```\s+", remaining_text)
        if end_match:
            return text[: cutoff_position + end_match.end()]

        next_json_start = (
            json_block_starts[max_json_blocks]
            if len(json_block_starts) > max_json_blocks
            else len(text)
        )
        return text[:next_json_start].rstrip()
