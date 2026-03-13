"""Extract key text from document images (invoice, note, salary slip) via OpenRouter vision."""
import base64
import logging
import re
from pathlib import Path

from openai import AsyncOpenAI

from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, VISION_MODEL

DOCUMENT_EXTRACT_SYSTEM = (
    "You are a document OCR assistant for financial documents. Extract key text and "
    "**calculate the correct final amount** that should be used when recording the transaction.\n\n"
    "**Rules:**\n"
    "1. **Salary slip / payslip:** Use Total Salary / Net Salary / Gaji Bersih (take-home after deductions). "
    "Do NOT use Total Income or gross. Formula: Total Income minus Total Potongan (deductions) = final amount.\n"
    "2. **Receipt / invoice:** Use the amount actually paid. Subtotal (HARGA JUAL) minus all deductions "
    "(vouchers, discounts, canceled items). Sum each voucher/deduction and subtract from subtotal.\n"
    "3. **Other docs:** Use the single main amount (total paid, net amount, or final balance).\n\n"
    "Output plain text with key facts (amounts, dates, descriptions). At the very end add exactly one line:\n"
    "FINAL_AMOUNT: <number>\n"
    "where <number> is the final amount as integer with no spaces (e.g. 4936928 or 116550). "
    "No currency symbol, no dots or commas in the number. If you cannot compute it, omit the FINAL_AMOUNT line.\n"
    "If the image is not a financial document, say 'Not a document' and nothing else."
)

_vision_client: AsyncOpenAI | None = None


def _get_vision_client() -> AsyncOpenAI | None:
    if not OPENROUTER_API_KEY:
        return None
    global _vision_client
    if _vision_client is None:
        _vision_client = AsyncOpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=OPENROUTER_API_KEY,
        )
    return _vision_client


def _encode_image_to_base64(path: Path) -> str:
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    suffix = path.suffix.lower()
    mime = "image/jpeg" if suffix in (".jpg", ".jpeg") else "image/png"
    return f"data:{mime};base64,{data}"


async def extract_document_text(image_path: Path) -> str:
    """
    Send image to OpenRouter vision model and return extracted key text.
    Returns empty string if OpenRouter is not configured or request fails.
    """
    client = _get_vision_client()
    if not client:
        return ""

    try:
        base64_url = _encode_image_to_base64(image_path)
        response = await client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": DOCUMENT_EXTRACT_SYSTEM,
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract the key text from this document image."},
                        {
                            "type": "image_url",
                            "image_url": {"url": base64_url},
                        },
                    ],
                },
            ],
        )
        text = (response.choices[0].message.content or "").strip()
        return text
    except Exception:
        logging.exception("Document vision extraction failed")
        return ""


def parse_final_amount(extracted_text: str) -> float | None:
    """
    Parse FINAL_AMOUNT line from vision output. Handles "FINAL_AMOUNT: 4936928" or "FINAL_AMOUNT: 4.936.928".
    Returns the number or None if not found.
    """
    if not extracted_text:
        return None
    match = re.search(r"FINAL_AMOUNT\s*:\s*([0-9.,]+)", extracted_text, re.IGNORECASE)
    if not match:
        return None
    raw = match.group(1).replace(".", "").replace(",", "")
    if not raw.isdigit():
        return None
    return float(raw)
