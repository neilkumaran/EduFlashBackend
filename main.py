from flask import Flask, request, Response, send_from_directory, send_file
import hashlib, string, random, json, mimetypes, time, psycopg2, math

app = Flask(__name__)

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

@app.route('/makeaccount', methods=['POST'])
def makeaccount():
    data = request.json
    if "username" not in data or "password" not in data or "email" not in data:
        return "invalid request", 400

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

@app.route('/startsession', methods=['POST'])
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
        cur.execute('SELECT * FROM sessions WHERE username = %s', (rand,))
        while len(cur.fetchall()) > 0:
            rand = ''.join(random.choices(string.ascii_letters, k=32))
            cur.execute('SELECT * FROM sessions WHERE username = %s', (rand,))
        cur.execute('INSERT INTO sessions (username, key, lasttime) VALUES (%s, %s, %s)', (data["username"],rand,time.time()))
        conn.commit()

        print(rand)
        return "{\"token\":\"" + rand + "\"}", 200


#@app.route('/profile', methods=['POST'])
#def profile():
#    data = request.json
#    if data["session"] not in sessions:
#        return "session not found"
#
#    return {
#        "username": sessions[data["session"]]["username"],
#        "email": users[sessions[data["session"]]["username"]]["email"],
#    }

if __name__ == '__main__':
    conn = psycopg2.connect(dbname="eduflash", user="eduflash", host="127.0.0.1")
    app.run(host='0.0.0.0', port=8080)
