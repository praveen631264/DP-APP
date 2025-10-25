import logging
from .base_step import PlaybookStep
from app.ai_models import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .playbook_utils import render_template
import dpath

logger = logging.getLogger(__name__)

class LLMPromptStep(PlaybookStep):
    """
    A playbook step that executes a prompt against the LLM.
    It can use values from the context to format the prompt.
    """
    def execute(self, step_config: dict, context: dict, db, doc_id: str, playbook_executor):
        prompt_template = step_config.get('prompt')
        output_key = step_config.get('output_key')

        if not prompt_template or not output_key:
            logger.error("LLMPromptStep is missing 'prompt' or 'output_key' in its configuration.")
            return

        # Format the prompt using data from the context
        # This allows chaining steps, e.g., using the output of a previous step.
        formatted_prompt = render_template(prompt_template, context)

        llm = get_llm()
        prompt = ChatPromptTemplate.from_messages([("user", formatted_prompt)])
        chain = prompt | llm | StrOutputParser()

        logger.info(f"Executing LLM prompt for step '{step_config.get('name')}'.")
        
        # Use streaming for better performance and to prepare for future real-time UI updates.
        result_chunks = []
        for chunk in chain.stream({}):
            result_chunks.append(chunk)
        result = "".join(result_chunks)

        # Store the result in the context using the specified output key.
        # dpath allows for nested dictionary access, e.g., "invoice.total_amount"
        dpath.new(context, f"outputs.{output_key}", result)
        logger.info(f"LLM prompt step completed. Stored result in context at 'outputs.{output_key}'.")