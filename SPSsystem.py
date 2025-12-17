from flask import Flask, request
app = Flask(__name__)
@app.route("/callback", methods=["POST"])
def callback():
    print(request.get_json(), flush=True)
    return "OK", 200