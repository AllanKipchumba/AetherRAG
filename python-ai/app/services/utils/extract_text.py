# import os
# import fitz  
# import docx  
# import textract

# def extract_text_from_file(file_path: str) -> str:
#     ext = os.path.splitext(file_path)[-1].lower()
    
#     if ext == ".pdf":
#         return extract_text_from_pdf(file_path)
#     elif ext == ".docx":
#         return extract_text_from_docx(file_path)
#     elif ext == ".doc":
#         return extract_text_from_doc(file_path)  # fallback to antiword or similar
#     else:
#         raise ValueError(f"Unsupported file type: {ext}")

# def extract_text_from_pdf(file_path: str) -> str:
#     doc = fitz.open(file_path)
#     return "\n".join(page.get_text() for page in doc)

# def extract_text_from_docx(file_path: str) -> str:
#     doc = docx.Document(file_path)
#     return "\n".join(paragraph.text for paragraph in doc.paragraphs)

# def extract_text_from_doc(file_path: str) -> str:
#     return textract.process(file_path).decode("utf-8")
