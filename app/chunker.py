import io
from pypdf import PdfReader

def extract_text(file_bytes: bytes, filename: str) -> str:
    if filename.endswith('.pdf'):
        reader = PdfReader(io.BytesIO(file_bytes))
        pages_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)
        return "\n".join(pages_text)

    elif filename.endswith('.txt') or filename.endswith('.md'):
        return file_bytes.decode('utf-8')

    else:
        raise ValueError("Unsupported file format. Please upload a .pdf, .md , or .txt file")

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    if not text.strip():
        return []
    chunks = []
    step = chunk_size - overlap dd
    for i in range(0, len(text), step):
        chunk = text[i: i + chunk_size]
        chunks.append(chunk) 
    return chunks
        

