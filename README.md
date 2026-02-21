Hackathon Project

This repository contains the BlackRock Challenge API implementation using FastAPI, Docker, and CI/CD automation.

```text
hackathon-project/
├── .github/
│   └── workflows/
│       └── docker-push.yml    # Automation
├── test/                      # test cases
|   ├── test_filter.py
|   ├── test_returns.py
|   └── test_validator.py
├── main.py                    # Logic
├── Dockerfile                 # Recipe
├── compose.yml                # blueprint
├── requirements.txt           # Ingredients
└── README.md                  # Manual

🚀 Running the Project

Prerequisites

Docker installed on your machine
Docker Compose installed

Steps

Clone the repository:

git clone https://github.com/kirankumaras/hackathon-project.git
cd hackathon-project

Build and run the container:

docker compose up --build

The API will be available at: http://localhost:5477

API endpoints:
/blackrock/challenge/v1/transactions:parse
/blackrock/challenge/v1/transactions:validator
/blackrock/challenge/v1/transactions:filter
/blackrock/challenge/v1/returns:index
/blackrock/challenge/v1/returns:nps
/blackrock/challenge/v1/performance

⚙️ CI/CD Pipeline

The .github/workflows/docker-push.yml automates building and pushing the Docker image.

📖 Summary

Run the API: docker compose up --build

Access endpoints: http://localhost:5477


alternative:

docker pull kirankumaras/hackathon-docker:latest
docker run -p 5477:5477 kirankumaras/hackathon-docker:latest