import pytest
from app.services import loader
from langchain_core.documents import Document


def test_pdf_loading(monkeypatch, tmp_path):
    """
    Verifies that load_documents() correctly processes a PDF file.
    Instead of parsing a real PDF, we mock PyPDFLoader.load()
    to return a valid Document object so the splitter logic can run.
    """

    # Create a temporary fake PDF file
    fake_pdf = tmp_path / "fake.pdf"
    fake_pdf.write_bytes(b"%PDF-1.4\nFake minimal PDF content\n%%EOF")

    # Mock out PyPDFLoader.load() to skip actual parsing
    monkeypatch.setattr(
        "app.services.loader.PyPDFLoader.load",
        lambda self: [Document(page_content="Hello from PDF", metadata={"source": str(fake_pdf)})],
    )

    # Run loader and verify output
    docs = loader.load_documents(str(fake_pdf))

    # Basic structure checks
    assert isinstance(docs, list)
    assert len(docs) == 1
    assert docs[0].page_content == "Hello from PDF"
    assert "source" in docs[0].metadata


@pytest.mark.parametrize("bad_ext", [".txt", ".csv", ".docx"])
def test_unsupported_file_type(tmp_path, bad_ext):
    """
    Confirms that load_documents() fails cleanly for unsupported file types.
    """

    fake_file = tmp_path / f"fake{bad_ext}"
    fake_file.write_text("Test document content.")

    # Expect a ValueError for invalid extensions
    with pytest.raises(ValueError, match="Unsupported file type"):
        loader.load_documents(str(fake_file))
