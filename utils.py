
import json
import requests
import time # For simulation

def test_api_push_config(api_config, context):
    # ... (code remains the same)
    pass

def test_send_message_config(service_config, context):
    """
    Executes a REAL messaging API call for live testing from the UI.
    This function simulates the calls but shows how it would be structured.
    """
    provider = service_config["provider"]
    details = service_config["message_details"]

    # 1. Fully render the message details with the provided test context
    try:
        rendered_details_str = json.dumps(details).format(**context)
        rendered_details = json.loads(rendered_details_str)
        
        # Securely get credentials from context
        auth_creds = context.get('secrets', {})

    except KeyError as e:
        return {"status_code": 400, "body": {"error": f"Missing key in context: {str(e)}"}}

    # 2. --- EXECUTE REAL API CALL (SIMULATED FOR THIS EXAMPLE) ---
    print(f"--- Live Testing Message ---")
    print(f"Provider: {provider}")
    print(f"Details: {rendered_details}")
    print(f"Using Credentials: { {k: '********' for k in auth_creds.keys()} }") # Mask secrets in log

    try:
        # In a real implementation, you would use provider-specific SDKs here.
        # e.g., for Twilio: from twilio.rest import Client
        #      client = Client(auth_creds['TWILIO_ACCOUNT_SID'], auth_creds['TWILIO_AUTH_TOKEN'])
        #      message = client.messages.create(...)

        time.sleep(1.5) # Simulate network latency

        if provider not in ["email", "twilio_sms", "telegram"]:
             raise ValueError(f"Provider '{provider}' is not supported for live testing.")

        # Simulate a generic success response
        mock_api_response = {
            "id": f"test_{int(time.time())}",
            "status": "SUCCESS",
            "info": f"Message successfully sent via {provider} (SIMULATED)"
        }

        return {
            "status_code": 200,
            "body": mock_api_response
        }

    except Exception as e:
        # Handle real API errors (e.g., authentication failure, invalid number)
        return {
            "status_code": 500,
            "body": {"error": "API call failed", "details": str(e)}
        }

def test_api_push_config(api_config, context):
    """
    Executes a REAL API call based on a playbook step configuration and returns the raw response.
    This is used for live testing from the UI.
    """
    # 1. Format URL, headers, and payload from the provided context
    url = api_config["url_template"].format(**context)
    
    headers = {k: str(v).format(**context) for k, v in api_config.get("headers", {}).items()}
    
    payload_str = json.dumps(api_config.get("payload_template", {}))
    payload_str = payload_str.format(**context)
    payload = json.loads(payload_str)

    # 2. Execute the real API request using the 'requests' library
    try:
        response = requests.request(
            method=api_config['method'],
            url=url,
            headers=headers,
            json=payload if api_config['method'] in ['POST', 'PUT'] else None,
            timeout=10 # 10-second timeout
        )
        
        # 3. Attempt to parse JSON body, fall back to raw text
        try:
            response_body = response.json()
        except ValueError:
            response_body = response.text

        # 4. Return a serializable summary of the response
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response_body
        }

    except requests.exceptions.RequestException as e:
        # Handle network errors (DNS, connection refused, timeout, etc.)
        return {
            "status_code": 500,
            "body": {"error": "Request failed", "details": str(e)}
        }
