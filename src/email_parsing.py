"""Extracts a structured delay signal from unstructured carrier-email text.

Real carrier emails phrase delays in all sorts of ways ("delay of
approximately 5 days", "Estimated delay: 4 business days", "ETA slipping ~2
days"). `CarrierEmailTable.delay_days_mentioned`/`.reason` are pre-tagged
columns (as if a human analyst — or an upstream system — had already read
the email), but RiskDetectionExecutor has no business shortcutting through
them; that would mean the pipeline never actually reads the unstructured
`subject`/`body` fields it claims to ingest. This module is what actually
reads that free text.

Uses an LLM (Azure OpenAI, when AZURE_OPENAI_ENDPOINT is configured, via
src/llm.py) for robust extraction over arbitrary phrasing; falls back to a
regex-based extractor over the same raw text otherwise, so behavior is identical
with or without Azure configured — no .env exists locally, so the regex path is
what actually runs today.
"""

import json
import logging
import re

from pydantic import BaseModel

from src.llm import complete as llm_complete

logger = logging.getLogger("supply_chain_agent.email_parsing")

_DELAY_DAYS_PATTERN = re.compile(r"delay[^\d]{0,20}?(\d+(?:\.\d+)?)\s*(?:business\s+)?days?", re.IGNORECASE)
_REASON_PATTERNS = [
    re.compile(r"root cause:?\s*([^.\n]+)", re.IGNORECASE),
    re.compile(r"due to ([^.\n]+)", re.IGNORECASE),
    re.compile(r"reason:?\s*([^.\n]+)", re.IGNORECASE),
]
_DELAY_KEYWORDS = ("delay", "stall", "disrupt", "hold", "congestion", "urgent")


class EmailDelaySignal(BaseModel):
    mentions_delay: bool = False
    delay_days: float = 0.0
    reason: str = ""


def _regex_extract(subject: str, body: str) -> EmailDelaySignal:
    text = f"{subject}\n{body}"

    delay_days = 0.0
    if match := _DELAY_DAYS_PATTERN.search(text):
        delay_days = float(match.group(1))

    reason = ""
    for pattern in _REASON_PATTERNS:
        if match := pattern.search(text):
            reason = match.group(1).strip().rstrip(".")
            break

    mentions_delay = delay_days > 0 or any(kw in text.lower() for kw in _DELAY_KEYWORDS)
    return EmailDelaySignal(mentions_delay=mentions_delay, delay_days=delay_days, reason=reason)


async def _llm_extract(subject: str, body: str) -> EmailDelaySignal | None:
    """Best-effort LLM extraction. Returns None on any failure so the caller falls back."""
    prompt = (
        "Extract shipment delay information from this carrier email. "
        "Respond with ONLY a JSON object, no other text: "
        '{"mentions_delay": <bool>, "delay_days": <number>, "reason": "<short phrase>"}\n\n'
        f"Subject: {subject}\n\nBody:\n{body}"
    )
    raw = await llm_complete(prompt)
    if raw is None:
        return None
    try:
        cleaned = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return EmailDelaySignal.model_validate(json.loads(cleaned))
    except (json.JSONDecodeError, ValueError):
        logger.warning("Could not parse LLM email-extraction JSON, falling back to regex", exc_info=True)
        return None


async def parse_email_delay_signal(subject: str, body: str) -> EmailDelaySignal:
    """Extracts a delay signal from raw email text — LLM when configured, regex otherwise."""
    return await _llm_extract(subject, body) or _regex_extract(subject, body)
