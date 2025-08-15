from flask import Flask, request, Response, send_from_directory, send_file
import hashlib, string, random, json, mimetypes, time, psycopg2

app = Flask(__name__)


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
