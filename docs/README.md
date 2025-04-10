# Documentation

## Project Structure
```
.
├── docs/                     # Documentation and architecture diagrams
│   ├── README.md
│   ├── Architecture_diagram.png
│   ├── System-diagram.jpg
│   ├── Vector_clocks_diagram.jpg
│   └── Leader_election_diagram.jpg
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
├── order_executor/             # Order executor microservice
│   ├── src/
│       ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│ 
├── order_queue/             # Order queue microservice
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

## Checkpoint 1:
### Architecture
![Architecture_diagram](https://github.com/user-attachments/assets/62486107-a7f9-43a8-8b79-7d7fca04c1df)

### System diagram
![System-diagram](https://github.com/user-attachments/assets/f5dd5430-fbfe-41a0-a885-d22542e94b29)

## Checkpoint 2:

### Vector clocks diagram
![VectorClocks-diagram](https://github.com/daum88/ds-practice-2025/blob/95c89419efd8afdec8658acd0fa1f5f1f0b2ea77/docs/vector_clocks_diagram.jpg)

### Leader election diagram
![Leader_election-diagram](https://github.com/daum88/ds-practice-2025/blob/95c89419efd8afdec8658acd0fa1f5f1f0b2ea77/docs/leader_election_diagram.png)




