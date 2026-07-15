# High-Load A/B Testing Recommendation Service
![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)

## Business Context

This project represents a scalable content recommendation engine developed for a high-traffic social media/e-commerce application. The goal of this service is to dynamically serve customized post recommendations to users, aiming to increase user engagement metrics (e.g., likes, retention) and conversion rates. 

To continuously improve recommendation quality, the service implements a robust **A/B testing architecture**. Real-time traffic is deterministically split between a lightweight control model (CatBoost) and a computationally heavier, deep learning-based test model (PyTorch with categorical embeddings).

## System Architecture

The service leverages a FastAPI backend connected to a PostgreSQL Feature Store. 

### Key Architectural Decisions:
1. **In-Memory Caching:** To achieve < 500ms latency per request, post and user features are pre-loaded into Pandas DataFrames during the application startup phase.
2. **Deterministic Hashing:** A/B traffic splitting is handled using `hashlib.md5(user_id + SALT)`. This ensures that a specific user always falls into the same experimental group across multiple sessions, preventing data corruption during the experiment.
3. **Model Fallback:** The API serves CatBoost recommendations as the baseline (Control) and dynamically invokes the PyTorch embedding architecture for the Test group.

### A/B Split & Inference Workflow

```mermaid
graph TD
    Client((Client)) -->|GET /post/recommendations/| API[FastAPI Backend]
    
    subgraph Data Layer [Feature Store]
        DB[(PostgreSQL)] -.->|Startup Preload| Cache_ML[(ML Features Cache)]
        DB -.->|Startup Preload| Cache_DL[(DL Features Cache)]
    end
    
    subgraph Model Serving
        Split{Traffic Split<br>MD5 Hash + Salt}
        Control[Control Group<br>CatBoost Model]
        Test[Test Group<br>PyTorch Model]
    end
    
    API --> Split
    Split -- "Control (50%)" --> Control
    Split -- "Test (50%)" --> Test
    
    Control -.-> Cache_ML
    Test -.-> Cache_DL
    
    Control --> Formatter[Response Formatter]
    Test --> Formatter
    Formatter -->|JSON Response| API
    API --> Client
```

## The A/B Splitting Workflow

The core of an A/B test is the splitting mechanism. It must satisfy two strict rules:
1. **Deterministic**: If User #123 is placed in the Test group today, they must remain in the Test group tomorrow. If they switch groups, the experiment data gets corrupted.
2. **Unbiased/Randomized**: The distribution of users must naturally fall to a 50/50 split without skewing based on user ID patterns (e.g., all even IDs shouldn't necessarily go to one group if IDs aren't randomly generated).

### The Hashing Implementation
To achieve this, we use the `hashlib.md5` hashing algorithm combined with a **salt**.

```mermaid
sequenceDiagram
    participant User
    participant Endpoint
    participant Hasher
    participant ML_Model as Control (CatBoost)
    participant DL_Model as Test (PyTorch)

    User->>Endpoint: Request (user_id=123, dt)
    Endpoint->>Hasher: get_exp_group(123)
    
    Note over Hasher: 1. Concat: "123" + "my_salt"<br/>2. MD5 Hash: a1b2c3...<br/>3. To Integer: 84930...<br/>4. Modulo 100: 42
    
    alt hash_val % 100 < 50
        Hasher-->>Endpoint: Return "test"
        Endpoint->>DL_Model: Run PyTorch Inference
        DL_Model-->>Endpoint: Return Top 5 DL Posts
    else hash_val % 100 >= 50
        Hasher-->>Endpoint: Return "control"
        Endpoint->>ML_Model: Run CatBoost Inference
        ML_Model-->>Endpoint: Return Top 5 ML Posts
    end
    
    Endpoint-->>User: {"exp_group": "...", "recommendations": [...]}
```

**Why a Salt?**
If multiple teams run multiple A/B tests on the same users, simply using `md5(user_id) % 100` would result in the exact same users falling into the test group for *every single experiment*. By adding a unique `SALT` (like `"my_salt"`), we pseudo-randomize the distribution entirely for this specific experiment.

## Setup & Deployment

This service is fully containerized using Docker, allowing seamless deployment to any cloud environment.

### 1. Model Weights
To prevent bloating the Git repository with large `.pkl` files, the model generation process is simulated.
* **Control Model:** You can run `python generate_models.py` to create a dummy `model_control.pkl` in the root directory. 
* **Test Model:** For demonstration, the PyTorch model weights are serialized as a Base64 string directly within `app.py`. In a true production environment, these would be retrieved from an S3 bucket or local volume.

### 2. Environment Variables
Secure credentials and configurations are loaded via environment variables.

Copy the `.env.example` file:
```bash
cp .env.example .env
```
Update `.env` with your PostgreSQL credentials.

### 3. Docker Deployment
Build and run the FastAPI service via Docker:

```bash
# Build the Docker image
docker build -t recommendation-service .

# Run the container (injecting the .env file)
docker run -d --name rec-api -p 8000:8000 --env-file .env recommendation-service
```

### 4. API Endpoints
* **Swagger UI:** `http://localhost:8000/docs`
* **Recommendation Endpoint:**
  ```http
  GET /post/recommendations/?id=200&time=2023-01-01T12:00:00&limit=5
  ```
  Returns a structured JSON response containing the recommended posts and the assigned experimental group (`control` or `test`).
