# PropAI — Autonomous Real Estate AI Platform

> Multi-Agent Real Estate AI System built with **FastAPI + LangChain + FAISS RAG + XGBoost + SHAP + Gemini + Groq**

A broker-focused AI copilot that performs **lead scoring, property retrieval, RAG knowledge answering, explainability reporting, and multi-agent orchestration** in one platform.

---

## Live System Capabilities

PropAI enables real estate brokers to:

* Score leads automatically (HOT / WARM / COLD)
* Retrieve matching properties instantly
* Answer legal & market questions using RAG
* Generate explainable AI insights (SHAP)
* Run orchestrated multi-agent workflows

---

## Evaluation Status

RAG quality is measured with RAGAS (faithfulness, answer relevancy, context precision/recall) against a held-out query set, targeting **0.97 faithfulness** and **<2% hallucination rate**.

The current run is **not a reliable measurement**: Groq's free-tier rate limits caused most per-query judge calls to time out, so only 1 of 9 queries produced a valid faithfulness score (5 is the minimum sample size the evaluator requires before reporting a result — see `src/evaluation/ragas_evaluator.py`). The single valid sample scored faithfulness 1.0 and hallucination rate 0.0, which is directionally encouraging but not statistically meaningful at n=1. A full run needs a paid LLM tier to sustain the required call volume.

| Metric | Target | Current Status |
| --- | --- | --- |
| RAGAS Faithfulness | 0.97 | Not yet reliably measured (n=1 of 9, insufficient sample) |
| Hallucination Rate | <2% | Not yet reliably measured (n=1 of 9, insufficient sample) |
| API Latency | <50ms | Target, not yet benchmarked |
| Lead Scoring Engine | — | XGBoost + LLM ensemble |
| Explainability | — | SHAP attribution |

Full evaluation artifacts: `backend/data/evaluation/ragas_results.json`.

---

## System Architecture

```
User Request
     │
     ▼
FastAPI Backend (app.py)
     │
     ▼
LangChain Orchestrator Agent
     │
 ┌────────────┬────────────┬────────────┬────────────┐
 ▼            ▼            ▼            ▼
Lead        Property      RAG        Explainability
Scoring      Search       Agent        Agent
Agent        Agent
 │            │            │
XGBoost     FAISS        Knowledge
+ SHAP      Retriever     Base
```

---

## Project Structure

```
propai-real-estate-platform/
│
├── app.py
├── requirements.txt
├── config/
│
├── src/
│   ├── agents/
│   │   ├── orchestrator.py
│   │   ├── lead_scoring_agent.py
│   │   ├── property_retrieval_agent.py
│   │   ├── rag_agent.py
│   │   ├── communication_agent.py
│   │   └── explainability_agent.py
│   │
│   ├── rag/
│   │   └── pipeline.py
│   │
│   ├── prompts/
│   │   └── templates.py
│   │
│   ├── database/
│   │   ├── mysql_client.py
│   │   └── mongo_client.py
│   │
│   ├── evaluation/
│   │   └── ragas_evaluator.py
│   │
│   └── utils/
│       ├── settings.py
│       └── llm_client.py
│
├── tests/
│
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Free LLM Providers Supported

| Provider      | Model                   |
| ------------- | ----------------------- |
| Google Gemini | gemini-1.5-flash        |
| Groq          | llama-3.3-70b-versatile |

Embeddings run locally using FAISS.

---

## Installation Guide

### Step 1 — Clone repository

```
git clone https://github.com/Shaaha-7/propai-real-estate-platform.git
cd propai-real-estate-platform
```

---

### Step 2 — Create virtual environment

Windows:

```
python -m venv venv
venv\Scripts\activate
```

Mac/Linux:

```
python3 -m venv venv
source venv/bin/activate
```

---

### Step 3 — Install dependencies

```
pip install -r requirements.txt
```

---

### Step 4 — Configure environment variables

Create `.env` file:

```
GOOGLE_API_KEY=your_key_here
LLM_PROVIDER=gemini
```

---

### Step 5 — Run server

```
uvicorn app:app --reload
```

Open:

```
http://localhost:8000/docs
```

---

## API Endpoints

| Endpoint           | Purpose                      |
| ------------------ | ---------------------------- |
| /agent/chat        | Multi-agent broker assistant |
| /leads/score       | Lead classification          |
| /properties/search | Property retrieval           |
| /rag/query         | Knowledge base Q&A           |
| /evaluation/ragas  | RAG evaluation                |
| /metrics           | Monitoring stats             |

---

## Lead Scoring Engine

Hybrid scoring architecture:

```
60% XGBoost Model
40% LLM Reasoning Layer
```

Produces:

* classification label
* confidence score
* SHAP explanation

---

## Example API Call

```
POST /leads/score
```

Example payload:

```
{
 "client_name": "Ahmed",
 "budget_aed": 2000000,
 "location_preference": "Dubai Hills",
 "bedrooms": 3,
 "timeline_months": 2
}
```

---

## Docker Deployment

```
docker-compose up -d
```

Services started:

* FastAPI
* MySQL
* MongoDB
* Redis
* MLflow

---

## Safety Guardrails

Includes:

* JSON schema validation
* hallucination reduction pipeline
* SHAP explainability
* confidence thresholds
* structured output enforcement

---

## Tech Stack

FastAPI
LangChain
FAISS
Gemini
Groq
XGBoost
SHAP
RAGAS
MLflow
Docker

---

## Author

**Shabeer Ahamed K**

Autonomous Real Estate AI Platform Developer
Multi-Agent LLM Systems · Applied AI · Production ML Pipelines
