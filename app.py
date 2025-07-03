from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from datetime import datetime
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Connect to local MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["webhook_db"]
collection = db["events"]

#routing to ui
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/events', methods=['GET'])
def get_events():
    events = list(collection.find().sort("timestamp", -1))
    for e in events:
        e['_id'] = str(e['_id'])
    return jsonify(events)

@app.route('/webhook', methods=['POST'])
def github_webhook():
    data = request.json
    event_type = request.headers.get('X-GitHub-Event')

    # push
    if event_type == 'push':
        record = {
            "type": "push",
            "author": data['pusher']['name'],
            "from_branch": None,
            "to_branch": data['ref'].split('/')[-1],
            "timestamp": datetime.utcnow()
        }

    #pull 
    elif event_type == 'pull_request':
        record = {
            "type": "pull_request",
            "author": data['pull_request']['user']['login'],
            "from_branch": data['pull_request']['head']['ref'],
            "to_branch": data['pull_request']['base']['ref'],
            "timestamp": datetime.utcnow()
        }
    #merge
    elif event_type == 'pull_request' and data['action'] == 'closed' and data['pull_request']['merged']:
        record = {
            "type": "merge",
            "author": data['pull_request']['user']['login'],
            "from_branch": data['pull_request']['head']['ref'],
            "to_branch": data['pull_request']['base']['ref'],
            "timestamp": datetime.utcnow()
    }

    else:
        return jsonify({"message": "Unsupported event type"}), 400

    # Store event
    collection.insert_one(record)
    return jsonify({"message": "Event stored successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
