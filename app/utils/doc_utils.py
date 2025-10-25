import io
import json
import logging
import openpyxl
import docx
import os
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_models import ChatOllama

logger = logging.getLogger(__name__)

# --- Text Extraction Functions ---

def extract_text(file_content, content_type):
    """
    Extracts text from a document's byte content based on its MIME type.
    """
    logger.info(f"Extracting text for content type: {content_type}")
    text = ""
    try:
        file_stream = io.BytesIO(file_content)
        
        if "pdf" in content_type:
            reader = PdfReader(file_stream)
            for page in reader.pages:
                text += page.extract_text() or ""
        elif "vnd.openxmlformats-officedocument.wordprocessingml.document" in content_type: # .docx
            doc = docx.Document(file_stream)
            for para in doc.paragraphs:
                text += para.text + "\n"
        elif "vnd.openxmlformats-officedocument.spreadsheetml.sheet" in content_type: # .xlsx
            workbook = openpyxl.load_workbook(file_stream)
            for sheet_name in workbook.sheetnames:
                sheet = workbook[sheet_name]
                for row in sheet.iter_rows():
                    for cell in row:
                        if cell.value:
                            text += str(cell.value) + " "
                    text += "\n"
        elif "text" in content_type:
            text = file_content.decode('utf-8', errors='ignore')
        else:
            logger.warning(f"Unsupported content type for text extraction: {content_type}. Trying plain text decode.")
            text = file_content.decode('utf-8', errors='ignore')

    except Exception as e:
        logger.error(f"Error extracting text for content_type {content_type}: {e}", exc_info=True)
        return "" 

    if not text.strip():
        logger.warning(f"Could not extract any text for content_type: {content_type}")

    return text.strip()


# --- AI-Powered Extraction and Routing Functions ---

def route_to_category(text: str, all_categories: list, llm: ChatOllama) -> str:
    """
    Uses a lightweight prompt to quickly classify a document into a category.
    This acts as the "Head Chef" or router for the Mixture-of-Experts architecture.
    """
    logger.info("Routing document to category...")
    if not text or not text.strip():
        logger.warning("Input text is empty. Cannot route.")
        return "Uncategorized"

    category_list = ", ".join(all_categories)
    system_prompt = f"""You are an expert document classifier. Your only task is to classify the document text into one of the following categories: [{category_list}].
You MUST return only the single, most appropriate category name from the list and nothing else. If no category fits, return "Uncategorized"."""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", "{input_text}"),
        ]
    )
    chain = prompt | llm | StrOutputParser()

    try:
        logger.info("Invoking router LLM for classification...")
        # Truncate input text for speed, as routing doesn't need the full document.
        llm_response = chain.invoke({"input_text": text[:4000]})
        
        # Basic cleaning of the model's output
        category = llm_response.strip().replace("\"", "").replace("'", "")

        if category not in all_categories:
            logger.warning(f"Router LLM returned a category '{category}' not in the approved list. Defaulting to Uncategorized.")
            return "Uncategorized"
        
        logger.info(f"Document successfully routed to category: '{category}'")
        return category

    except Exception as e:
        logger.error(f"An error occurred during routing: {e}", exc_info=True)
        return "Uncategorized"

def extract_kvps(text: str, extraction_prompt: str, llm: ChatOllama) -> dict:
    """
    Extracts Key-Value Pairs (KVPs) from text using a specific, provided prompt.
    """
    logger.info("Extracting KVPs with a specific prompt...")
    if not text or not text.strip():
        logger.warning("Input text is empty. Skipping LLM call.")
        return {}

    system_prompt = f"""{extraction_prompt}

You MUST return the output as a single, valid JSON object. Do not provide any other text, explanation, or markdown formatting.

Example output format:
{{
  "invoice_number": "INV-12345",
  "customer_name": "John Doe",
  "total_amount": "500.00"
}}"""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", "{input_text}"),
        ]
    )
    chain = prompt | llm | StrOutputParser()

    # --- Invoke the Chain and Parse the Output ---
    logger.info("Invoking LLM chain for KVP extraction...")
    try:
        llm_response = chain.invoke({"input_text": text})
        logger.debug(f"Raw LLM response: {llm_response}")
        
        # Clean the response to ensure it's valid JSON
        # Local models sometimes add extra text or formatting
        if "```json" in llm_response:
            llm_response = llm_response.split("```json")[1].split("```")[0]
        
        result = json.loads(llm_response)

        if not isinstance(result, dict):
            logger.warning("LLM output was not a dictionary. Defaulting to empty.")
            return {}

        logger.info(f"LLM KVP extraction successful. Found {len(result)} pairs.")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response from LLM: {e}", exc_info=True)
        logger.error(f"Problematic LLM Output: {llm_response}")
        raise ValueError("LLM returned malformed JSON.") from e
    except Exception as e:
        logger.error(f"An unexpected error occurred during LLM chain invocation: {e}", exc_info=True)
        raise

# --- Text Splitting Functions ---

def split_text_into_chunks(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
    """
    Splits a long text into smaller, overlapping chunks.
    """
    if not text:
        return []
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    
    chunks = text_splitter.split_text(text)
    logger.info(f"Split text into {len(chunks)} chunks.")
    return chunks

def summarize_text_for_embedding(text: str, llm: ChatOllama) -> str:
    """
    Uses the LLM to create a detailed summary of the text.
    The goal is to capture all key concepts for effective embedding.
    """
    if not text or not text.strip():
        logger.warning("Input text is empty. Cannot summarize.")
        return ""

    system_prompt = """You are a highly skilled summarization AI. Your task is to create a detailed, comprehensive summary of the provided text.
The summary must be dense and include all key topics, names, dates, figures, and conclusions mentioned in the original document.
The purpose of this summary is to be used for semantic search, so do not leave out important details.
Return only the summary text and nothing else."""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", "{input_text}"),
        ]
    )
    chain = prompt | llm | StrOutputParser()

    try:
        logger.info("Invoking LLM to summarize text for embedding...")
        summary = chain.invoke({"input_text": text})
        logger.info(f"Successfully generated a summary of length {len(summary)} for embedding.")
        return summary
    except Exception as e:
        logger.error(f"An error occurred during summarization: {e}", exc_info=True)
        return "" # Return empty string on failure