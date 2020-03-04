from os import getenv
from hashlib import sha256
# from urllib.parse import unquote

from boto3 import client
from flask import Flask, jsonify, request


dynamodb_client = client('dynamodb')
dynamodb_table = getenv("DYNAMODB_TABLE_NAME")

app = Flask(__name__)


@app.route("/urlinfo/1/<path:host>", defaults={'path': '/'})
@app.route("/urlinfo/1/<path:host>/<path:path>")
def check_url(host, path):
    # Sanitize host and path. "/" should never be at the end of host, always be at the start of path
    if host.endswith("/"):
        host = host[:-1]
    if not path.startswith("/"):
        path = f"/{path}"
    path = request.full_path[request.full_path.find(host) + len(host):]
    if path.endswith("?"):
        path = path[:-1]

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
