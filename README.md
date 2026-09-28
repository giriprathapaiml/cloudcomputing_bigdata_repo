Lab Manual: Asynchronous ETL Processing with Flask, Celery, Redis, Docker and Postman
1. Lab Objective
In this lab, you will build and test a simple asynchronous ETL processing system using:

Flask — REST API

Celery — background task processing

Redis — Celery message broker and result backend

Docker — containerization

Docker Compose — orchestration

Postman — API testing

The application demonstrates how a Flask API can accept an ETL request and delegate the actual processing to a Celery worker.

Instead of making the client wait for the ETL process to complete, Flask places the task in Redis and immediately returns a Celery task ID.

2. Architecture
The application consists of three Docker services:

                         POST /run-etl
                              |
                              v
                    +------------------+
                    |   Flask Web API  |
                    |      :5000       |
                    +--------+---------+
                             |
                       run_etl.delay()
                             |
                             v
                    +------------------+
                    |      Redis       |
                    |      :6379       |
                    |  Broker/Backend  |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    |  Celery Worker   |
                    |                  |
                    |    run_etl()     |
                    +------------------+

Request flow
Postman sends a POST request to Flask.

Flask extracts the param value.

Flask calls run_etl.delay(param).

Celery sends the task to Redis.

The Celery worker receives the task.

The worker executes the ETL operation.

The result is stored in Redis.

Flask immediately returns the Celery task ID to Postman.

3. Prerequisites
Before starting the lab, install the following software.

Required software
Docker Desktop
Install Docker Desktop for Windows/macOS, or Docker Engine + Docker Compose on Linux.

Verify Docker:

docker --version

Example:

Docker version 27.x.x

Verify Docker Compose:

docker compose version

Example:

Docker Compose version v2.x.x

Postman
Install Postman for testing the REST API.

4. Project Structure
Create the following project directory:

etl-project/
│
├── app.py
├── tasks.py
├── requirements.txt
├── Dockerfile
├── Dockerfile.worker
└── docker-compose.yml

The purpose of each file is:

File	Purpose
app.py	Flask REST API
tasks.py	Celery configuration and ETL task
requirements.txt	Python dependencies
Dockerfile	Flask application image
Dockerfile.worker	Celery worker image
docker-compose.yml	Starts Flask, Celery and Redis

5. Create the Flask Application
Create a file named:

app.py

Add:

from flask import Flask, request, jsonify
from tasks import run_etl

app = Flask(__name__)


@app.route("/run-etl", methods=["POST"])
def trigger_etl():
    data = request.get_json(silent=True) or {}
    param = data.get("param", "default")

    task = run_etl.delay(param)

    return jsonify({"task_id": task.id}), 202


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

Explanation
Flask application
app = Flask(__name__)

Creates the Flask application.

API endpoint
@app.route("/run-etl", methods=["POST"])

Creates a POST endpoint:

/run-etl

Reading JSON
data = request.get_json(silent=True) or {}

Reads JSON from the request body.

Using silent=True prevents Flask from raising an exception when the request does not contain valid JSON.

Extracting the parameter
param = data.get("param", "default")

If the request contains:

{
  "param": "customer_data"
}

the value of param becomes:

customer_data

If no parameter is supplied, the application uses:

default

Queueing the Celery task
task = run_etl.delay(param)

This sends the task to Celery.

The ETL process does not run inside the Flask request.

Returning the task ID
return jsonify({"task_id": task.id}), 202

The API returns HTTP status:

202 Accepted

because the request has been accepted for asynchronous processing.

6. Create the Celery Task
Create:

tasks.py

Add:

from celery import Celery
import time


# Configure Celery to use Redis
celery_app = Celery(
    "etl",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
)


@celery_app.task
def run_etl(param):
    print(f"Starting ETL with param: {param}")

    time.sleep(5)  # Simulate ETL work

    print("ETL complete")

    return f"Processed with param: {param}"

7. Understanding the Celery Configuration
The following configuration connects Celery to Redis:

celery_app = Celery(
    "etl",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
)

There are two important components.

Broker
redis://redis:6379/0

The broker is used to send tasks from Flask to the Celery worker.

Result backend
redis://redis:6379/0

The backend stores task results.

8. Understanding the ETL Task
The task is defined using:

@celery_app.task

This tells Celery that run_etl() can execute as a background task.

The function:

def run_etl(param):

accepts the parameter supplied by the Flask API.

For demonstration, the ETL process waits for five seconds:

time.sleep(5)

This simulates a long-running ETL operation.

The task then returns:

return f"Processed with param: {param}"

9. Create requirements.txt
Create:

requirements.txt

Add:

Flask
celery
redis

These packages are required for the application.

10. Create the Flask Dockerfile
Create:

Dockerfile

Add:

FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]

Explanation
Base image
FROM python:3.10-slim

