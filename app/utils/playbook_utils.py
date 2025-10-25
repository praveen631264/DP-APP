import logging
import operator

logger = logging.getLogger(__name__)

def _flatten_context(context, parent_key='', sep='.'):
    """
    Flattens a nested dictionary for easy template replacement.
    e.g., context['document']['kvps']['invoice_id'] becomes 'document.kvps.invoice_id'
    """
    items = []
    for k, v in context.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_context(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def render_template(template, context):
    """
    Recursively renders a template (string, list, or dict) using the playbook context.
    Placeholders are in the format {key.subkey}.
    This is a more powerful renderer than standard string formatting.
    """
    if not template:
        return template

    if isinstance(template, str):
        # Flatten the context for easy replacement of nested keys
        flat_context = _flatten_context(context)
        # Use a simple but effective string replacement loop
        for key, value in flat_context.items():
            placeholder = f"{{{key}}}"
            # Ensure value is a string for replacement
            template = template.replace(placeholder, str(value))
        return template
    elif isinstance(template, dict):
        # Recursively render templates in dictionary values
        return {k: render_template(v, context) for k, v in template.items()}
    elif isinstance(template, list):
        # Recursively render templates in list items
        return [render_template(i, context) for i in template]
    else:
        # Return non-templatable types as is
        return template

def _get_value_from_context(path, context):
    """
    Safely retrieves a value from a nested context dictionary using dot notation.
    e.g., 'outputs.extracted_data.total_amount'
    """
    keys = path.split('.')
    value = context
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return None # Path is invalid
    return value

def evaluate_condition(condition_str, context):
    """
    Safely evaluates a simple condition string against the playbook context.
    Supports: ==, !=, >, <, >=, <=, contains
    Example: "outputs.invoice_details.total_amount > 10000"
    """
    ops = {
        '==': operator.eq, '!=': operator.ne,
        '>': operator.gt, '<': operator.lt,
        '>=': operator.ge, '<=': operator.le,
        'contains': operator.contains
    }

    try:
        for op_str, op_func in ops.items():
            if op_str in condition_str:
                variable_path, value_str = [part.strip() for part in condition_str.split(op_str, 1)]
                
                # Get the actual value from the context
                actual_value = _get_value_from_context(variable_path, context)

                # Strip quotes from the value string if they exist
                if value_str.startswith(("'", '"')) and value_str.endswith(("'", '"')):
                    value_str = value_str[1:-1]

                # Attempt to cast the condition value to the same type as the actual value
                if actual_value is not None:
                    try:
                        # Handle boolean strings explicitly
                        if isinstance(actual_value, bool):
                            condition_value = value_str.lower() in ('true', '1', 't', 'yes')
                        else:
                            condition_value = type(actual_value)(value_str)
                    except (ValueError, TypeError):
                        # If casting fails, compare as strings
                        condition_value = value_str
                    return op_func(actual_value, condition_value)
                else:
                    return False # Variable not found in context

        logger.warning(f"Condition '{condition_str}' is invalid or uses an unsupported operator.")
        return False
    except Exception as e:
        logger.error(f"Error evaluating condition '{condition_str}': {e}", exc_info=True)
        return False