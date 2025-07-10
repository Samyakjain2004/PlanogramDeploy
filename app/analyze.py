import base64
import os
import cv2
import tempfile
from openai import AzureOpenAI
import time
from app.utils.product_extractor import extract_product_name
from dotenv import load_dotenv
load_dotenv()

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")

# Initialize client
client = AzureOpenAI(
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
)

def encode_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def extract_products_from_image(image_path, user_question, frame_number=None, fps=None):
    try:
        base64_image = encode_image(image_path)

        timestamp_ms = None
        if frame_number is not None and fps:
            timestamp_ms = int((frame_number / fps) * 1000)
            location_context = f"\n🖼 Frame Number: {frame_number}\n⏱ Timestamp (ms): {timestamp_ms}"
        else:
            location_context = ""
            
        # Check if API credentials are properly loaded
        if not all([AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME, 
                   AZURE_OPENAI_API_VERSION, AZURE_OPENAI_API_KEY]):
            return "Error: Azure OpenAI API credentials are missing. Please check your .env file."

        prompt_text = f"""
You are a helpful assistant that analyzes retail shelf images taken from video frames. Each image is from a different time and angle in the store video. The user will ask a question about products on the shelf. Your job is to analyze **only this single image/frame**, and return a clear and factual answer.

🧠 General Instructions:
- Use only the visible contents of this frame to answer the user's question.
- Frame context: {location_context}
- Do not assume what's outside the frame or in other frames.
- Be concise, courteous, and specific to the query.
- If the requested product or detail is **not visible**, state that clearly.
- If the query refers to a **specific product**, then at the end of the summary add a new line in this format exactly:
  `product_name = <Product Name>`
- If no product is mentioned, skip this line.

Return ONLY the summary and the product name line if applicable.

User Query: {user_question}
"""

        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert retail shelf analyst that provides accurate, image-based product insights from shelf photos."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt_text
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2048,
            temperature=0.1,
            top_p=1.0,
            model=AZURE_OPENAI_DEPLOYMENT_NAME,
            timeout=30  # Add 30 second timeout to prevent hanging
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        error_type = str(type(e).__name__)
        error_message = str(e)
        
        # More specific error handling
        if "timeout" in error_message.lower():
            print(f"[⚠️ Skipping frame {frame_number} due to error: Request timed out.]")
            return f"[Skipped frame {frame_number} due to timeout. Try again later.]"
        elif any(net_err in error_message.lower() for net_err in ["connection", "network", "connect"]):
            print(f"[⚠️ Skipping frame {frame_number} due to error: Connection error.]")
            return f"[Skipped frame {frame_number} due to connection error. Check your internet connection.]"
        else:
            print(f"[⚠️ Skipping frame {frame_number} due to error: {error_type}: {error_message}]")
            return f"[Skipped frame {frame_number} due to error: {error_type}]"

