# scripts/llm_cross_validation.py

import os
import pandas as pd
import numpy as np
from pathlib import Path
import logging
import time
import argparse
import json
from PIL import Image
import base64
from io import BytesIO
import asyncio # Added for asynchronous operations

# --- Use AsyncOpenAI library to interact with OpenRouter ---
try:
    from openai import AsyncOpenAI # Use the async client
except ImportError:
    logging.error("OpenAI library not installed. Please install it: pip install openai")
    AsyncOpenAI = None

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'
OUTPUT_DIR = BASE_DIR / 'llm_evaluation_results'
OUTPUT_DIR.mkdir(exist_ok=True)

# --- OpenRouter API Configuration ---
DEFAULT_OPENROUTER_API_KEY = "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"
YOUR_SITE_URL = os.environ.get("YOUR_SITE_URL", "http://localhost")
YOUR_SITE_NAME = os.environ.get("YOUR_SITE_NAME", "MM-DFD-Validation")

# --- Models to Use via OpenRouter ---
# Define models used for text verification
OR_TEXT_MODELS = [
    "perplexity/sonar-reasoning-pro",
    "perplexity/sonar",
    "google/gemini-2.0-flash-001", # Also supports vision
    "deepseek/deepseek-r1",
    "deepseek/deepseek-chat-v3-0324",
]
# Define models used for image verification
OR_IMAGE_MODELS = [
    "google/gemini-2.0-flash-001",
]

# --- Model Weighting (Perplexity highest, then web/strong reasoning, then others) ---
MODEL_WEIGHTS = {
    "perplexity/sonar-reasoning-pro": 0.4, # Higher weight
    "perplexity/sonar": 0.2,              # Higher weight
    "google/gemini-2.0-flash-001": 0.15, # Good reasoning + vision + potential web
    "deepseek/deepseek-r1": 0.15,              # Strong reasoning
    "deepseek/deepseek-chat-v3-0324": 0.1,     # Base chat
    # Ensure sum is close to 1.0 (0.25+0.25+0.20+0.15+0.15 = 1.0)
    # Note: Weights are primarily for text verification aggregation.
}

# Rate limiting delay
DEFAULT_API_DELAY = 1.5 # Slightly adjusted delay for async calls

# --- Helper Functions ---
def load_image_as_base64(image_path):
    """Loads an image file and returns its base64 encoded string."""
    # (Implementation remains the same as previous version)
    if not image_path:
        logging.warning("No image path provided to load_image_as_base64.")
        return None
    abs_path = Path(image_path)
    if not abs_path.exists():
        abs_path = DATA_DIR / image_path
        if not abs_path.exists():
            logging.error(f"Image file not found: {image_path}")
            return None
    try:
        logging.info(f"Loading image from: {abs_path}")
        with Image.open(abs_path) as img:
            output_format = "JPEG" if img.format != "PNG" else "PNG"
            buffered = BytesIO()
            if output_format == "JPEG" and img.mode == 'RGBA': img = img.convert('RGB')
            img.save(buffered, format=output_format)
            img_byte = buffered.getvalue()
            return base64.b64encode(img_byte).decode('utf-8')
    except Exception as e:
        logging.warning(f"Could not load or encode image {abs_path}: {e}")
        return None

def format_structured_llm_response(model_name, success, data=None, error=None):
    """Standardizes the response format, expecting specific keys.
       Ensures 'success' key is always present.
    """
    # Initialize with base structure and correct success status
    base_response = {
        "model": model_name,
        "success": success, # Ensure success is always set
        "verdict": "Error" if not success else "Parsing Error", # Default verdict based on success
        "confidence": 0.0,
        "reason": None,
        "error": str(error) if error else (None if success else "Unknown error during processing"),
        "raw_response": None
    }

    if success and isinstance(data, dict):
        # Attempt to extract keys, providing defaults if missing
        base_response.update({
            "verdict": data.get("verdict", "Parsing Error"),
            "confidence": data.get("confidence", 0.0),
            "reason": data.get("reason", "No reason provided or parsing failed."),
            "error": None # Clear error if successfully parsed dict
        })
        # Basic validation for confidence
        try:
             confidence_val = float(base_response["confidence"])
             if not (0.0 <= confidence_val <= 1.0):
                  logging.warning(f"Model {model_name} returned confidence out of range: {confidence_val}. Clamping to 0.0-1.0.")
                  base_response["confidence"] = max(0.0, min(1.0, confidence_val))
             else:
                  base_response["confidence"] = confidence_val # Ensure it's float
        except (ValueError, TypeError):
             logging.warning(f"Model {model_name} returned non-numeric confidence: {base_response['confidence']}. Setting to 0.0.")
             base_response["confidence"] = 0.0

    elif not success and isinstance(data, str): # Handle case where parsing failed but raw text exists
        base_response["raw_response"] = data
        # Ensure error message reflects parsing failure
        base_response["error"] = f"Failed to parse LLM response as JSON. {base_response['error'] if base_response['error'] else ''}".strip()

    # For other cases (e.g., success=False, data is not dict or str), the initial base_response is used.

    return base_response


