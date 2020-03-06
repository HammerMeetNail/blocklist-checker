[![Build Status](https://travis-ci.com/HammerMeetNail/blocklist-checker.svg?branch=master)](https://travis-ci.com/HammerMeetNail/blocklist-checker)
[![Coverage Status](https://coveralls.io/repos/github/HammerMeetNail/blocklist-checker/badge.svg?branch=master)](https://coveralls.io/github/HammerMeetNail/blocklist-checker?branch=master)

# blocklist-checker
A stateless service for determining if a URL is safe to visit.

# Prerequisites
1. DynamoDB table with the following attributes
	```
	Table name
		blocklist
	Primary partition key
		domain (String)
	Primary sort key
		sha256 (String)
	```
2. A record added to the table, such as `domain=example.com:80` and `path=/test`
3. (Optional) Docker

# Getting Started
```
docker build --tag hammermeetnail/blocklist-checker:latest .

# Add your AWS info to docker-compose.yml
docker-compose up -d

# Check if url is blocked
curl localhost/urlinfo/1/example.com:80/test
```

# How It Works
`blocklist-checker` listens for `GET` requests coming at `/urlinfo/1/{hostname_and_port}/{original_path_and_query_string}`. It will check the `host` and `path` combination against DynamoDB and return an `200 OK` if the URL is not found. If the URL is found, the URL was previously added to the blocklist and should not be routed to. A `403 Forbidden` will be returned. Each response will also return a small JSON response indicating whether the URL is blocked, e.g., `{blocked: true}`.

# Examples
```
# Start the application on port 80 using AWS creds
(blocklist-checker) dave@ubuntu-vm02:~/git/blocklist-checker$ docker-compose up
Starting blocklist-checker_url-blocklist_1 ... done
Attaching to blocklist-checker_url-blocklist_1
url-blocklist_1  | [2020-03-03 00:28:31 +0000] [1] [INFO] Starting gunicorn 20.0.4
url-blocklist_1  | [2020-03-03 00:28:31 +0000] [1] [INFO] Listening at: http://0.0.0.0:5000 (1)
url-blocklist_1  | [2020-03-03 00:28:31 +0000] [1] [INFO] Using worker: gthread
url-blocklist_1  | [2020-03-03 00:28:31 +0000] [10] [INFO] Booting worker with pid: 10
url-blocklist_1  | [2020-03-03 00:28:31 +0000] [12] [INFO] Booting worker with pid: 12
url-blocklist_1  | 172.21.0.1 - - [03/Mar/2020:00:28:43 +0000] "GET /urlinfo/1/example.com:80/ HTTP/1.1" 200 18 "-" "curl/7.58.0"
url-blocklist_1  | 172.21.0.1 - - [03/Mar/2020:00:28:48 +0000] "GET /urlinfo/1/example.com:80/test HTTP/1.1" 403 17 "-" "curl/7.58.0"

# Check safe an unsafe URLs
dave@ubuntu-vm02:~/git/url-blocklist$ curl localhost/urlinfo/1/example.com:80/
{"blocked":false}
dave@ubuntu-vm02:~/git/url-blocklist$ curl localhost/urlinfo/1/example.com:80/test
{"blocked":true}
```

# Local Development
Everything is built to work in a container and on a local workstation. 

## Container Guide
```
# Build only the main application, skipping tests
docker build --target Build --tag blocklist-checker .

# Build the application and execute tests
docker build --target Release --tag blocklist-checker .

# Run application locally on port 5000 after installing requirements.txt
gunicorn -c gunicorn.py wsgi:app
```

## Tests
`Pytest` is used to execute and paramaterize tests. `Moto` is used to mock out the AWS `boto3` library. Tests are executed in the `Dockerfile` under the `Test` stage. Test URLs are pulled from a known list retrieved from https://openphish.com/feed.txt
