from os import getenv

from boto3 import client
from flask import Flask, jsonify


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

    # Query DynamoDB for a single record - domain and path must match exactly
    print(dynamodb_table)
    blocked_url = dynamodb_client.query(
        TableName=dynamodb_table,
        Select="COUNT",
        Limit=1,
        KeyConditions={
            'domain': {
                'ComparisonOperator': 'EQ',
                'AttributeValueList': [{'S': host}]
            },
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
