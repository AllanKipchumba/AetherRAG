from embedding_service import download_document, extract_text_from_pdf, embedding_model, collection

async def process_embedding(url: str, doc_id: str):
    try:
        file_path = await download_document(url)
        text = extract_text_from_pdf(file_path)
        embedding = embedding_model.encode(text)

        # Store in ChromaDB
        collection.add(
            documents=[text],
            embeddings=[embedding.tolist()],
            ids=[doc_id],
            metadatas=[{"source": "kafka", "filename": doc_id}]
        )

        print(f"[+]Embedding for {doc_id} stored successfully.")

    except Exception as e:
        print(f"[-]Error processing embedding: {e}")
