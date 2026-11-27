# DockerAPI - Student Management Service

A lightweight, stateless Student Management API built with FastAPI, containerized with Docker, tested automatically with pytest, and wired into a GitHub Actions pipeline that verifies all routes before pushing images to Docker Hub.

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [API Routes](#api-routes)
- [Local Setup](#local-setup)
- [Automated Testing](#automated-testing)
- [Docker and Compose](#docker-and-compose)
- [Scaling and Load Balancing](#scaling-and-load-balancing)
- [CI/CD Pipeline](#cicd-pipeline)
- [Hosting Guide](#hosting-guide)

---

## Overview

The goal of this project is to take a backend API from local development to a repeatable, observable container workflow. Every incoming HTTP request passes through a logging middleware that records the method, path, status code, and latency in milliseconds. Keeping the application stateless allows multiple containers to run side by side behind a reverse proxy without losing client state.

## Project Structure

```text
.
├── .github/
│   └── workflows/
│       └── ActionsYaml.yaml   # Runs tests first, then builds and pushes to Docker Hub
├── .env.example               # Template for local Docker Hub credentials
├── .gitignore                 # Keeps secrets and cache files out of version control
├── automationTesting.py       # Route-level test suite using FastAPI TestClient
├── docker-compose.yml         # Single-command service orchestration with health check
├── Dockerfile                 # Container definition based on python:3.12-slim
├── main.py                    # FastAPI application, middleware, and CRUD endpoints
├── nginx.conf                 # Upstream load-balancer config for multi-instance runs
├── render.yaml                # Blueprint for deploying the Docker service on Render
├── requirements.txt           # Application and test dependencies
└── README.md                  # Project documentation and routing guide
```

## API Routes

All routes are served from the base URL (for example, `http://localhost:8000` locally or your hosted service URL). Interactive OpenAPI documentation is available at `/docs`.

| Method | Route | Description | Status Codes |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Returns service metadata and available top-level routes | `200` |
| `GET` | `/health` | Liveness check used by Docker, load balancers, and hosts | `200` |
| `GET` | `/students` | Lists all student records | `200` |
| `GET` | `/students/{student_id}` | Fetches a single student by ID | `200`, `404` |
| `POST` | `/students` | Creates a new student record | `201`, `422` |
| `PUT` | `/students/{student_id}` | Updates fields on an existing student record | `200`, `404`, `422` |
| `DELETE` | `/students/{student_id}` | Removes a student record by ID | `200`, `404` |

### Sample Request and Response

Create a student:

```bash
curl -X POST http://localhost:8000/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Rohan", "course": "Cloud Computing", "semester": 5}'
```

Response (`201 Created`):

```json
{
  "id": 3,
  "name": "Rohan",
  "course": "Cloud Computing",
  "semester": 5
}
```

Check service health:

```bash
curl http://localhost:8000/health
```

Response (`200 OK`):

```json
{
  "status": "healthy"
}
```

## Local Setup

1. Create and activate a virtual environment:

```bash
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

2. Install the dependencies:

```bash
pip install -r requirements.txt
```

3. Start the development server:

```bash
uvicorn main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` in your browser to inspect and test every endpoint interactively.

## Automated Testing

The route suite in `automationTesting.py` exercises `/`, `/health`, listing students, creating/reading/updating/deleting a record, and 404 handling for missing IDs.

Run the suite with pytest:

```bash
pytest automationTesting.py -v
```

Or run the script directly:

```bash
python automationTesting.py
```

## Docker and Compose

### Run with Docker Compose

Build and start the container in the background:

```bash
docker compose up -d --build
```

Check logs and container health:

```bash
docker compose logs -f
docker compose ps
```

Stop and clean up:

```bash
docker compose down
```

### Build and Run Manually

```bash
docker build -t <your_docker_username>/fastapi-app:v0.1 .
docker run --rm -p 8000:8000 <your_docker_username>/fastapi-app:v0.1
```

## Scaling and Load Balancing

Because `main.py` does not store per-user sessions in memory, you can run multiple instances on separate host ports and place Nginx in front of them:

```bash
docker run -d --name fastapi-1 -p 8001:8000 <your_docker_username>/fastapi-app:v0.1
docker run -d --name fastapi-2 -p 8002:8000 <your_docker_username>/fastapi-app:v0.1

docker run -d --name student-lb \
  -p 8080:8080 \
  -v "${PWD}/nginx.conf:/etc/nginx/nginx.conf:ro" \
  nginx:alpine
```

Requests sent to `http://localhost:8080/health` are distributed across both instances. Inspect `docker logs fastapi-1` and `docker logs fastapi-2` to observe traffic split between the containers.

Clean up when finished:

```bash
docker stop fastapi-1 fastapi-2 student-lb
docker rm fastapi-1 fastapi-2 student-lb
```

## CI/CD Pipeline

The workflow in `.github/workflows/ActionsYaml.yaml` runs on every push or pull request to `main`:

1. `test` job: installs dependencies and executes `pytest automationTesting.py -v`.
2. `build-and-push` job (runs only on pushes to `main` after tests pass): logs in to Docker Hub, builds the image from `Dockerfile`, and pushes both `v0.1` and `latest` tags.

### Required GitHub Secrets

In your `DockerAPI` repository on GitHub, open **Settings > Secrets and variables > Actions** and add:

- `DOCKERUSERNAME`: Your Docker Hub username.
- `DOCKERTOKEN`: A Docker Hub Personal Access Token generated from **Account Settings > Security > Access Tokens**.

## Hosting Guide

This repository includes `Dockerfile` and `render.yaml`, allowing direct deployment as a live web service on Render (or any Docker-capable host such as Railway or Fly.io):

1. Push this repository to your GitHub account under `DockerAPI`.
2. Sign in to [Render](https://render.com) and select **New > Blueprint** (or **New > Web Service**).
3. Connect your `DockerAPI` repository. Render reads `render.yaml`, builds the `Dockerfile`, binds to the injected `PORT` environment variable, and monitors `/health`.
4. Once deployed, verify the live service by opening `<your-render-url>/health` and `<your-render-url>/docs`.
