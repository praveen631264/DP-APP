from ctransformers import AutoModelForCausalLM
from pypdf import PdfReader
from docx import Document
import threading
from app import document_categories # Import the centralized categories

# A lock to ensure that the model is loaded only once
model_lock = threading.Lock()
llm = None

def get_llm():
    """
    Loads the quantized language model into memory. 
    This function is thread-safe and ensures the model is loaded only once.
    """
    global llm
    with model_lock:
        if llm is None:
            # Download the model from Hugging Face Hub
            # Using a smaller, quantized model for CPU execution
            llm = AutoModelForCausalLM.from_pretrained(
                "TheBloke/Mistral-7B-Instruct-v0.1-GGUF", 
                model_file="mistral-7b-instruct-v0.1.Q4_K_M.gguf", 
                model_type="mistral",
                gpu_layers=0  # Set to 0 to force CPU execution
            )
    return llm

def extract_text_from_pdf(filepath):
    """Extracts text from a PDF file."""
    reader = PdfReader(filepath)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def extract_text_from_docx(filepath):
    """Extracts text from a DOCX file."""
    doc = Document(filepath)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def process_document_with_llm(document):
    """
    Processes a document using the local LLM to classify it and extract KVPs.
    """
    llm = get_llm()
    filepath = document['path']
    
    # 1. Extract text from the document
    if filepath.endswith('.pdf'):
        text = extract_text_from_pdf(filepath)
    elif filepath.endswith('.docx'):
        text = extract_text_from_docx(filepath)
    else:
        # For images, you would need an OCR library like Tesseract.
        # This is a placeholder for now.
        text = "Image content would be extracted here."

    # 2. Classify the document using the dynamic category list
    category_list = ", ".join(document_categories)
    classification_prompt = f"""Classify the following document text into one of these categories: {category_list}. 
    Text: {text}
    Category:"""
    category = llm(classification_prompt)

    # 3. Extract Key-Value Pairs
    kvp_prompt = f"""Based on the text of the document, which is a {category}, extract the key-value pairs. 
    Text: {text}
    Key-Value Pairs:"""
    kvps = llm(kvp_prompt)

    return {
        "category": category.strip(),
        "kvps": kvps.strip(),
        "status": "Extraction Complete",
        "text": text
    }