def analyze_video_for_query(video_path, user_question, frame_interval=23):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    frame_responses = []
    product_timestamps = []
    frame_index = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_index % frame_interval == 0:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_image_file:
                temp_filename = temp_image_file.name
                cv2.imwrite(temp_filename, frame)

            timestamp_ms = int((frame_index / fps) * 1000)

            response = extract_products_from_image(
                image_path=temp_filename,
                user_question=user_question,
                frame_number=frame_index,
                fps=fps
            )

            frame_responses.append(f"🖼 Frame {frame_index} ({timestamp_ms} ms):\n{response}")

            # if "not visible" not in response.lower() and "not found" not in response.lower():
            #     product_timestamps.append(timestamp_ms)
            # === Heuristics to detect valid frames ===
            response_clean = response.lower()

            # Only include confident detections
            keywords_present = any(keyword in response_clean for keyword in
                                   ["located", "visible", "is on", "can be seen", "placed", "sitting", "present",
                                    "seen"])
            uncertain_phrases = any(phrase in response_clean for phrase in
                                    ["not visible", "not found", "unclear", "could be", "might be", "probably"])

            # Skip last few frames if likely false positive
            video_duration_ms = (total_frames / fps) * 1000
            end_threshold_ms = video_duration_ms * 0.9  # last 10%

            if keywords_present and not uncertain_phrases:
                if timestamp_ms < end_threshold_ms or "end" not in response_clean:
                    product_timestamps.append(timestamp_ms)

            os.remove(temp_filename)

        frame_index += 1

    cap.release()

    combined_text = "\n\n".join(frame_responses)

    summary_prompt = f"""
You are a summarization assistant. Based on the following frame-wise analysis of a shelf video, write a summary of where the requested product(s) appear.
- If the query refers to a **specific product**, then at the end of the summary add a new line in this format exactly:
  `product_name = <Product Name>`
- If no product is mentioned, skip this line.

Return ONLY the summary and the product name line if applicable.

📌 User Query: {user_question}

🔍 Frame Responses:
{combined_text}

✏️ Return a helpful, natural language summary for the user. Do not include any extra information (about frames and frame numbers) other than the answer to the asked query.
"""

    summary_response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a summarization expert for retail shelf video analytics."},
            {"role": "user", "content": summary_prompt}
        ],
        max_tokens=512,
        temperature=0.3,
        top_p=1.0,
        model=AZURE_OPENAI_DEPLOYMENT_NAME,
        timeout=30  # Add 30 second timeout to prevent hanging
    )

    base_summary = summary_response.choices[0].message.content.strip()

    # Final return: summary without timestamps, but timestamps available separately
    if not product_timestamps or "not visible" in base_summary.lower():
        product_timestamps = []
    if video_path.lower().endswith((".jpg", ".jpeg", ".png")):
        response = extract_products_from_image(image_path=video_path, user_question=user_question)
        evaluation_result = evaluate_summary_accuracy(user_question, base_summary, combined_text)
        print("\n--- Evaluation Summary ---")
        print(evaluation_result)
        product_name = extract_product_name(base_summary)
        if not product_name or product_name.lower() == "unknown":
            product_name = extract_product_name(user_question)
        print(f"[🛍️ Extracted Product Name]: {product_name}")
        return {
            "final_summary": base_summary,
            "timestamps": product_timestamps,
            "product_name": product_name
        }
    evaluation_result = evaluate_summary_accuracy(user_question, base_summary, combined_text)
    print("\n--- Evaluation Summary ---")
    print(evaluation_result)
    product_name = extract_product_name(base_summary)
    if not product_name or product_name.lower() == "unknown":
        product_name = extract_product_name(user_question)
    print(f"[🛍️ Extracted Product Name]: {product_name}")
    return {
        "final_summary": base_summary,
        "timestamps": product_timestamps,
        "product_name": product_name
    }

def evaluate_summary_accuracy(user_question, generated_summary, frame_analysis_text):
    evaluation_prompt = f"""
You are an evaluation assistant. Your job is to evaluate the quality of the generated summary based on the provided supporting frame analysis.

🧠 Guidelines:
- The frame responses may each contain partial or new information.
- The final summary is expected to combine this information holistically.
- Do NOT compare each line of the summary with each frame.
- Instead, check if the facts stated in the summary are **generally supported** by at least one of the frames.
- The summary should not contradict the evidence.
- Do NOT penalize the summary for not including every frame.
- Only judge whether the included information is accurate and relevant to the user's question.

🧪 Additional Rule:
- If the summary is **not 100% accurate**, list exactly what information is **incorrect**, **unsupported**, or **missing** based on the frame responses.

📌 User Question:
{user_question}

📄 Generated Summary:
{generated_summary}

📷 Supporting Frame Responses:
{frame_analysis_text}

🎯 Please return your evaluation in the following format:

Accuracy Score (0–100)%: <score>
Evaluation Summary: <brief explanation of factual correctness and completeness>
"""

    eval_response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are an unbiased evaluator that assesses summary quality based on provided evidence."},
            {"role": "user", "content": evaluation_prompt}
        ],
        max_tokens=300,
        temperature=0.2,
        model=AZURE_OPENAI_DEPLOYMENT_NAME  # Or use "gpt-4o" if preferred
    )

    return eval_response.choices[0].message.content.strip()
