from flask import Flask, jsonify
import os
 
app = Flask(__name__)
 
@app.route("/")
def home():
    return jsonify(message="Welcome from inside a Docker Container!")
 
@app.route("/health")
def health():
    return jsonify(status="ok"), 200
 
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
