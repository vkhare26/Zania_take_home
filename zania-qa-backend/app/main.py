import os
import json
import shutil
import tempfile
import traceback
from fastapi import FastAPI, UploadFile, HTTPException
from dotenv import load_dotenv

# Local imports
from app.services.loader import load_documents
from app.services.qa_chain import build_retriever, build_qa_chain
from app.core.logging import setup_logging


# Load environment variables and initialize logging early

load_dotenv()
logger = setup_logging()

# Initialize the FastAPI app
app = FastAPI(title="Zania RAG Backend", version="1.0.0")


@app.on_event("startup")
def startup_event():
    """Log service startup event."""
    logger.info("Zania RAG backend starting up.")



# /qa Endpoint — Core RetrievalQA pipeline

@app.post("/qa")
async def qa_endpoint(document: UploadFile, questions: UploadFile):
    """
    Accepts two uploads:
      - Knowledge base: a .pdf or .json file containing reference material
      - Questions: a .json file with {"questions": ["q1", "q2", ...]}

    Returns factual, context-grounded answers using a hybrid
    LangChain RetrievalQA pipeline (FAISS + BM25 + LLM).
    """

    # Step 1: Validate input file types
    if not document or not questions:
        raise HTTPException(status_code=400, detail="Both document and questions files are required.")

    doc_suffix = os.path.splitext(document.filename)[1]
    q_suffix = os.path.splitext(questions.filename)[1]

    if doc_suffix.lower() not in [".pdf", ".json"]:
        raise HTTPException(status_code=400, detail="Knowledge base must be a .pdf or .json file.")
    if q_suffix.lower() != ".json":
        raise HTTPException(status_code=400, detail="Questions file must be a .json file.")

    try:
        # Step 2: Write uploaded files to temporary storage
        # (ensures compatibility with file loaders that expect file paths)
        with tempfile.NamedTemporaryFile(delete=False, suffix=doc_suffix) as temp_doc, \
             tempfile.NamedTemporaryFile(delete=False, suffix=q_suffix) as temp_q:
            shutil.copyfileobj(document.file, temp_doc)
            shutil.copyfileobj(questions.file, temp_q)

        # Step 3: Parse and chunk the knowledge base
        docs = load_documents(temp_doc.name)
        if not docs:
            raise HTTPException(status_code=400, detail="No documents could be loaded from the knowledge base.")
        print(f"✅ Loaded {len(docs)} chunks from {document.filename}")

        # Step 4: Initialize retriever and QA chain
        retriever = build_retriever(docs)
        qa_chain = build_qa_chain(retriever)

        # Step 5: Parse the questions file
        with open(temp_q.name, "r") as f:
            questions_json = json.load(f)

        if "questions" not in questions_json or not isinstance(questions_json["questions"], list):
            raise HTTPException(status_code=400, detail="Invalid questions.json: must contain a 'questions' list.")

        # Step 6: Run inference for each question
        results = []
        for idx, q in enumerate(questions_json["questions"], start=1):
            q = q.strip()
            if not q:
                continue

            print(f"\n🔍 Processing Q{idx}: {q}")
            try:
                result = qa_chain.invoke({"query": q})
                answer = result.get("result", "").strip() or "No answer generated."
            except Exception as e:
                traceback.print_exc()
                answer = f"Error during QA execution: {str(e)}"

            results.append({"question": q, "answer": answer})

        # Step 7: Return structured output
        return {"answers": results}

    except HTTPException:
        # Allow explicit FastAPI errors to propagate cleanly
        raise
    except Exception as e:
        # Catch unexpected exceptions and return a clean 500 response
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

    finally:
        # Step 8: Clean up temporary files
        try:
            if "temp_doc" in locals() and os.path.exists(temp_doc.name):
                os.remove(temp_doc.name)
            if "temp_q" in locals() and os.path.exists(temp_q.name):
                os.remove(temp_q.name)
        except Exception:
            # Avoid secondary errors during cleanup
            pass
