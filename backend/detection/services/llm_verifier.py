# backend/detection/services/llm_verifier.py

import os
import logging
import time
import json
import numpy as np
from pathlib import Path
from PIL import Image
import base64
from io import BytesIO
import asyncio
from django.conf import settings # Import Django settings

# --- Use AsyncOpenAI library --- (Ensure installed: pip install openai)
try:
    from openai import AsyncOpenAI
except ImportError:
    logging.error("OpenAI library not installed. Please install it: pip install openai")
    AsyncOpenAI = None

logger = logging.getLogger(__name__)

# --- Configuration (Adapted from llm_cross_validation.py, uses Django settings) ---
API_KEY = settings.OPENROUTER_API_KEY
# Use environment variables for site URL/Name, or defaults
YOUR_SITE_URL = os.environ.get("YOUR_SITE_URL", "http://localhost")
YOUR_SITE_NAME = os.environ.get("YOUR_SITE_NAME", "MM-DFD-Backend")

# Define models (Consider making these configurable in settings.py too)
OR_TEXT_MODELS = [
    "perplexity/sonar-reasoning-pro",
    "perplexity/sonar",
    "google/gemini-2.0-flash-001", # Supports vision
    "deepseek/deepseek-r1",
    "deepseek/deepseek-chat-v3-0324",
]
OR_IMAGE_MODELS = [
    "google/gemini-2.0-flash-001",
]

MODEL_WEIGHTS = {
    "perplexity/sonar-reasoning-pro": 0.4,
    "perplexity/sonar": 0.2,
    "google/gemini-2.0-flash-001": 0.15,
    "deepseek/deepseek-r1": 0.15,
    "deepseek/deepseek-chat-v3-0324": 0.1,
}

DEFAULT_API_DELAY = 1.0 # Adjusted async delay

# --- Helper Functions (Mostly copied from llm_cross_validation.py) ---

def load_image_as_base64(image_path):
    """Loads an image file and returns its base64 encoded string."""
    if not image_path:
        logger.warning("No image path provided to load_image_as_base64.")
        return None
    abs_path = Path(image_path)
    if not abs_path.is_file():
        logger.error(f"Image file not found or is not a file: {abs_path}")
        return None
    try:
        logger.info(f"Loading image for LLM from: {abs_path}")
        with Image.open(abs_path) as img:
            output_format = "JPEG" if img.format != "PNG" else "PNG"
            buffered = BytesIO()
            if output_format == "JPEG" and img.mode == 'RGBA': img = img.convert('RGB')
            img.save(buffered, format=output_format)
            img_byte = buffered.getvalue()
            return base64.b64encode(img_byte).decode('utf-8')
    except Exception as e:
        logger.warning(f"Could not load or encode image {abs_path}: {e}")
        return None

def format_structured_llm_response(model_name, success, data=None, error=None):
    """Standardizes the response format."""
    base_response = {
        "model": model_name,
        "success": success,
        "verdict": "Error" if not success else "Parsing Error",
        "confidence": 0.0,
        "reason": None,
        "error": str(error) if error else (None if success else "Unknown error during processing"),
        "raw_response": None
    }
    if success and isinstance(data, dict):
        base_response.update({
            "verdict": data.get("verdict", "Parsing Error"),
            "confidence": data.get("confidence", 0.0),
            "reason": data.get("reason", "No reason provided or parsing failed."),
            "error": None
        })
        try:
            confidence_val = float(base_response["confidence"])
            base_response["confidence"] = max(0.0, min(1.0, confidence_val))
        except (ValueError, TypeError):
            logger.warning(f"Model {model_name} returned non-numeric confidence: {base_response['confidence']}. Setting to 0.0.")
            base_response["confidence"] = 0.0
    elif not success and isinstance(data, str):
        base_response["raw_response"] = data
        base_response["error"] = f"Failed to parse LLM response as JSON. {base_response['error'] if base_response['error'] else ''}".strip()
    return base_response


