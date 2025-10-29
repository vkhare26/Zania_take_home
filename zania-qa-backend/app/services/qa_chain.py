import os
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import (
    EnsembleRetriever,
    MultiQueryRetriever,
    ContextualCompressionRetriever,
)
from langchain.retrievers.document_compressors.chain_extract import LLMChainExtractor
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# Load environment variables from .env at startup
load_dotenv()


# Compliance-aware QA prompt — tuned for concise, evidence-based answers

QA_TEMPLATE = """
You are a senior GRC (Governance, Risk, and Compliance) analyst.

Use ONLY the retrieved context below to answer the question factually and concisely.
If the context provides partial information, summarize clearly what is known and what is missing.
Quote or paraphrase relevant sentences when possible.
If absolutely no relevant details are found, respond with:
"Information not found in the provided document."

Context:
{context}

Question: {question}

Answer:
"""


# Domain synonym expansion prompt for more robust query matching

SYNONYM_PROMPT = """
You are a compliance and cybersecurity subject-matter expert.
Rewrite the user's question into 3–5 semantically equivalent forms that might match
different phrasing in SOC 2, ISO 27001, or GRC documentation.

Expand terminology and include domain synonyms:
- "personal information" ↔ "customer data" / "PII" / "user data"
- "third parties" ↔ "vendors" / "subprocessors" / "external providers"
- "incident notification" ↔ "security event disclosure" / "breach communication"
- "cloud provider" ↔ "hosting provider" / "infrastructure provider"
- "data center location" ↔ "hosting region" / "infrastructure region"

Return only the rewritten queries, one per line, with no explanation.

User question:
{question}
"""


def build_retriever(docs):
    """
    Constructs a hybrid retriever that blends:
      • FAISS for semantic similarity
      • BM25 for keyword precision
      • MultiQuery rewriting for domain-aware phrasing
      • LLM-based compression for tighter context
    """

    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise ValueError("❌ Missing OPENAI_API_KEY. Please set it in your .env file or environment.")

    # Step 1: Create embeddings using OpenAI’s latest text-embedding model
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-large",
        openai_api_key=openai_key,
    )

    # Step 2: Initialize FAISS vector store (fast, in-memory similarity search)
    vectorstore = FAISS.from_documents(docs, embedding=embeddings)
    semantic_retriever = vectorstore.as_retriever(
        search_kwargs={
            "k": 25,           # number of top results returned
            "fetch_k": 80,     # broader candidate pool for reranking
            "score_threshold": 0.1,
        }
    )

    # Step 3: Keyword-based BM25 retriever for exact term recall
    keyword_retriever = BM25Retriever.from_documents(docs)

    # Step 4: Combine semantic + keyword retrievers for balanced recall/precision
    base_retriever = EnsembleRetriever(
        retrievers=[keyword_retriever, semantic_retriever],
        weights=[0.4, 0.6],  # small bias toward semantic matching
    )

    # Step 5: Expand user queries via LLM to catch domain-specific phrasing
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=openai_key)
    multiquery_prompt = PromptTemplate(input_variables=["question"], template=SYNONYM_PROMPT)
    multiquery_retriever = MultiQueryRetriever.from_llm(
        retriever=base_retriever,
        llm=llm,
        include_original=True,
        prompt=multiquery_prompt,
    )

    # Helper for quick debugging during development
    def debug_multiquery(question: str):
        """Prints out the generated query variants for inspection."""
        from langchain_core.output_parsers import StrOutputParser
        chain = multiquery_prompt | llm | StrOutputParser()
        rewrites = chain.invoke({"question": question})
        print("\n🧠 [MultiQuery Expansion Preview]")
        print(rewrites)
        print("-" * 60)

    

    # Step 6: Add contextual compression — extracts only the relevant parts of long chunks
    compressor_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=openai_key)
    compressor = LLMChainExtractor.from_llm(compressor_llm)
    retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=multiquery_retriever,
    )

    print("Hybrid retriever initialized (FAISS + BM25 + Synonym MultiQuery + Compression)")
    return retriever


def build_qa_chain(retriever):
    """
    Creates the main RetrievalQA chain that ties the retriever to an LLM.
    Designed for compliance-focused, source-grounded answers.
    """

    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise ValueError("Missing OPENAI_API_KEY. Please set it in your .env file or environment.")

    # Use the tuned compliance prompt to keep answers factual and narrow
    prompt = PromptTemplate(input_variables=["context", "question"], template=QA_TEMPLATE)

    # Initialize the same lightweight GPT model used in retrieval
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=openai_key)

    # Build the RetrievalQA chain — combines retrieval + LLM completion
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",           # simple context concatenation
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True, # useful for debugging / transparency
        verbose=False,
    )

    print("QA Chain initialized with tuned prompt and hybrid retriever.")
    return qa_chain
