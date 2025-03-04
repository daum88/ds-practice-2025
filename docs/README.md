# Documentation

This folder should contain your documentation, explaining the structure and content of your project. It should also contain your diagrams, explaining the architecture. The recommended writing format is Markdown.


## Project Structure
```
.
├── docs/                     # Documentation and architecture diagrams
│   ├── README.md
│   └── (Add diagrams here)
├── fraud_detection/          # Fraud detection microservice
│   ├── src/
│   ├── Dockerfile
│   ├── requirements.txt
├── frontend/                 # Frontend microservice
│   ├── src/
│   ├── index.html
│   ├── Dockerfile
├── orchestrator/             # Orchestrator microservice
│   ├── src/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
├── suggestions/              # Suggestions mircoservice
│   ├── src/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
├── transaction_verification/ # Transaction verification microservice
│   ├── src/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
├── utils/                    # Utility functions
├── .gitignore                # Git ignore file
├── README.md                 # Project documentation
└── docker-compose.yaml       # Docker Compose configuration
```



