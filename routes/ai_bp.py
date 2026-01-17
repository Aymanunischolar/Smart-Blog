from flask import Blueprint, request, jsonify
import google.generativeai as genai # Genai model imported here
import os, json
import re
from config import Config



"""
-----------------------Over here in this file all ai cleaning and text formatting for it response
will be done along with profanity and sensitive content check.

"""

ai_bp = Blueprint('ai', __name__)#Blueprint registered here to be registered in app.py

# Gemini model configured
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel(Config.GEMINI_MODEL)

# routes/ai_bp.py
def clean_markdown_logic(text):
    """
    Removes Markdown symbols (*, **, ##).
     Removes hashtags from the end of the text.
    """
    if not text: return ""

    #Removes Markdown bold/italic/headers
    text = re.sub(r'\*\*|__|\*|_|`', '', text)
    text = re.sub(r'^\s*#+\s+', '', text, flags=re.MULTILINE)

    # Removes hashtags from the END of the content
    text = re.sub(r'(\s*#\w+)+\s*$', '', text)

    return text.strip()


def clean_text(text, is_hashtag=False):
    """
    Sanitizes input but ALLOWS basic HTML formatting (bold, italic, lists).
    """
    if not text: return ""

    # 1. ALLOWED TAGS LIST (Security)
    # We replace strict tag removal with specific removal of scripts
    if not is_hashtag:
        #Remove dangerous tags: script, style, iframe, object, embed, etc.
        #Simple regex to remove <script>...</script> blocks entirely
        text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style.*?>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)

        #Removes event handlers (e.g. onclick="...")
        text = re.sub(r' on\w+="[^"]*"', '', text, flags=re.IGNORECASE)
        text = re.sub(r' javascript:[^"]*', '', text, flags=re.IGNORECASE)
    else:
        # Strict cleaning for hashtags remains
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'[^\w\s#]', '', text)
        return " ".join(text.split()).strip()

    return text.strip()




@ai_bp.route('/generate', methods=['POST'])
def generate_post():
    topic = request.json.get('topic')
    if not topic:
        return jsonify({"error": "No topic provided"}), 400

    try:
        # Categories initialized for the prompt matching the dropdown
        valid_categories = "['Tech', 'Social', 'Education', 'Jobs', 'Health', 'Finance', 'Travel']"

        #Prompting done here to make sure ai does what we want
        prompt = (
            f"Act as a professional blogger. Write about: '{topic}' (approx 100 words). "
            f"Classify the topic into exactly ONE of these categories: {valid_categories}. "
            f"Return ONLY a JSON object with keys: title, content, hashtags, category. "
            f"RULES: \n"
            f"1. 'hashtags' must be a LIST of strings, e.g. [\"#Tag1\", \"#Tag2\"]. \n"
            f"2. 'category' must be exactly one string from the provided list. \n"
            f"3. 'content' must NOT contain hashtags. \n"
            f"4. Do not use markdown formatting."
        )

        response = model.generate_content(prompt)
        text_response = response.text

        # --- JSON Extraction ---
        start_idx = text_response.find('{')
        end_idx = text_response.rfind('}') + 1

        if start_idx == -1 or end_idx == 0:
            raise ValueError("AI did not return valid JSON")

        json_str = text_response[start_idx:end_idx]
        data = json.loads(json_str)

        # --- Data will be Cleaned in formatted structure ---

        #Format Hashtags (List -> String with spaces)
        tags = data.get('hashtags', [])
        if isinstance(tags, list):
            data['hashtags'] = " ".join(tags)
        elif isinstance(tags, str):
            data['hashtags'] = re.sub(r'(?<!\s)#', ' #', tags).strip()

        # Clean Content
        if 'title' in data:
            data['title'] = clean_markdown_logic(data['title'])
        if 'content' in data:
            data['content'] = clean_markdown_logic(data['content'])

        # Ensure Category is valid (Fallback to 'Social' if AI fails)
        valid_list = ['Tech', 'Social', 'Education', 'Jobs', 'Health', 'Finance', 'Travel']
        if data.get('category') not in valid_list:
            data['category'] = 'Social'

        return jsonify(data)

    except Exception as e:
        print(f"Gemini Error: {e}")
        return jsonify({"error": "AI could not generate content."}), 500


@ai_bp.route('/check', methods=['POST'])
def check_content():
    """Context-aware safety scan using AI. Every function before being posted will
    call this endpoint for validation"""
    data = request.json
    full_text = f"{data.get('content', '')} {data.get('hashtags', '')}"

    try:
        prompt = f"Is this content safe for all ages? Reply ONLY SAFE or UNSAFE.\nText: {full_text}"
        response = model.generate_content(prompt)
        is_unsafe = "UNSAFE" in response.text.upper()
        return jsonify({"status": "UNSAFE" if is_unsafe else "SAFE"})
    except Exception:
        return jsonify({"status": "SAFE"})