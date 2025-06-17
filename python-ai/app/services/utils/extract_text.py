import fitz  # PyMuPDF
import logging

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from PDF using PyMuPDF.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        str: Extracted text content
        
    Raises:
        Exception: If PDF cannot be processed
    """
    doc = None
    try:
        doc = fitz.open(file_path)
        text = ""
        
        for page_num, page in enumerate(doc, 1):
            page_text = page.get_text()
            if page_text.strip():  # Only add non-empty pages
                text += page_text + "\n"
        
        if not text.strip():
            raise Exception("No text content found in PDF")
            
        return text.strip()
        
    except Exception as e:
        logger.error(f"Failed to extract text from PDF {file_path}: {e}")
        raise Exception(f"PDF text extraction failed: {e}")
    finally:
        if doc:
            doc.close()