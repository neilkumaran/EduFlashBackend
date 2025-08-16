from flask import Flask, render_template_string, request
import os
from dotenv import load_dotenv
from openai import OpenAI
from flask_cors import CORS
from flask import jsonify

app = Flask(__name__)
CORS(app, origins=["http://172.18.80.1:5500"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # /ai/flask
PARENT_DIR = os.path.dirname(BASE_DIR)  # /ai

# .env from /ai
load_dotenv(os.path.join(PARENT_DIR, ".env"))

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# prompt.txt from /ai
with open(os.path.join(PARENT_DIR, "prompt.txt"), "r", encoding="utf-8") as f:
    prompt = f.read()

@app.before_request
def log_request_info():
    print(f"[REQUEST] {request.method} {request.path}", flush=True)


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json() or {}
    topic = data.get("topic", "")
    lang = data.get("lang", "")
    print(f"[AI INPUT] topic={topic!r}, lang={lang!r}", flush=True)
    
    flask_output = gen_guide(topic, lang)

    return jsonify({
        "flaskoutput": flask_output
    })

def gen_guide(topic, lang):
    given_prompt = f"{prompt}\nTopic: {topic}\nLanguage: {lang}"
    print("Generating.....")
    output = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": "You are a highly educated individual who will write educational guides for users based on their prompts."},
            {"role": "user", "content": given_prompt}
        ],
        temperature=1
    ).choices[0].message.content.strip()

    return output


if __name__ == "__main__":
    app.run(debug=True)
