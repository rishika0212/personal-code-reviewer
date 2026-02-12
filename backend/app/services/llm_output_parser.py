import json
import logging
from typing import Optional, Any, Dict

logger = logging.getLogger(__name__)

def safe_parse_json(raw_text: str) -> Optional[Dict[str, Any]]:
    """
    Attempts to parse JSON from LLM output safely.
    Handles common issues like markdown code blocks and leading/trailing text.
    Returns None if parsing fails.
    """
    if not raw_text:
        return None
        
    try:
        # Try direct parse first
        return json.loads(raw_text)
    except json.JSONDecodeError:
        try:
            # Try to extract JSON from markdown or other surrounding text
            start = raw_text.find("{")
            end = raw_text.rfind("}") + 1
            
            if start >= 0 and end > start:
                return json.loads(raw_text[start:end])
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse failed even after extraction: {e}")
            
    return None

async def repair_and_parse(raw_text: str, llm_service) -> Optional[Dict[str, Any]]:
    """
    Attempts to parse JSON, and if it fails, asks the LLM to repair it.
    Returns None if repair also fails.
    """
    parsed = safe_parse_json(raw_text)
    if parsed is not None:
        return parsed

    logger.info("LLM output is malformed. Attempting repair...")
    
    repair_prompt = f"""
The following text was intended to be valid JSON but is malformed.

Fix it so that:
- The output is VALID JSON
- No explanation
- No markdown
- No extra text

Text:
{raw_text}
"""

    try:
        repaired = await llm_service.generate(
            system_prompt="You are a JSON repair tool. Output ONLY valid JSON.",
            user_prompt=repair_prompt,
            temperature=0.0  # Use 0.0 for deterministic output during repair
        )
        
        return safe_parse_json(repaired)
    except Exception as e:
        logger.error(f"Repair attempt failed: {e}")
        return None
