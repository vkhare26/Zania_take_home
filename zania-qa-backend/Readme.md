# Zania QA Backend

This repository contains a backend service for document-based question answering, built using **FastAPI**, **LangChain**, and **OpenAI**.  
It allows you to upload a PDF document and a JSON file with questions, and returns concise, context-aware answers drawn directly from the document.

---

## Overview

The service extracts text from a PDF, splits it into chunks, embeds those chunks into a **FAISS vector index**, and uses a **retrieval-augmented generation (RAG)** pipeline to generate factual answers with OpenAI models.  
It’s designed to be simple, portable, and production-ready, with a clean FastAPI interface and full Docker support.

### Key Features
- Upload a **PDF** and a **JSON file** of questions.
- Uses **FAISS** for efficient similarity search.
- Retrieval and answer generation handled by **LangChain + OpenAI**.
- Simple, configurable environment setup.
- Ready for deployment via **Docker**.
- Includes unit tests (pytest).

---

## Project Structure

```

zania-qa-backend/
├── app/
│   ├── core/               # Logging and configuration
│   ├── models/             # Pydantic schemas
│   ├── services/           # Loader, retriever, and QA logic
│   ├── main.py             # FastAPI entry point
│   └── **init**.py
├── tests/                  # Unit tests
├── sample_data/            # Example PDFs and JSON files
├── logs/                   # Runtime logs
├── requirements.txt
├── Dockerfile
├── .env
└── README.md

```

---

## Setup

---

### 2. Local Development

```bash
# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the API
uvicorn app.main:app --reload
````

Once running, open your browser at:
👉 [http://localhost:8000/docs](http://localhost:8000/docs)

---

## API Usage

### Endpoint: `POST /qa`

Uploads a document (PDF) and a JSON file containing questions, and returns model-generated answers.

**Request Type:**
`multipart/form-data`

| Field       | Type         | Description                          |
| ----------- | ------------ | ------------------------------------ |
| `document`  | File (.pdf)  | The knowledge base document          |
| `questions` | File (.json) | A JSON file with a list of questions |

### Example Input

**questions.json**

```json
{
  "questions": [
    "What is the purpose of SOC 2 Type 2?",
    "Which controls are evaluated?",
    "How often are audits conducted?"
  ]
}
```

**Example Request**

```bash
curl -X POST "http://localhost:8000/qa" \
  -F "document=@sample_data/soc2-type2.pdf" \
  -F "questions=@sample_data/questions.json"
```

**Example Response**

```json
{
  "answers": [
    {
      "question": "What is the purpose of SOC 2 Type 2?",
      "answer": "It evaluates the operational effectiveness of security and availability controls over time."
    },
    {
      "question": "How often are audits conducted?",
      "answer": "SOC 2 Type 2 audits are typically performed annually."
    }
  ]
}
```

---

## Running Tests

```bash
pytest -v
```

---

## Docker Deployment

### Build the Image

```bash
docker build -t zania-qa-backend .
```

### Run the Container

```bash
docker run -p 8000:8000 --env-file .env zania-qa-backend
```

Then open:
👉 [http://localhost:8000/docs](http://localhost:8000/docs)

## Logs

All logs are saved to:

```
logs/zania_backend.log
```
