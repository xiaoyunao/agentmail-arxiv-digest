from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .profiles import InterestProfile
from .ranker import RankedPaper
from .triage import TRIAGE_SCHEMA, TriagedPaper, build_triage_prompt, parse_triage_decision, select_triaged


DEFAULT_TRIAGE_MODEL = "gpt-5.4-mini"


class OpenAITriageClient:
    """Small OpenAI Responses API client for relevance triage."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model or os.environ.get("OPENAI_TRIAGE_MODEL", DEFAULT_TRIAGE_MODEL)
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI triage")

    def triage_one(self, profile: InterestProfile, ranked: RankedPaper) -> TriagedPaper:
        payload = {
            "model": self.model,
            "reasoning": {"effort": "low"},
            "input": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Return only valid JSON for the requested schema.",
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": build_triage_prompt(profile, ranked)}],
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "arxiv_triage_decision",
                    "schema": TRIAGE_SCHEMA,
                    "strict": True,
                }
            },
        }
        response = self._post_json(payload)
        decision = parse_triage_decision(_extract_response_text(response), ranked.paper.arxiv_id)
        return TriagedPaper(ranked=ranked, decision=decision)

    def _post_json(self, payload: dict) -> dict:
        request = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI API error {exc.code}: {body}") from exc


def triage_with_openai(
    profile: InterestProfile,
    ranked: list[RankedPaper],
    *,
    model: str | None = None,
) -> list[TriagedPaper]:
    client = OpenAITriageClient(model=model)
    return select_triaged(profile, [client.triage_one(profile, item) for item in ranked])


def _extract_response_text(response: dict) -> str:
    if "output_text" in response:
        return response["output_text"]

    chunks: list[str] = []
    for output in response.get("output", []):
        for content in output.get("content", []):
            if content.get("type") in {"output_text", "text"} and "text" in content:
                chunks.append(content["text"])
    if chunks:
        return "".join(chunks)
    raise RuntimeError("OpenAI response did not contain output text")
