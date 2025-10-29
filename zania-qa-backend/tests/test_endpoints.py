from fastapi.testclient import TestClient
from app.main import app
import io, json

# Create a test client for the FastAPI app
client = TestClient(app)

# Minimal valid PDF bytes — just enough for PyPDF to recognize it as a PDF
VALID_PDF_BYTES = (
    b"%PDF-1.4\n"
    b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] /Contents 4 0 R >>\nendobj\n"
    b"4 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 72 712 Td (Hello PDF!) Tj ET\nendstream\nendobj\n"
    b"xref\n0 5\n0000000000 65535 f \n0000000010 00000 n \n0000000079 00000 n \n0000000147 00000 n \n0000000276 00000 n \n"
    b"trailer\n<< /Root 1 0 R /Size 5 >>\nstartxref\n394\n%%EOF"
)


def test_missing_files():
    """Should return 400 or 422 if required files are missing."""
    response = client.post("/qa")
    assert response.status_code in (400, 422)


def test_valid_request(monkeypatch):
    """
    Full integration-style test for the /qa endpoint.
    Mocks the heavy LangChain components to focus on request handling.
    """

    # Mock dependencies to avoid actual OpenAI / FAISS calls
    def mock_load(_):
        return [{"page_content": "fake content", "metadata": {"source_type": "pdf"}}]

    def mock_build_retriever(_):
        return "mock_retriever"

    class DummyChain:
        def invoke(self, q):
            return {"result": "mock answer"}

    def mock_build_chain(_):
        return DummyChain()

    monkeypatch.setattr("app.main.load_documents", mock_load)
    monkeypatch.setattr("app.main.build_retriever", mock_build_retriever)
    monkeypatch.setattr("app.main.build_qa_chain", mock_build_chain)

    # Prepare valid test files (PDF + questions JSON)
    doc = io.BytesIO(VALID_PDF_BYTES)
    q = io.BytesIO(json.dumps({"questions": ["Example question"]}).encode())

    # Send request to /qa endpoint
    resp = client.post(
        "/qa",
        files={
            "document": ("a.pdf", doc, "application/pdf"),
            "questions": ("b.json", q, "application/json"),
        },
    )

    # Validate response structure
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "answers" in data
    assert data["answers"][0]["answer"] == "mock answer"
