# blocklist-manager
A service for managing a URL blocklist in DynamoDB

# Prerequisites
1. DynamoDB table with the following attributes
```
Table name
	blocklist
Primary partition key
	domain (String)
Primary sort key
	path (String)
```

# Getting Started
```
docker build --tag url-blocklist:local .
docker-compose up -d

# Check if url is blocked
curl localhost/urlinfo/1/example.com:80/test
```

# Local Development
```
gunicorn -c gunicorn.py wsgi:app
```