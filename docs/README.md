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
├── books_database/                 # books database microservice
│   ├── src/
│       ├── app.py
│   ├── Dockerfile
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
├── payment/                 # Payment microservice
│   ├── src/
│       ├── app.py
│   ├── Dockerfile
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
![Leader_election-diagram](https://github.com/daum88/ds-practice-2025/blob/4132a05ba8e9ceeefe893c7929f20bf7d6357778/docs/leader_election_bully_diagram.png)

### System model:

Our system follows a distributed microservice architecture. Each service runs in its own Docker container and communicates with others over gRPC. The setup is managed using Docker Compose, making it easy to run and scale different components.

**Architecture & Services:**
The system is made up of the following key services:

**Orchestrator:**
This is the main coordinator. It receives incoming orders (via an HTTP API), calls other services to verify and enrich the order, and finally adds it to a queue. It's the only component that talks to every other service directly.

**Fraud Detection:**
Checks if an order looks suspicious. Stateless and responds quickly to fraud-check requests.

**Transaction Verification:**
Confirms whether an order is valid (e.g., payment amount, rules, etc.).

**Suggestions:**
Generates recommendations to go along with an order (like upselling). Uses OpenAI behind the scenes.

**Order Queue:**
A priority queue that holds orders waiting to be executed. Other services push to it, and the executor pulls from it.

**Order Executor:**
This service dequeues and processes orders. There can be multiple executor instances running — they use a leader election algorithm to make sure only one of them is actively processing orders at a time.

**Connections Between Services:**
All the backend services (fraud, verification, suggestions, queue) expose gRPC APIs. The orchestrator is a gRPC client to each of them. The executor talks to the order queue using gRPC as well.
Each service is connected through Docker’s internal network, and service names in the compose file are used for discovery.

**Leader Election:**
Leader Election in this system uses the Bully Algorithm, where each order executor instance has a unique numeric ID. On startup or failure detection, executors initiate elections by contacting higher-ID peers. The instance with the highest reachable ID becomes the leader and announces itself. Only the leader dequeues and executes orders. If it fails, remaining executors detect it via heartbeats and trigger a new election to maintain continuous processing.

**Failure Scenarios:**
If the executor leader crashes, the others detect the failure and elect a new leader.
If the orchestrator goes down, new orders can’t be submitted, but the rest of the system keeps running.
If one of the worker services (fraud, verification, etc.) fails, the orchestrator handles it (e.g., skips suggestions or marks the order as failed).
If the order queue goes down, nothing can be enqueued or dequeued until it's back.

**Assumptions:**
We assume fail-stop behavior (a crashed service just stops, doesn’t act weird).
Services can recover from restarts.
The internal Docker network is reliable.


## Checkpoint 3:

### Consistency protocol diagram
![Consistency_Protocol-diagram](https://github.com/daum88/ds-practice-2025/blob/venkat/docs/consistency_protocol_diagram.png)

### Two-phase commit protocol diagram
![Two-Phase_commit_protocol-diagram](https://github.com/daum88/ds-practice-2025/blob/venkat/docs/2Phase_commit_protocol_diagram.png)



