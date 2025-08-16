from flask import Flask, render_template_string, request
import os
from dotenv import load_dotenv
from openai import OpenAI

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # /ai/flask
PARENT_DIR = os.path.dirname(BASE_DIR)  # /ai

# .env from /ai
load_dotenv(os.path.join(PARENT_DIR, ".env"))

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# prompt.txt from /ai
with open(os.path.join(PARENT_DIR, "prompt.txt"), "r", encoding="utf-8") as f:
    prompt = f.read()

def gen_guide(topic, lang):
    given_prompt = f"{prompt}\nTopic: {topic}\nLanguage: {lang}"
    output = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": "You are a highly educated individual who will write educational guides for users based on their prompts."},
            {"role": "user", "content": given_prompt}
        ],
        temperature=1
    ).choices[0].message.content.strip()

    return output

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Guide Generator</title>
    <script>
        function showGenerating() {
            document.getElementById("output").innerHTML = "<em>Generating...</em>";
        }
    </script>
</head>
<body>
    <h1>Guide Generator</h1>
    <h1>anything submitted in the text boxes are saved to the vars topic and lang (respectively)</h1>
    <form method="POST" onsubmit="showGenerating()">
        <label>Topic:</label><br>
        <input type="text" name="topic" value="{{ topic }}"><br><br>
        <label>Language:</label><br>
        <input type="text" name="lang" value="{{ lang }}"><br><br>
        <input type="submit" value="Generate">
    </form>
    <div id="output">
    {% if output %}
        <hr>
        <h2>Output:</h2>
        <pre>{{ output }}</pre>
    {% endif %}
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    topic = ""
    lang = ""
    output = ""

    if request.method == "POST":
        topic = request.form.get("topic", "")
        lang = request.form.get("lang", "")
        output = gen_guide(topic, lang)

    return render_template_string(HTML_PAGE, topic=topic, lang=lang, output=output)

if __name__ == "__main__":
    app.run(debug=True)
