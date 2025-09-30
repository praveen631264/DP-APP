import io
import json
import logging
import openpyxl
import docx
import os
from PyPDF2 import PdfReader
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_models import ChatOllama

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

def get_kvps_and_category(text: str, examples: list = []):
    """
    Extracts Key-Value Pairs (KVPs) and determines a category from the text,
    guided by provided examples.
    """
    logger.info("Initializing local LLM call to extract KVPs and category.")

    if not text or not text.strip():
        logger.warning("Input text is empty. Skipping LLM call.")
        return {}, None

    # --- Construct the System Prompt ---
    system_prompt = """You are an expert document analysis AI. Your task is to analyze the user's document text and perform two actions:
1.  **Categorize the Document**: Classify the document into a relevant category.
2.  **Extract Key-Value Pairs (KVPs)**: Identify and extract important information from the document as key-value pairs.

You MUST return the output as a single, valid JSON object with two keys: 'category' and 'kvps'. The 'kvps' value must be a JSON object itself. Do not provide any other text, explanation, or markdown formatting."""

    # --- Inject Fine-Tuning Examples into the Prompt ---
    if examples:
        example_str = "\n\nHere are some examples of how to categorize documents correctly:\n"
        for ex in examples:
            # We truncate the example text to keep the prompt concise
            truncated_text = (ex['text'][:200] + '...') if len(ex['text']) > 200 else ex['text']
            example_str += f"- Document text starting with: '{truncated_text}' should be categorized as '{ex['category']}'.\n"
        
        system_prompt += example_str
    
    system_prompt += """\n\nNow, analyze the following document. Remember to only return the final JSON object.

Example output format:
{
  "category": "Invoice",
  "kvps": {
    "invoice_number": "INV-12345",
    "customer_name": "John Doe",
    "total_amount": "500.00"
  }
}"""

    # --- LLM and Prompt Configuration ---

    try:
        # Connect to the local LLM using Ollama
        llm = ChatOllama(
            base_url=os.environ.get("OLLAMA_BASE_URL"),
            model=os.environ.get("CHAT_MODEL_NAME", "phi3:mini"),
            temperature=0
        )
    except Exception as e:
        logger.error(f"Failed to initialize the Ollama LLM. Ensure Ollama is running and accessible. Error: {e}", exc_info=True)
        raise ConnectionError("Could not connect to the local AI model via Ollama.") from e

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", "{input_text}"),
        ]
    )

    chain = prompt | llm | StrOutputParser()

    # --- Invoke the Chain and Parse the Output ---
    logger.info("Invoking local LLM chain for analysis...")
    try:
        llm_response = chain.invoke({"input_text": text})
        logger.debug(f"Raw LLM response: {llm_response}")
        
        # Clean the response to ensure it's valid JSON
        # Local models sometimes add extra text or formatting
        if "```json" in llm_response:
            llm_response = llm_response.split("```json")[1].split("```")[0]
        
        result = json.loads(llm_response)
        kvps = result.get("kvps", {})
        category = result.get("category")

        if not isinstance(kvps, dict):
            logger.warning("LLM output for 'kvps' was not a dictionary. Defaulting to empty.")
            kvps = {}

        logger.info(f"LLM analysis successful. Suggested Category='{category}'.")
        return kvps, category

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response from LLM: {e}", exc_info=True)
        logger.error(f"Problematic LLM Output: {llm_response}")
        raise ValueError("LLM returned malformed JSON.") from e
    except Exception as e:
        logger.error(f"An unexpected error occurred during LLM chain invocation: {e}", exc_info=True)
        raise