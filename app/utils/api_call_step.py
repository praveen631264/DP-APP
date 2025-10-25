import logging
import requests
import dpath
import jmespath
import base64
from .base_step import PlaybookStep
from .playbook_utils import render_template

logger = logging.getLogger(__name__)

class ApiCallStep(PlaybookStep):
    """
    A powerful, intelligent, and generic playbook step to make external API calls.

    This step is highly flexible and intelligent:
    - Secure Secret Management: Fetches credentials (API keys, passwords) from a
      secure 'secrets' store instead of hard-coding them in playbooks.
    - Advanced Authentication: Natively handles Bearer Token and Basic Auth.
    - Dynamic Templating: Uses the `render_template` utility to build the URL,
      headers, and body from the playbook context.
    - Intelligent Response Mapping: Uses JMESPath expressions to precisely extract
      and map data from the API response into the playbook context.
    """
    def execute(self, step_config: dict, context: dict, db, doc_id: str, playbook_executor):
        # --- 1. Fetch Secrets and Build Enriched Context ---
        secret_names = step_config.get('secrets', [])
        secrets = {name: db.get_secret(name) for name in secret_names}
        if any(value is None for value in secrets.values()):
            missing = [name for name, value in secrets.items() if value is None]
            raise ValueError(f"ApiCallStep failed: The following secrets could not be found: {missing}")

        # Create a temporary context for rendering that includes the fetched secrets
        render_context = {**context, "secrets": secrets}

        # --- 2. Get Configuration and Render All Templates ---
        url = render_template(step_config.get('url'), render_context)
        method = step_config.get('method', 'POST').upper()
        headers_template = step_config.get('headers_template', {})
        body_template = step_config.get('body_template', {})
        auth_config = step_config.get('auth', {})
        response_mapping = step_config.get('response_mapping') # JMESPath mapping

        if not url or not response_mapping:
            msg = "ApiCallStep requires 'url' and 'response_mapping' in its configuration."
            logger.error(msg)
            raise ValueError(msg)

        headers = render_template(headers_template, render_context)
        body = render_template(body_template, render_context)

        # --- 3. Handle Authentication ---
        self._apply_authentication(headers, auth_config, render_context)
        
        logger.info(f"Executing ApiCallStep '{step_config.get('name')}': {method} to {url}")

        # --- 4. Execute API Call ---
        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                json=body if method not in ['GET', 'DELETE'] else None,
                timeout=30
            )
            response.raise_for_status()

            # --- 5. Process and Map Response using JMESPath ---
            raw_response_data = {
                "status_code": response.status_code,
                "body": response.json() if response.content else {},
                "headers": dict(response.headers)
            }

            for output_key, jmespath_expr in response_mapping.items():
                try:
                    # Use JMESPath to find and extract the desired data
                    mapped_value = jmespath.search(jmespath_expr, raw_response_data)
                    dpath.new(context, f"outputs.{output_key}", mapped_value)
                    logger.info(f"Mapped API response via '{jmespath_expr}' to 'outputs.{output_key}'.")
                except Exception as jmes_e:
                    logger.error(f"JMESPath expression '{jmespath_expr}' failed: {jmes_e}", exc_info=True)
                    raise ValueError(f"Invalid JMESPath expression: {jmespath_expr}")

            logger.info(f"ApiCallStep '{step_config.get('name')}' completed successfully.")

        except requests.exceptions.RequestException as e:
            logger.error(f"ApiCallStep failed: {e}", exc_info=True)
            raise

    def _apply_authentication(self, headers: dict, auth_config: dict, render_context: dict):
        """
        Modifies the headers dictionary to apply authentication based on the step's
        auth configuration.
        """
        auth_type = auth_config.get('type')
        if not auth_type:
            return

        logger.info(f"Applying '{auth_type}' authentication.")

        if auth_type == 'bearer_token':
            token_template = auth_config.get('token')
            if not token_template:
                raise ValueError("Bearer token auth is missing the 'token' template.")
            
            token = render_template(token_template, render_context)
            headers['Authorization'] = f"Bearer {token}"

        elif auth_type == 'basic_auth':
            user_template = auth_config.get('username')
            pass_template = auth_config.get('password')
            if not user_template or not pass_template:
                raise ValueError("Basic auth is missing 'username' or 'password' templates.")

            username = render_template(user_template, render_context)
            password = render_template(pass_template, render_context)
            
            credentials = f"{username}:{password}".encode('utf-8')
            encoded_credentials = base64.b64encode(credentials).decode('utf-8')
            headers['Authorization'] = f"Basic {encoded_credentials}"

        else:
            raise ValueError(f"Unsupported authentication type: '{auth_type}'")