Uses a lightweight Python 3.10 image.

Working directory
WORKDIR /app

Sets /app as the working directory inside the container.

Copy dependencies
COPY requirements.txt .

Copies the dependency file into the image.

Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

Installs Flask, Celery and Redis Python packages.

Copy application
COPY . .

Copies the project files into the container.

Start Flask
CMD ["python", "app.py"]

Starts the Flask API.

11. Create the Celery Worker Dockerfile
Create:

Dockerfile.worker

Add:

FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["celery", "-A", "tasks.celery_app", "worker", "--loglevel=info"]

The worker uses the same application files but starts Celery instead of Flask.

The important command is:

celery -A tasks.celery_app worker --loglevel=info

It tells Celery:

Import celery_app from tasks.py

Start a worker

Display informational logs

12. Create Docker Compose Configuration
Create:

docker-compose.yml

Add:

version: "3.9"

services:
  web:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "5000:5000"
    depends_on:
      - redis

  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

13. Understanding Docker Compose
Docker Compose starts three services.

Web
web:

Runs the Flask API.

The port mapping:

ports:
  - "5000:5000"

means:

Host port 5000 → Container port 5000

Therefore the API is accessible at:

http://localhost:5000

Worker
worker:

Runs the Celery worker.

It does not expose a port because clients do not directly communicate with the worker.

Redis
redis:
  image: redis:7-alpine

Runs Redis using the official lightweight Redis image.

14. Why the Hostname Is redis
In tasks.py:

broker="redis://redis:6379/0"

The hostname is:

redis

This matches the Docker Compose service name:

services:
  redis:

Docker Compose creates an internal network where containers can communicate using service names.

Therefore:

redis

resolves to the Redis container from the Flask and Celery containers.

Do not normally change this to:

localhost

inside the containers.

Inside a container, localhost refers to that same container, not the Redis container.

15. Build and Start the Application
Open a terminal in the project directory.

Run:

docker compose up --build

The --build option tells Docker to rebuild the application images.

You should see three services start:

web
worker
redis

16. Verify Running Containers
Open another terminal and run:

docker compose ps

You should see something similar to:

NAME              SERVICE    STATUS
etl-project-web   web        running
etl-project-worker worker   running
etl-project-redis redis      running

The exact container names may differ.

17. Verify Flask
Open a browser and visit:

http://localhost:5000

You may see:

404 Not Found

This is expected because the application currently has only:

POST /run-etl

There is no / route.

A 404 at the root does not mean Flask is broken.

18. Test Using Postman
Open Postman.

Create a new HTTP request.

Method
Select:

POST

URL
Enter:

http://localhost:5000/run-etl

19. Configure the Postman Body
Go to:

Body

Select:

raw

Then select:

JSON

Enter:

{
  "param": "test"
}

20. Verify the Content-Type
Go to the Headers tab.

Make sure the following header exists:

Key	Value
Content-Type	application/json

The request should effectively be:

POST http://localhost:5000/run-etl

Content-Type: application/json

{
  "param": "test"
}

21. Send the Request
Click:

Send

You should receive:

