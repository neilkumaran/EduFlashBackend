from flask import Flask, request, Response, send_from_directory, send_file
import hashlib, string, random, json, mimetypes, time

app = Flask(__name__)

sessions = {}
users = {}


@app.route('/')
def index():
    return send_file('index.html')

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('statis', path)

@app.route('/makeaccount', methods=['POST'])
def makeaccount():
    data = request.json
    if data["username"] in users.keys():
        return "taken"
    salt = ''.join(random.choices(string.ascii_letters, k=5))
    hashed = hashlib.md5((data["password"]+salt).encode()).hexdigest()
    users[data["username"]] = { "email": data["email"], "hash": hashed, "salt": salt }
    with open("users.json", "w") as file:
        file.write(json.dumps(users))
    rand = ''.join(random.choices(string.ascii_letters, k=32))
    while rand in sessions.keys():
        rand = ''.join(random.choices(string.ascii_letters, k=32))
    sessions[rand] = { "username": data["username"], "lastactive": time.time(), "chatbot": None }
    print(sessions)
    return rand

#@app.route('/startsession', methods=['POST'])
#def startsession():
#    data = request.json
#    if data["username"] not in users.keys():
#        return "badpass"
#    hashed = hashlib.md5((data["password"]+users[data["username"]]["salt"]).encode()).hexdigest()
#    if hashed != users[data["username"]]["hash"]:
#        return "badpass"
#    rand = ''.join(random.choices(string.ascii_letters, k=32))
#    while rand in sessions.keys():
#        rand = ''.join(random.choices(string.ascii_letters, k=32))
#    sessions[rand] = { "username": data["username"], "lastactive": time.time(), "chatbot": None }
#    return rand

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
    app.run(host='0.0.0.0', port=8080)