async def call_openrouter_api_async(prompt, model_name, image_base64=None):
    """ASYNC calls the specified model via the OpenRouter API."""
    if not AsyncOpenAI: return format_structured_llm_response(model_name, False, error="AsyncOpenAI client not available.")
    if not API_KEY: return format_structured_llm_response(model_name, False, error="OpenRouter API key not configured in settings.")

    client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=API_KEY)
    messages = [{"role": "user", "content": []}]
    messages[0]["content"].append({"type": "text", "text": prompt})

    if image_base64 and model_name in OR_IMAGE_MODELS:
        try:
            mime = "image/jpeg" if image_base64.startswith("/9j/") else "image/png"
            image_url = f"data:{mime};base64,{image_base64}"
            messages[0]["content"].append({"type": "image_url", "image_url": {"url": image_url}})
            logger.info(f"Preparing image for vision model: {model_name}")
        except Exception as img_err:
             logger.error(f"Error processing image for model {model_name}: {img_err}")
             # Proceed without image if processing fails
    elif image_base64:
        logger.warning(f"Image provided, but model {model_name} not in vision list. Sending text only.")

    try:
        logger.debug(f"Calling OpenRouter model: {model_name}")
        completion = await client.chat.completions.create(
            extra_headers={"HTTP-Referer": YOUR_SITE_URL, "X-Title": YOUR_SITE_NAME},
            model=model_name,
            messages=messages,
            max_tokens=700,
            temperature=0.3,
            # response_format={"type": "json_object"}, # Uncomment if models support JSON reliably
        )
        raw_content = completion.choices[0].message.content
        logger.debug(f"Raw response from {model_name}: {raw_content}")

        try:
            if raw_content.strip().startswith("```json"):
                 raw_content = raw_content.strip()[7:-3].strip()
            elif raw_content.strip().startswith("```"):
                 raw_content = raw_content.strip()[3:-3].strip()
            parsed_data = json.loads(raw_content)
            if not isinstance(parsed_data, dict):
                 raise ValueError("Response is not a JSON object.")
            return format_structured_llm_response(model_name, True, data=parsed_data)
        except json.JSONDecodeError as json_err:
            logger.warning(f"Failed to parse JSON from {model_name}: {json_err}. Raw: {raw_content}")
            return format_structured_llm_response(model_name, False, error=f"JSONDecodeError: {json_err}", data=raw_content)
        except ValueError as val_err:
             logger.warning(f"Parsed JSON structure invalid from {model_name}: {val_err}. Raw: {raw_content}")
             return format_structured_llm_response(model_name, False, error=f"Invalid JSON Structure: {val_err}", data=raw_content)

    except Exception as e:
        logger.error(f"OpenRouter API call failed for model {model_name}: {e}")
        error_detail = str(e)
        # Attempt to get more info if available (depends on the specific exception)
        if hasattr(e, 'response') and hasattr(e.response, 'text'): error_detail += f" | Response: {e.response.text}"
        return format_structured_llm_response(model_name, False, error=error_detail)


