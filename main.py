from flask import Flask, request, Response, send_from_directory, send_file
import hashlib, string, random, json, mimetypes, time, psycopg2, math, os
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI

app = Flask(__name__)

CORS(app, origins={"http://localhost:5501"}) #MODIFY THIS IN PROD TO eduflash.org!!!!! 

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) #root
AI_DIR = os.path.join(BASE_DIR, "ai")

# .env is in /ai
load_dotenv(os.path.join(AI_DIR, ".env"))

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

with open(os.path.join(AI_DIR, "prompt.txt"), "r", encoding="utf-8") as f:
    prompt = f.read()

def trust_factor(likes, dislikes, reports, views,
                 report_weight = 1.5,  # reports are weighed differently, 1 report = 3 dislikes
                 decay_k = 0.2,        # exponential decay rate for reports
                 virt_view = 200,      # virtual views are given to new guides (ex: to not give 0% trust factor to a guide with 1 view and one dislike)
                 init_score = 0.75,    # initial trust factor is 50%
                 view_penalty= 0.05,   # fraction of non engaging views to dilute the score and make views matter
                 scale_factor= 1.1):   # scale factor because its a lil harsh
    
    """
    the following will be the equation to create trust factor rating
    it will return a value from 0 to 100 and will also check for triggers
    """

    # the weight of the reports decreases as the amount of reports increase
    effective_report_weight = report_weight * math.exp(-decay_k * max(0, reports - 1))

    #net score
    net_score = likes - dislikes - (effective_report_weight * reports)

    # account for the full engagement to be put into the engagement factor
    total_engagement = likes + dislikes + reports

    # reduces view penalty for guides with moderate engagement
    engagement_factor = 1 / (1 + total_engagement)  # more engagement -> less view dilution

    # Denominator
    denominator = virt_view + total_engagement + view_penalty * engagement_factor * max(0, views - total_engagement)

    # Bayesian trust scaling
    trust_score = (virt_view * init_score + net_score) / denominator

    # Apply scale factor
    trust_score *= scale_factor

    # Clamp 0–1, scale to 0–100
    trust_score = max(0.0, min(1.0, trust_score)) * 100

    return round(trust_score, 2)


# wrapper for trust_factor(), this returns a rating score
def scale(likes, dislikes, reports, views):
    score = trust_factor(likes, dislikes, reports, views)

    if score >= 90:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 50:
        return "Mixed"
    elif score >= 30:
        return "Poor"
    else:
        return "Very Poor"


@app.route('/')
def index():
    return send_file('index.html')

@app.route('/api/makeaccount', methods=['POST'])
def makeaccount():
    data = request.json
    if "username" not in data or "password" not in data or "email" not in data:
        return "invalid request", 400
    if "/" in data["username"]:
        return "username taken", 409

    with conn.cursor() as curs:
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = %s', (data["username"],))
        if len(cur.fetchall()) > 0:
            return "username taken", 409

        salt = ''.join(random.choices(string.ascii_letters, k=5))
        hashed = hashlib.md5((data["password"]+salt).encode()).hexdigest()

        cur.execute('INSERT INTO users (username, hash, salt, email) VALUES (%s, %s, %s, %s)', (data["username"],hashed,salt,data["email"]))
        rand = ''.join(random.choices(string.ascii_letters, k=32))
        cur.execute('SELECT * FROM sessions WHERE username = %s', (rand,))
        while len(cur.fetchall()) > 0:
            rand = ''.join(random.choices(string.ascii_letters, k=32))
            cur.execute('SELECT * FROM sessions WHERE username = %s', (rand,))
        cur.execute('INSERT INTO sessions (username, key, lasttime) VALUES (%s, %s, %s)', (data["username"],rand,time.time()))
        conn.commit()

        print(rand)
        return "{\"token\":\"" + rand + "\"}", 200

@app.route('/api/startsession', methods=['POST'])
def startsession():
    data = request.json
    if "username" not in data or "password" not in data:
        return "invalid request", 400

    with conn.cursor() as curs:
        cur = conn.cursor()
        cur.execute('SELECT (hash, salt) FROM users WHERE username = %s', (data["username"],))
        row = cur.fetchone()[0]
        if row == None:
            return "login failed", 401
        row = row[1:-1].split(",")

        hashed = hashlib.md5((data["password"]+row[1]).encode()).hexdigest()

        if not row[0] == hashed:
            return "login failed", 401
        rand = ''.join(random.choices(string.ascii_letters, k=32))
        cur.execute('SELECT * FROM sessions WHERE key = %s', (rand,))
        while len(cur.fetchall()) > 0:
            rand = ''.join(random.choices(string.ascii_letters, k=32))
            cur.execute('SELECT * FROM sessions WHERE username = %s', (rand,))
        cur.execute('INSERT INTO sessions (username, key, lasttime) VALUES (%s, %s, %s)', (data["username"],rand,time.time()))
        conn.commit()

        print(rand)
        return {"token": rand}, 200

@app.route('/api/search', methods=['POST'])
def getprofile():
    data = request.json

    with conn.cursor() as curs:
        if "topic" in data:
            cur.execute('SELECT (hash, owner, likes, dislikes, reports, views, topic, title) FROM pages WHERE topic LIKE %%s% LIMIT 50', (data["topic"],))
            return cur.fetchall(), 200
        if "title" in data:
            cur.execute('SELECT (hash, owner, likes, dislikes, reports, views, topic, title) FROM pages WHERE topic LIKE %%s% LIMIT 50', (data["title"],))
            return cur.fetchall(), 200
    return "invalid request", 400

@app.route('/api/profile', methods=['POST'])
def profile():
    data = request.json
    if "username" not in data:
        return "user not found", 400

    with conn.cursor() as curs:
        cur.execute('SELECT email FROM users WHERE username = %s', (data["username"],))
        email = cur.fetchone()[0]
        return {"email": email}, 200

@app.route('/api/makepage', methods=['POST'])
def makepage():
    data = request.json
    if "token" not in data or "title" not in data or "topic" not in data or "file" not in request.files:
        return "invalid request", 400
    file = request.files["file"]
    if file.filename == "":
        return "invalid request", 400

    with conn.cursor() as curs:
        cur.execute('SELECT username FROM sessions WHERE key = %s', (data["token"],))
        row = cur.fetchone()[0]
        if row == None:
            return "invalid token", 403
        hashed = hashlib.md5(file.read().encode()).hexdigest()
        file.save("pages/" + hashed)
        cur.execute('INSERT INTO pages (hash, owner, topic, title, likes, dislikes, reports, views) VALUES (%s, %s, %s, %s, 0, 0, 0, 0)', (hashed,row,data["topic"],data["title"]))
        conn.commit()
        return "Created", 201

# neils ai for manos create page
@app.route("/api/generate", methods=['POST'])
def generate():
    data = request.json
    if "token" not in data or "topic" not in data or "lang" not in data:
        return "invalid request", 400

    with conn.cursor() as curs:
        cur.execute('SELECT username FROM sessions WHERE key = %s', (data["token"],))
        row = cur.fetchone()[0]
        if row == None:
            return "invalid token", 403

    return client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": "You are a highly educated individual who will write educational guides for users based on their prompts."},
            {"role": "user", "content": f"{prompt}\nTopic: {data['topic']}\nLanguage: {data['lang']}"}
        ],
        temperature=1
    ).choices[0].message.content.strip(), 200

if __name__ == '__main__':
    conn = psycopg2.connect(dbname="eduflash", user="eduflash", host="127.0.0.1")
    app.run(host='0.0.0.0', port=8080)
