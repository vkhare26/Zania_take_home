from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from pathlib import Path
import json

def load_documents(file_path: str):
    """
    Load and preprocess documents from either a PDF or JSON file.
    Returns a list of LangChain Document objects ready for downstream retrieval.
    """
    path = Path(file_path)

    # Case 1: PDF documents (knowledge base or reference material)
    if path.suffix.lower() == ".pdf":
        # Use LangChain's PDF loader to extract text from all pages
        loader = PyPDFLoader(file_path)
        raw_docs = loader.load()

        # Split long text into overlapping chunks for better context retention
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=2500,
            chunk_overlap=400,
            length_function=len,
            separators=["\n\n", "\n", ".", " "],  # prefer splitting on paragraph or sentence breaks
        )
        docs = splitter.split_documents(raw_docs)

        # Add basic metadata for traceability
        for doc in docs:
            doc.metadata["source_type"] = "pdf"
            doc.metadata["file_name"] = path.name

        print(f"Loaded {len(docs)} chunks from {path.name}")
        return docs

    # Case 2: JSON input (either QA pairs or question lists)
    elif path.suffix.lower() == ".json":
        with open(file_path, "r") as f:
            data = json.load(f)

        docs = []
        # Handle list of {question, answer} dictionaries
        if isinstance(data, list) and all(isinstance(d, dict) for d in data):
            for d in data:
                q = d.get("question", "").strip()
                a = d.get("answer", "").strip()
                content = f"Question: {q}\nAnswer: {a}"
                docs.append(
                    Document(
                        page_content=content,
                        metadata={"source_type": "json_qa_pair"}
                    )
                )
        # Handle single dict with a "questions" key (plain question list)
        elif isinstance(data, dict) and "questions" in data:
            for q in data["questions"]:
                docs.append(
                    Document(
                        page_content=q,
                        metadata={"source_type": "json_questions"}
                    )
                )
        return docs

    # Unsupported file types
    else:
        raise ValueError("Unsupported file type: must be .pdf or .json")
