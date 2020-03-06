import pytest
import boto3
from urllib.parse import urlparse
from hashlib import sha256
from os import path
from moto import mock_dynamodb2

import sys
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from web.checker import app


app.testing = True

# Mock the boto3 client and create a blocklist table
def mock_aws():
    client = boto3.client('dynamodb')

    params = {
        'TableName': "blocklist",
        'KeySchema': [
            {'AttributeName': "domain", 'KeyType': "HASH"},    # Partition key
            {'AttributeName': "sha256", 'KeyType': "RANGE"}   # Sort key
        ],
        'AttributeDefinitions': [
            {'AttributeName': "domain", 'AttributeType': "S"},
            {'AttributeName': "sha256", 'AttributeType': "S"}
        ],
        'ProvisionedThroughput': {
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    }

    # Create the table
    client.create_table(**params)

    return client

# Generate a list of blocked urls for test client
def generate_blocklist():
    blocked_urls = []

    with open("test/feed.txt") as feed:
        for line in feed:
            url = urlparse(line)
            host = url.netloc
            query = url.query
            path = url.path

            if url.scheme == "http" and host.find(":") == -1:
                host = host.strip() + ":80"
            elif url.scheme == "https" and host.find(":") == -1:
                host = host.strip() + ":443"

            if len(path) == 0:
                path = "/"

            blocked_urls.append(("/urlinfo/1/",host, path.rstrip(), query.rstrip()))
            
    return blocked_urls

# Validate that urls added to DynamoDB return a 403 
blocked_urls = generate_blocklist()
@mock_dynamodb2
@pytest.mark.parametrize("prefix,host,path,query", blocked_urls)
def test_block(prefix, host, path,query):

    client = mock_aws()
    sha = sha256(f"{host}{path}".encode()).hexdigest()
    print(sha)

    client.put_item(
        TableName="blocklist",
        Item={
            'domain': {
                'S': host
            },
            'sha256': {
                'S': sha
            },
            'path': {
                'S': path
            }
        }
    )

    with app.test_client() as client:
        result = client.get(f"{prefix}{host}{path}", query_string=query)

        assert result.status_code == 403
        assert result.get_json() == {'blocked': True}

# Validate that urls not added to DynamoDB return a 200 
allowed_urls = [
    ("/urlinfo/1/", "automagic.com:443", "/"),
    ("/urlinfo/1/", "automagic.com:443", "/one"),
    ("/urlinfo/1/", "automagic.com:443", "/one/two/three/four")
]
@mock_dynamodb2
@pytest.mark.parametrize("prefix,host,path", allowed_urls)
def test_allow(prefix, host, path):

    client = mock_aws()

    with app.test_client() as client:
        result = client.get(f"{prefix}{host}{path}")

        assert result.status_code == 200
        assert result.get_json() == {'blocked': False}
