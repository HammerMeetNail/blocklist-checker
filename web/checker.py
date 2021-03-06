from os import getenv
from hashlib import sha256

from boto3 import client
from flask import Flask, jsonify, request

dynamodb_client = client('dynamodb')
dynamodb_table = getenv("DYNAMODB_TABLE_NAME")

app = Flask(__name__)

# Needed to catch // 
app.url_map.merge_slashes = False

@app.route("/urlinfo/1/<path:host>", defaults={'path': '/'})
@app.route("/urlinfo/1/<path:host>/<path:path>")
def check_url(host, path):
    
    # determine true host and path using raw_uri
    if host.endswith("/"):
        host = host[:-1]
    host_offset = request.environ['RAW_URI'].find(host) + len(host)
    path = path if path == "/" else request.environ['RAW_URI'][host_offset:]

    # Query DynamoDB for a single record - domain, sha256 and path must match exactly
    sha = sha256(f"{host}{path}".encode()).hexdigest()

    blocked_url = dynamodb_client.query(
        TableName=dynamodb_table,
        Select="COUNT",
        Limit=1,
        KeyConditions={
            'domain': {
                'ComparisonOperator': 'EQ',
                'AttributeValueList': [{'S': host}]
            },
            'sha256': {
                'ComparisonOperator': 'EQ',
                'AttributeValueList': [{'S': sha}]
            }
        },
        QueryFilter={
            'path': {
                'ComparisonOperator': 'EQ',
                'AttributeValueList': [{'S': path}]
            }
        }
    )

    # If a record is returned, it is blocked.
    response = jsonify(blocked=False)
    if blocked_url["Count"] != 0:
        response = jsonify(blocked=True)
        response.status_code = 403
    return response


if __name__ == "__main__":  # pragma: no cover
    app.run(host='0.0.0.0')
