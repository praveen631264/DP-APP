import logging
import json
import dpath
from .base_step import PlaybookStep
from .playbook_utils import _get_value_from_context

logger = logging.getLogger(__name__)

class JsonParseStep(PlaybookStep):
    """
    An intelligent utility step to parse a JSON string from the playbook context
    and store the resulting object back into the context.

    This is extremely useful for processing the string output of an LLMPromptStep
    that was instructed to return JSON, making the structured data available
    to subsequent steps.
    """
    def execute(self, step_config: dict, context: dict, db, doc_id: str, playbook_executor):
        input_path = step_config.get('input_path')
        output_key = step_config.get('output_key')

        if not input_path or not output_key:
            logger.error("JsonParseStep is missing 'input_path' or 'output_key'.")
            raise ValueError("JsonParseStep requires 'input_path' and 'output_key'.")

        # Retrieve the string value from the context using its dot-notation path
        json_string = _get_value_from_context(input_path, context)

        if not isinstance(json_string, str):
            logger.error(f"Input for JsonParseStep at '{input_path}' is not a string.")
            raise TypeError(f"Expected a string at '{input_path}', but found {type(json_string)}.")

        try:
            parsed_data = json.loads(json_string)
            dpath.new(context, f"outputs.{output_key}", parsed_data)
            logger.info(f"Successfully parsed JSON and stored it at 'outputs.{output_key}'.")
        except json.JSONDecodeError as e:
            logger.error(f"JsonParseStep failed: Invalid JSON string provided. Error: {e}", exc_info=True)
            raise