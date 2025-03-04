# Documentation

## Project Structure
```
.
├── docs/                     # Documentation and architecture diagrams
│   ├── README.md
│   ├── Architecture_diagram.png
│   └── System-diagram.jpg
│ 
├── frontend/                 # Frontend microservice
│   ├── src/
│       ├── index.html
│   ├── Dockerfile
│ 
├── orchestrator/             # Orchestrator microservice
│   ├── src/
│       ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│ 
├── fraud_detection/          # Fraud detection microservice
│   ├── src/
│       ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│ 
├── transaction_verification/ # Transaction verification microservice
│   ├── src/
│       ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│ 
├── suggestions/              # Suggestions mircoservice
│   ├── src/
│       ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│ 
├── utils/                    # Utility functions (apis, pb, others)
├── docker-compose.yaml       # Docker Compose configuration
├── README.md                 # Project documentation
```

### Architecture
![Architecture_diagram](https://github.com/user-attachments/assets/62486107-a7f9-43a8-8b79-7d7fca04c1df)

### System diagram
![System-diagram](https://github.com/user-attachments/assets/f5dd5430-fbfe-41a0-a885-d22542e94b29)


