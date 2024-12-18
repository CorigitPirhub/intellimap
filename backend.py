from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app) 

@app.route('/api/get-data', methods=['GET'])
def get_data():
    # 处理GET请求
    return jsonify({"message": "This is a GET response"})

@app.route('/api/post-data', methods=['POST'])
def post_data():
    # 处理POST请求
    data = request.json
    return jsonify({"received_data": data, "message": "This is a POST response"})

def start_server():
    global app
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5001)
