import aiohttp
import os
from sentence_transformers import SentenceTransformer
from chromadb import PersistentClient

# Initialize the embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Initialize local ChromaDB client (new API)
chroma_client = PersistentClient(path="./chromadb")
collection = chroma_client.get_or_create_collection(name="document_embeddings")

async def download_document(url: str) -> str:
    filename = url.split("?")[0].split("/")[-1]
    file_path = os.path.join("/tmp", filename)

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                with open(file_path, 'wb') as f:
                    f.write(await resp.read())
                return file_path
            else:
                raise Exception(f"Failed to download document: {resp.status}")

def extract_text_from_pdf(file_path: str) -> str:
    import fitz  # PyMuPDF
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text