# --- Unified ASYNC OpenRouter API Call Function ---
async def call_openrouter_api_async(prompt, model_name, image_base64=None, api_key=DEFAULT_OPENROUTER_API_KEY):
    """ASYNC calls the specified model via the OpenRouter API using the OpenAI library format."""
    if not AsyncOpenAI: return format_structured_llm_response(model_name, False, error="AsyncOpenAI client not available.")
    if not api_key: return format_structured_llm_response(model_name, False, error="OpenRouter API key not configured.")

    client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
    messages = [{"role": "user", "content": []}]
    messages[0]["content"].append({"type": "text", "text": prompt})

    if image_base64:
        is_vision_model = model_name in OR_IMAGE_MODELS
        if is_vision_model:
            mime = "image/jpeg" if image_base64.startswith("/9j/") else "image/png"
            image_url = f"data:{mime};base64,{image_base64}"
            messages[0]["content"].append({"type": "image_url", "image_url": {"url": image_url}})
            logging.info(f"Preparing image for vision model: {model_name}")
        else:
            logging.warning(f"Image provided, but model {model_name} not in vision list. Sending text only.")

    try:
        logging.debug(f"Calling OpenRouter model: {model_name}")
        completion = await client.chat.completions.create(
            extra_headers={"HTTP-Referer": YOUR_SITE_URL, "X-Title": YOUR_SITE_NAME},
            model=model_name,
            messages=messages,
            max_tokens=700,
            temperature=0.3, # Lower temperature for more factual responses
            # response_format={"type": "json_object"}, # Request JSON output if supported by model/OpenRouter
        )
        raw_content = completion.choices[0].message.content
        logging.debug(f"Raw response from {model_name}: {raw_content}")

        # Attempt to parse the response as JSON
        try:
            # Clean potential markdown code blocks
            if raw_content.strip().startswith("```json"):
                 raw_content = raw_content.strip()[7:-3].strip()
            elif raw_content.strip().startswith("```"):
                 raw_content = raw_content.strip()[3:-3].strip()

            parsed_data = json.loads(raw_content)
            if not isinstance(parsed_data, dict):
                 raise ValueError("Response is not a JSON object.")
            # Basic check for expected keys (optional but good practice)
            # if not all(k in parsed_data for k in ["verdict", "confidence", "reason"]):
            #     raise ValueError("JSON missing required keys: verdict, confidence, reason")

            return format_structured_llm_response(model_name, True, data=parsed_data)

        except json.JSONDecodeError as json_err:
            logging.warning(f"Failed to parse JSON from {model_name}: {json_err}. Raw response: {raw_content}")
            return format_structured_llm_response(model_name, False, error=f"JSONDecodeError: {json_err}", data=raw_content)
        except ValueError as val_err:
             logging.warning(f"Parsed JSON structure invalid from {model_name}: {val_err}. Raw response: {raw_content}")
             return format_structured_llm_response(model_name, False, error=f"Invalid JSON Structure: {val_err}", data=raw_content)


    except Exception as e:
        logging.error(f"OpenRouter API call failed for model {model_name}: {e}")
        error_detail = str(e)
        if hasattr(e, 'response') and hasattr(e.response, 'text'): error_detail += f" | Response: {e.response.text}"
        return format_structured_llm_response(model_name, False, error=error_detail)


# --- Core ASYNC Verification Function for Single Input ---