async def verify_news_with_llms_async(text_input, image_path_input=None):
    """
    ASYNC verifies a news item using multiple LLMs and aggregates results.
    Returns the aggregated result dictionary.
    """
    logger.info("--- Starting LLM Verification (Async) ---")
    if not API_KEY:
        logger.error("OpenRouter API key is not configured in settings.")
        return {"error": "API key not configured.", "overall_verdict": "Error", "aggregated_confidence": 0.0}

    img_b64 = None
    if image_path_input:
        img_b64 = load_image_as_base64(image_path_input)
        if not img_b64:
            logger.warning(f"Failed to load image {image_path_input}, proceeding without it.")

    tasks = []
    if text_input:
        text_prompt = f"""请对以下新闻内容进行事实核查。请严格按照以下 JSON 格式返回你的分析结果，不要添加任何额外的解释性文字或markdown标记：
{{ "verdict": "判断结果", "confidence": 置信度分数, "reason": "理由/证据摘要" }}
判断结果必须是"真实"、"虚假"、"无法核实"或"混合信息"之一。置信度分数是一个 0.0 到 1.0 之间的小数。理由请提供简洁客观的分析依据。
新闻内容："{text_input}"""
        for model_id in OR_TEXT_MODELS:
            tasks.append(asyncio.create_task(call_openrouter_api_async(text_prompt, model_id))) # Removed api_key arg, uses global
            await asyncio.sleep(0.05)

    if img_b64:
        image_prompt = f"""请分析提供的图片，并结合以下新闻文本进行判断。请严格按照以下 JSON 格式返回你的分析结果：
{{ "verdict": "综合判断结果", "confidence": 置信度分数, "reason": "图片与文本关联性分析及判断理由" }}
综合判断结果是对结合图片和文本后新闻整体真实性的判断（真实/虚假/无法核实/混合信息）。置信度分数是你对此判断的确信程度（0.0-1.0）。
新闻文本："{text_input if text_input else '（无文本提供）'}"""
        if not text_input:
            image_prompt = f"""请分析提供的图片，判断它所描绘的场景或事件的真实性。请严格按照以下 JSON 格式返回你的分析结果：
{{ "verdict": "图片真实性判断", "confidence": 置信度分数, "reason": "图片分析理由（例如：是否像真实照片、AI生成、拼接、摆拍等）" }}
图片真实性判断是"真实"、"疑似伪造"、"无法判断"之一。"""
        for model_id in OR_IMAGE_MODELS:
             tasks.append(asyncio.create_task(call_openrouter_api_async(image_prompt, model_id, image_base64=img_b64))) # Removed api_key arg
             await asyncio.sleep(0.05)

    if not tasks:
        logger.warning("No text or image provided, LLM verification skipped.")
        return {"error": "No text or image for LLM verification.", "overall_verdict": "Skipped", "aggregated_confidence": 0.0}

    logger.info(f"Sending {len(tasks)} LLM API requests concurrently...")
    individual_results = await asyncio.gather(*tasks)
    logger.info("LLM API responses received.")

    text_results_raw = [res for res in individual_results if res['model'] in OR_TEXT_MODELS]
    image_results_raw = [res for res in individual_results if res['model'] in OR_IMAGE_MODELS]

    # --- Aggregation Logic (Focus on Text) ---
    final_verdict = "Inconclusive"
    final_confidence = 0.5
    needs_review = False
    valid_confidences = []
    valid_text_results = [r for r in text_results_raw if r['success'] and isinstance(r.get('confidence'), (int, float))]

    if valid_text_results:
        total_weight = 0
        weighted_sum_conf = 0 # Weighted sum of confidences
        weighted_sum_fake_lean = 0 # Weighted sum of leaning towards fake (1=Fake, 0=True, 0.5=Uncertain)

        for result in valid_text_results:
            model = result['model']
            weight = MODEL_WEIGHTS.get(model, 0)
            if weight > 0:
                confidence = result['confidence']
                verdict_str = result.get('verdict', '').lower()
                verdict_score = 0.5 # Default uncertain
                if '虚假' in verdict_str or 'fake' in verdict_str:
                    verdict_score = 1.0
                elif '真实' in verdict_str or 'true' in verdict_str:
                    verdict_score = 0.0

                weighted_sum_conf += weight * confidence
                # Weighted lean: use verdict score, potentially modified by confidence?
                # Simple approach: use verdict_score directly
                weighted_sum_fake_lean += weight * verdict_score
                total_weight += weight
                valid_confidences.append(confidence)

        if total_weight > 0:
            final_confidence = weighted_sum_conf / total_weight # Average confidence
            avg_fake_lean = weighted_sum_fake_lean / total_weight # Average lean towards fake

            if len(valid_confidences) > 1:
                confidence_std_dev = np.std(valid_confidences)
                if confidence_std_dev > 0.25: needs_review = True

            # Determine verdict based on average lean
            if avg_fake_lean >= 0.75:
                final_verdict = "Likely Fake"
            elif avg_fake_lean <= 0.25:
                final_verdict = "Likely True"
            elif avg_fake_lean > 0.4 and avg_fake_lean < 0.6:
                final_verdict = "Uncertain / Mixed Signals"
                needs_review = True # Flag middle ground for review too
            else:
                 final_verdict = "Uncertain"
        else:
            logger.warning("No valid text results with weights found for LLM aggregation.")
            final_verdict = "Aggregation Error"

    aggregated_result = {
        "overall_verdict": final_verdict,
        "aggregated_confidence": round(final_confidence, 3),
        "needs_manual_review": needs_review,
        "text_verifications": text_results_raw,
        "image_verifications": image_results_raw,
    }
    logger.info("--- LLM Verification Finished ---")
    return aggregated_result 