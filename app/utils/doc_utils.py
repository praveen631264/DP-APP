import io
import json
import logging
import openpyxl
import docx
from PyPDF2 import PdfReader
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI # Example provider

logger = logging.getLogger(__name__)

# --- Text Extraction Functions ---

def get_doc_text(file_content, content_type):
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


# --- AI-Powered Extraction Functions ---

def get_kvps_and_category(text: str):
    """
    Extracts Key-Value Pairs (KVPs) and determines a category from the text
    by calling a Large Language Model (LLM).
    """
    logger.info("Initializing LLM call to extract KVPs and category.")

    if not text or not text.strip():
        logger.warning("Input text is empty. Skipping LLM call.")
        return {}, None

    # --- LLM and Prompt Configuration ---
    # NOTE: Replace 'ChatOpenAI' with your desired provider (e.g., ChatGooglePalm, ChatAnthropic).
    # Ensure you have set the required environment variables (e.g., OPENAI_API_KEY).
    try:
        llm = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0)
    except Exception as e:
        logger.error(f"Failed to initialize the LLM. Ensure your API key is set and the provider is available. Error: {e}", exc_info=True)
        # Fail gracefully if the LLM can't be loaded
        raise ConnectionError("Could not connect to the specified AI model provider.") from e

    # This prompt template instructs the LLM to act as a document analyzer
    # and return a JSON object with a specific structure.
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an expert document analysis AI. Your task is to analyze the user's document text and perform two actions:
1.  **Categorize the Document**: Classify the document into one of the following categories: 'Invoice', 'Contract', 'Resume', 'Purchase Order', or 'Unknown'.
2.  **Extract Key-Value Pairs (KVPs)**: Identify and extract important information from the document as key-value pairs.

You MUST return the output as a single, valid JSON object with two keys: 'category' and 'kvps'. The 'kvps' value must be a JSON object itself. Do not provide any other text, explanation, or markdown formatting.

Example output format:
{
  "category": "Invoice",
  "kvps": {
    "invoice_number": "INV-12345",
    "customer_name": "John Doe",
    "total_amount": "500.00"
  }
}
""",
            ),
            ("user", "{input_text}"),
        ]
    )

    # The chain combines the prompt, the LLM, and an output parser.
    chain = prompt | llm | StrOutputParser()

    # --- Invoke the Chain and Parse the Output ---
    logger.info("Invoking LLM chain for analysis...")
    try:
        llm_response = chain.invoke({"input_text": text})
        logger.debug(f"Raw LLM response: {llm_response}")
        
        # Parse the JSON string response from the LLM
        result = json.loads(llm_response)
        kvps = result.get("kvps", {})
        category = result.get("category", "Unknown")

        if not isinstance(kvps, dict):
            logger.warning("LLM output for 'kvps' was not a dictionary. Defaulting to empty.")
            kvps = {}

        logger.info(f"LLM analysis successful. Category='{category}'.")
        return kvps, category

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response from LLM: {e}", exc_info=True)
        logger.error(f"Problematic LLM Output: {llm_response}")
        raise ValueError("LLM returned malformed JSON.") from e
    except Exception as e:
        logger.error(f"An unexpected error occurred during LLM chain invocation: {e}", exc_info=True)
        raise