async def verify_single_news_async(text_input, image_path_input=None, api_key=DEFAULT_OPENROUTER_API_KEY, api_delay=DEFAULT_API_DELAY):
    """
    ASYNC verifies a single news item using multiple LLMs via OpenRouter and aggregates results.
    """
    logging.info("--- Starting Single Item Verification (Async) ---")
    if not text_input and not image_path_input:
        logging.error("Both text_input and image_path_input are empty.")
        return {"error": "No text or image provided."}

    # --- Prepare Image Data ---
    img_b64 = None
    if image_path_input:
        img_b64 = load_image_as_base64(image_path_input)
        if not img_b64:
            logging.warning(f"Failed to load image {image_path_input}, proceeding without it.")

    # --- Prepare API Call Tasks ---
    tasks = []

    # Text Verification Tasks
    if text_input:
        # Updated prompt asking for JSON
        text_prompt = f"""请对以下新闻内容进行事实核查。请严格按照以下 JSON 格式返回你的分析结果，不要添加任何额外的解释性文字或markdown标记：
{{
  "verdict": "判断结果",
  "confidence": 置信度分数,
  "reason": "理由/证据摘要"
}}
其中，"判断结果"必须是"真实"、"虚假"、"无法核实"或"混合信息"之一。"置信度分数"是一个 0.0 到 1.0 之间的小数，表示你对判断结果的确信程度。"理由/证据摘要"请提供简洁客观的分析依据或来源。

新闻内容：
\"{text_input}\"
"""
        for model_id in OR_TEXT_MODELS:
            tasks.append(asyncio.create_task(call_openrouter_api_async(text_prompt, model_id, api_key=api_key)))
            # Add small delay *between creating tasks* if hitting creation limits,
            # but the main delay is handled by asyncio.gather implicitly or explicit sleeps if needed.
            await asyncio.sleep(0.05) # Small delay between task creations


    # Image Verification Tasks
    if img_b64:
        # Updated prompts asking for JSON
        if text_input:
            image_prompt = f"""请分析提供的图片，并结合以下新闻文本进行判断。请严格按照以下 JSON 格式返回你的分析结果：
{{
  "verdict": "综合判断结果",
  "confidence": 置信度分数,
  "reason": "图片与文本关联性分析及判断理由"
}}
其中，"综合判断结果"是对结合图片和文本后新闻整体真实性的判断（真实/虚假/无法核实/混合信息）。"置信度分数"是你对此判断的确信程度（0.0-1.0）。"理由"需说明图片内容、与文本关联、是否佐证或矛盾。

新闻文本：
\"{text_input}\"
"""
        else:
            image_prompt = f"""请分析提供的图片，判断它所描绘的场景或事件的真实性。请严格按照以下 JSON 格式返回你的分析结果：
{{
  "verdict": "图片真实性判断",
  "confidence": 置信度分数,
  "reason": "图片分析理由（例如：是否像真实照片、AI生成、拼接、摆拍等）"
}}
其中，"图片真实性判断"是"真实"、"疑似伪造"、"无法判断"之一。"置信度分数"是你对此判断的确信程度（0.0-1.0）。

"""
        for model_id in OR_IMAGE_MODELS:
             # Ensure image is only sent to designated vision models
            tasks.append(asyncio.create_task(call_openrouter_api_async(image_prompt, model_id, image_base64=img_b64, api_key=api_key)))
            await asyncio.sleep(0.05) # Small delay between task creations

    # --- Execute Tasks Concurrently ---
    logging.info(f"Sending {len(tasks)} API requests concurrently...")
    individual_results = await asyncio.gather(*tasks)
    logging.info("All API responses received.")

    # Separate text and image results (assuming model names are unique identifiers)
    text_results_raw = [res for res in individual_results if res['model'] in OR_TEXT_MODELS]
    image_results_raw = [res for res in individual_results if res['model'] in OR_IMAGE_MODELS]

    # --- Aggregation Logic (Focus on Text Results for Overall Verdict/Confidence) ---
    final_verdict = "Inconclusive"
    final_confidence = 0.5 # Default neutral
    needs_review = False
    valid_confidences = []

    # Filter successful text results with valid confidence for aggregation
    valid_text_results = [r for r in text_results_raw if r['success'] and isinstance(r.get('confidence'), (int, float))]

    if valid_text_results:
        total_weight = 0
        weighted_sum = 0
        for result in valid_text_results:
            model = result['model']
            weight = MODEL_WEIGHTS.get(model, 0) # Get weight, default 0 if model not in weights dict
            if weight > 0:
                 # Map verdict to a numeric score for weighted average (e.g., Fake=1.0, True=0.0, Uncertain/Mixed=0.5)
                 verdict_score = 0.5 # Default for Uncertain/Mixed/Error in verdict string
                 verdict_str = result.get('verdict', '').lower()
                 if '虚假' in verdict_str or 'fake' in verdict_str:
                      verdict_score = 1.0
                 elif '真实' in verdict_str or 'true' in verdict_str:
                      verdict_score = 0.0
                 # Use the model's self-reported confidence, weighted by our assigned model weight
                 # We are averaging the "propensity towards fake" based on verdict and confidence
                 score_to_average = verdict_score * result['confidence'] + (1-verdict_score)*(1-result['confidence']) # Weighted lean towards Fake

                 # Let's try a simpler average of confidence scores directly,
                 # and determine verdict later based on the average and individual verdicts?
                 # Simpler approach: Weighted average of the confidence score itself.
                 weighted_sum += weight * result['confidence']
                 total_weight += weight
                 valid_confidences.append(result['confidence']) # For std dev calculation

        if total_weight > 0:
            # Calculate final weighted confidence
            final_confidence = weighted_sum / total_weight

            # Calculate standard deviation for divergence check
            if len(valid_confidences) > 1:
                confidence_std_dev = np.std(valid_confidences)
                if confidence_std_dev > 0.25: # Threshold for triggering review
                    needs_review = True
                    logging.warning(f"High divergence detected in model confidences (std dev: {confidence_std_dev:.3f}). Flagging for review.")
            else:
                 confidence_std_dev = 0.0 # Cannot calculate std dev for one value

            # Determine final verdict based on aggregated confidence thresholds
            # Count how many models lean towards Fake vs True
            fake_leaning_votes = sum(1 for r in valid_text_results if '虚假' in r.get('verdict','').lower())
            true_leaning_votes = sum(1 for r in valid_text_results if '真实' in r.get('verdict','').lower())
            uncertain_votes = len(valid_text_results) - fake_leaning_votes - true_leaning_votes

            # Decision logic based on thresholds and vote counts (can be refined)
            if final_confidence >= 0.70 and fake_leaning_votes > true_leaning_votes:
                 final_verdict = "Likely Fake"
            elif final_confidence <= 0.30 and true_leaning_votes > fake_leaning_votes:
                 final_verdict = "Likely True"
            elif abs(fake_leaning_votes - true_leaning_votes) <= 1 and uncertain_votes >= 1: # Close call or uncertain models present
                 final_verdict = "Uncertain / Mixed Signals"
                 needs_review = True # Flag close calls for review
            else: # Default to uncertain if logic doesn't clearly fit
                 final_verdict = "Uncertain"


        else:
            logging.warning("No valid text results with weights found for aggregation.")
            final_verdict = "Aggregation Error"


    # --- Prepare Final Output ---
    aggregated_result = {
        "overall_verdict": final_verdict,
        "aggregated_confidence": round(final_confidence, 3),
        "needs_manual_review": needs_review,
        "original_text": text_input,
        "original_image_path": image_path_input,
        "text_verifications": text_results_raw,
        "image_verifications": image_results_raw,
    }

    logging.info("--- Single Item Verification Finished ---")
    return aggregated_result