{
  "task_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}

The HTTP status should be:

202 Accepted

The task ID will be different for every request.

22. What Happens After Send?
The request follows this sequence:

Postman
   |
   | POST /run-etl
   v
Flask
   |
   | run_etl.delay("test")
   v
Redis
   |
   | task
   v
Celery Worker
   |
   | run_etl("test")
   v
ETL Processing
   |
   | 5 seconds
   v
ETL Complete

The Flask API returns the task ID immediately.

It does not wait five seconds for the ETL operation.

23. Check Celery Worker Logs
Look at the terminal running:

docker compose up --build

You should see the worker receive the task.

You should see output similar to:

Starting ETL with param: test

After approximately five seconds:

ETL complete

You should also see Celery report that the task completed successfully.

24. Test With Different Parameters
In Postman, change the request body to:

{
  "param": "customer_data"
}

Click Send.

The response will contain another task ID:

{
  "task_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}

The worker should show:

Starting ETL with param: customer_data
ETL complete

Try another parameter:

{
  "param": "sales_data"
}

The worker should process:

sales_data

25. Test Without a Parameter
Send:

{}

The application uses:

default

because of:

param = data.get("param", "default")

The worker should display:

Starting ETL with param: default

26. Test an Empty Request
You can also send:

{}

The request should still be accepted because the application has a default parameter.

Expected response:

{
  "task_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}

27. Common Error: 415 Unsupported Media Type
If Postman returns:

415 Unsupported Media Type

check the request configuration.

Correct configuration
In Postman:

Body
  → raw
  → JSON

The header should be:

Content-Type: application/json

The body should be:

{
  "param": "test"
}

Also make sure you are not using:

form-data

or:

x-www-form-urlencoded

28. Why request.get_json() Is Used
The Flask application uses:

data = request.get_json(silent=True) or {}

instead of directly accessing:

request.json

This makes the endpoint more tolerant of requests that do not contain valid JSON.

The application then safely obtains the parameter:

param = data.get("param", "default")

29. Check Flask Logs
If the API does not work, run:

docker compose logs web

This displays Flask container logs.

For example:

 * Running on http://127.0.0.1:5000
 * Running on http://172.x.x.x:5000

30. Check Celery Logs
Run:

docker compose logs worker

This shows Celery worker logs.

You can also follow the logs continuously:

docker compose logs -f worker

31. Check Redis Logs
Run:

docker compose logs redis

Redis should start successfully and listen on port:

6379

32. Check All Logs
To follow all services:

docker compose logs -f

To stop following logs:

Ctrl + C

This normally does not stop the containers; it stops log viewing.

33. Check Individual Container Status
Run:

docker compose ps

All three services should be running:

web
worker
redis

If one has stopped, inspect its logs.

For example:

docker compose logs worker

34. Restart the Application
Stop the application:

docker compose down

Start it again:

docker compose up

If source files or dependencies have changed, use:

docker compose up --build

35. Rebuild From Scratch
If you suspect an old Docker image is being used:

docker compose down
docker compose build --no-cache
docker compose up

The --no-cache option forces Docker to rebuild the image without using previous build layers.

36. Verify Redis Connectivity
You can check Redis from the Redis container:

docker compose exec redis redis-cli ping

Expected response:

PONG

This confirms that Redis is running.

37. Important Docker Networking Concept
From your host machine, Redis is available at:

localhost:6379

because of:

ports:
  - "6379:6379"

However, from the Flask and Celery containers, Redis is accessed using:

redis:6379

Therefore:

Host:
localhost:6379

Docker containers:
redis:6379

38. Current Limitation of the API
The current API returns only the task ID:

{
  "task_id": "..."
}

It does not currently expose an endpoint such as:

GET /task/<task_id>

Therefore Postman cannot yet directly query the status of a submitted task.

The Celery worker logs can be used to verify that the task completed.

A future enhancement can add a task-status endpoint using Celery's:

AsyncResult

39. Expected Lab Result
After completing the lab, you should be able to demonstrate:

Flask
POST /run-etl

accepts an ETL request.

Redis
Acts as the Celery message broker and result backend.

Celery
Processes the ETL asynchronously.

Docker
Runs the components in isolated containers.

Postman
Sends requests to the Flask REST API.

40. Final Project Structure
Your completed project should look like:

etl-project/
│
├── app.py
├── tasks.py
├── requirements.txt
├── Dockerfile
├── Dockerfile.worker
└── docker-compose.yml

41. Complete Source Code
app.py
from flask import Flask, request, jsonify
from tasks import run_etl

app = Flask(__name__)


@app.route("/run-etl", methods=["POST"])
def trigger_etl():
    data = request.get_json(silent=True) or {}
    param = data.get("param", "default")

    task = run_etl.delay(param)

    return jsonify({"task_id": task.id}), 202


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

tasks.py
from celery import Celery
import time


celery_app = Celery(
    "etl",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
)


@celery_app.task
def run_etl(param):
    print(f"Starting ETL with param: {param}")

    time.sleep(5)

    print("ETL complete")

    return f"Processed with param: {param}"

requirements.txt
Flask
celery
redis

Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]

Dockerfile.worker
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["celery", "-A", "tasks.celery_app", "worker", "--loglevel=info"]

docker-compose.yml
version: "3.9"

services:
  web:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "5000:5000"
    depends_on:
      - redis

  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

42. Lab Execution Checklist
Use the following checklist during the lab.

 Docker is installed.

 Docker Compose is available.

 Postman is installed.

 Project directory is created.

 app.py is created.

 tasks.py is created.

 requirements.txt is created.

 Dockerfile is created.

 Dockerfile.worker is created.

 docker-compose.yml is created.

 docker compose up --build executes successfully.

 web container is running.

 worker container is running.

 redis container is running.

 Postman is configured for POST.

 URL is http://localhost:5000/run-etl.

 Body is configured as raw JSON.

 Content-Type is application/json.

 ETL parameter is supplied.

 API returns HTTP 202.

 API returns a Celery task ID.

 Celery worker receives the task.

 Worker prints ETL complete.

43. Expected Final Demonstration
A successful demonstration should show the following.

Postman request
POST http://localhost:5000/run-etl
Content-Type: application/json

{
  "param": "student_data"
}

Postman response
HTTP/1.1 202 Accepted

{
  "task_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}

Celery worker
Starting ETL with param: student_data
ETL complete

This confirms that Flask, Redis and Celery are communicating correctly and that the ETL job is being executed asynchronously.