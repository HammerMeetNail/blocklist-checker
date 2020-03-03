import pytest
from os import path
import boto3
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
            {'AttributeName': "path", 'KeyType': "RANGE"}   # Sort key
        ],
        'AttributeDefinitions': [
            {'AttributeName': "domain", 'AttributeType': "S"},
            {'AttributeName': "path", 'AttributeType': "S"}
        ],
        'ProvisionedThroughput': {
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    }

    # Create the table
    client.create_table(**params)

    return client

# Validate that urls added to DynamoDB return a 403 
blocked_urls = [
    ("/urlinfo/1/", "example.com:80", "/"),
    ("/urlinfo/1/", "example.com:80", "/one"),
    ("/urlinfo/1/", "example.com:80", "/one/two/three/four")
]


@mock_dynamodb2
@pytest.mark.parametrize("prefix,host,path", blocked_urls)
def test_block(prefix, host, path):

    client = mock_aws()

    client.put_item(
        TableName="blocklist",
        Item={
            'domain': {
                'S': host
            },
            'path': {
                'S': path
            }
        }
    )

    with app.test_client() as client:
        result = client.get(f"{prefix}{host}{path}")

        assert result.status_code == 403
        assert result.get_json() == {'blocked': True}

# Validate that urls not added to DynamoDB return a 200 
allowed_urls = [
    ("/urlinfo/1/", "automagic.com:443", "/"),
    ("/urlinfo/1/", "automagic.com:443", "/one"),
    ("/urlinfo/1/", "automagic.com:443", "/one/two/three/four")
]


@mock_dynamodb2
@pytest.mark.parametrize("prefix,host,path", blocked_urls)
def test_allow(prefix, host, path):

    client = mock_aws()

    with app.test_client() as client:
        result = client.get(f"{prefix}{host}{path}")

        assert result.status_code == 200
        assert result.get_json() == {'blocked': False}
