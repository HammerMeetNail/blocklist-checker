import os

import boto3
from flask import Flask, jsonify


client = boto3.client('dynamodb')

app  = Flask(__name__)

@app.route("/urlinfo/1/<path:host>", defaults={'path': '/'})
@app.route("/urlinfo/1/<path:host>/<path:path>")
def check_url(host, path):
    blocked_url = client.query(
        TableName="blocklist",
        Select="COUNT",
        KeyConditions = {
            'domain':{
                'ComparisonOperator':'EQ',
                'AttributeValueList': [{'S': host}]
            },
            'path':{
                'ComparisonOperator':'EQ',
                'AttributeValueList': [{'S': f"/{path}"}]
            }
        }
    )

    response = jsonify(blocked=False)
    if blocked_url["Count"] != 0:
        response = jsonify(blocked=True)
        response.status_code = 403
    return response

if __name__ == "__main__":
    app.run(host='0.0.0.0')