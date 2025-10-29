# Zania QA Backend

This repository contains a backend service for document-based question answering, built with **FastAPI**, **LangChain**, **FAISS**, and **OpenAI**.  
It allows you to upload a PDF document and a JSON file of questions, and returns concise, context-aware answers drawn directly from the content of the document.

---

## Overview

The service extracts text from PDFs, splits it into manageable chunks, embeds them into a **FAISS** vector index, and runs a **retrieval-augmented generation (RAG)** pipeline using OpenAI models.  
It’s lightweight, production-ready, and easy to deploy via Docker.

### Key Features
- Upload a **PDF** and a **JSON** file of questions.
- Uses **FAISS** for fast semantic similarity search.
- Hybrid retrieval with **BM25 + FAISS embeddings**.
- Powered by **LangChain** and **OpenAI GPT-4o-mini**.
- Clean FastAPI interface with automatic docs (`/docs`).
- Includes structured logging and unit tests.
- Fully Dockerized for easy deployment.

---

## Project Structure

```

zania-qa-backend/
├── app/
│   ├── core/               # Logging and configuration
│   ├── services/           # Loader, retriever, and QA logic
│   ├── main.py             # FastAPI entry point
│   └── **init**.py
├── tests/                  # Unit tests (pytest)
├── sample_data/            # Example PDFs and JSON files
├── logs/                   # Runtime logs
├── requirements.txt
├── Dockerfile
├── .env
└── README.md

````

---

## Setup

### 1. Environment Variables

Create a `.env` file in the project root:

```bash
OPENAI_API_KEY=your_openai_api_key_here
````

*(Make sure `.env` is included in your `.gitignore` so your key never gets pushed to GitHub.)*

---

### 2. Local Development

```bash
# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the API
venv/bin/python -m uvicorn app.main:app --reload
```

Then open your browser at:
http://localhost:8000/docs

---

## API Usage

### Endpoint: `POST /qa`

Uploads a document [PDF or Json] and a JSON file of questions, and returns model-generated answers.

**Request Type:**
`multipart/form-data`

| Field       | Type         | Description                          |
| ----------- | ------------ | ------------------------------------ |
| `document`  | File (.pdf)  | The knowledge base document          |
| `questions` | File (.json) | A JSON file containing the questions |

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

## Example Run (Real SOC 2 Type 2 Use-Case)

Here’s a real example using a SOC 2 Type 2 report (`soc2-type2.pdf`) and the following questions:

**questions.json**

```json
{
  "questions": [
    "Do you have formally defined criteria for notifying a client during an incident that might impact the security of their data or systems? What are your SLAs for notification?",
    "Is personal information transmitted, processed, stored, or disclosed to or retained by third parties? If yes, describe.",
    "Which cloud providers do you rely on?",
    "Please specify the primary data center location/region of the underlying cloud infrastructure used to host the service(s) as well as the backup location(s).",
    "Which of the following, if any, are performed as part of your monitoring process for the service: APM, EUM, or DEM?"
  ]
}
```

**Response:**

```json
{
  "answers": [
    {
      "question": "Do you have formally defined criteria for notifying a client during an incident that might impact the security of their data or systems? What are your SLAs for notification?",
      "answer": "The context does not specify formal criteria or SLAs for client notification. It notes that customers can contact Product Fruits s.r.o. via the support email address and that security incidents are escalated by severity, but specific notification timelines or SLAs are not detailed."
    },
    {
      "question": "Is personal information transmitted, processed, stored, or disclosed to or retained by third parties? If yes, describe.",
      "answer": "Yes. Customer PII is encrypted at rest in production databases and transmitted over HTTPS/TLS. AWS hosts the infrastructure, and vendor risk is reviewed periodically to maintain compliance with security standards."
    },
    {
      "question": "Which cloud providers do you rely on?",
      "answer": "Product Fruits s.r.o. relies on Amazon Web Services (AWS) for hosting, GitHub for application management, and Microsoft Office 365 for collaboration and communication services."
    },
    {
      "question": "Please specify the primary data center location/region of the underlying cloud infrastructure used to host the service(s) as well as the backup location(s).",
      "answer": "The primary data center is hosted in AWS Europe. No backup region is specified in the document."
    },
    {
      "question": "Which of the following, if any, are performed as part of your monitoring process for the service: APM, EUM, or DEM?",
      "answer": "Information not found in the provided document."
    }
  ]
}
```

This example shows how the backend parses a real compliance report, retrieves relevant sections, and produces accurate, context-aware answers — without hallucinating or fabricating information.

---

## Running Tests

```bash
python -m pytest -v
```

All tests cover PDF loading, validation, and endpoint behavior using mock components.

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
http://localhost:8000/docs

---

## Logs

All runtime logs are written to:

```
logs/zania_backend.log
```

---

## Notes

* The `.env` file **must never** be committed to Git.
  It’s already listed in `.gitignore`.
* The code is modular, making it easy to replace FAISS with Chroma or another vector store if needed.

```