# --- Argument Parser and Main Execution (Example Usage) ---
def parse_args():
    parser = argparse.ArgumentParser(description="Verify a single news item using LLM APIs via OpenRouter with Ensemble Logic.")
    parser.add_argument('--text', type=str, default="", help="Text content of the news item.")
    parser.add_argument('--image_path', type=str, default=None, help="Path to the image file (optional).")
    parser.add_argument('--output_file', type=str, default=None,
                        help="Path to save the single result JSON (optional).")
    parser.add_argument('--api_key', type=str, default=DEFAULT_OPENROUTER_API_KEY, help="OpenRouter API Key.")
    parser.add_argument('--delay', type=float, default=DEFAULT_API_DELAY, help="Base delay between API calls.")

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    script_start_time = time.time()

    if not AsyncOpenAI:
        logging.error("AsyncOpenAI client not available. Please install 'openai'.")
        exit(1)
    if not args.text and not args.image_path:
        logging.error("Error: Provide --text and/or --image_path.")
        exit(1)

    # Run the async verification function
    verification_result = asyncio.run(verify_single_news_async(
        text_input=args.text,
        image_path_input=args.image_path,
        api_key=args.api_key,
        api_delay=args.delay
    ))

    # Print the result to console
    print("\n--- Aggregated Verification Results ---")
    print(json.dumps(verification_result, indent=2, ensure_ascii=False))
    print("------------------------------------")

    # Optionally save the result to a file
    if args.output_file:
        try:
            output_path = Path(args.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(verification_result, f, indent=2, ensure_ascii=False)
            logging.info(f"Aggregated result saved to {output_path}")
        except Exception as e:
            logging.error(f"Failed to save result to {args.output_file}: {e}")

    script_duration = time.time() - script_start_time
    logging.info(f"Total script duration: {script_duration / 60:.2f} minutes")