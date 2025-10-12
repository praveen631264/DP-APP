
import requests
import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def _resolve_placeholders(payload, context):
    """Recursively resolve placeholders like {{variable}} in the payload."""
    if isinstance(payload, dict):
        return {k: _resolve_placeholders(v, context) for k, v in payload.items()}
    elif isinstance(payload, list):
        return [_resolve_placeholders(i, context) for i in payload]
    elif isinstance(payload, str):
        for key, value in context.items():
            payload = payload.replace(f"{{{{{key}}}}}", str(value))
    return payload

def _capture_from_response(response_body, capture_rules, context):
    """Capture values from the response body based on rules."""
    for key, path in capture_rules.items():
        parts = path.split('.')
        if parts[0] == 'body':
            current = response_body
            try:
                for part in parts[1:]:
                    current = current[part]
                context[key] = current
            except (KeyError, TypeError) as e:
                logger.warning(f"Could not capture {path}: {e}")

def run_e2e_tests(test_file='e2e_tests.json'):
    """Reads a test definition file and executes the E2E tests."""
    with open(test_file, 'r') as f:
        test_suite = json.load(f)

    base_url = test_suite['base_url']
    report = {
        "test_suite": test_suite['test_suite_name'],
        "run_timestamp": datetime.utcnow().isoformat(),
        "overall_status": "SUCCESS",
        "flows": []
    }
    context = {} # To hold captured variables

    for flow in test_suite['flows']:
        flow_report = {
            "flow_name": flow['flow_name'],
            "status": "SUCCESS",
            "steps": []
        }
        logger.info(f"--- Running Flow: {flow['flow_name']} ---")

        for step in flow['steps']:
            step_report = {
                "step_name": step['step_name'],
                "status": "FAILURE", # Default to failure
                "endpoint": step['endpoint'],
                "method": step['method']
            }
            
            endpoint = _resolve_placeholders(step['endpoint'], context)
            url = f"{base_url}{endpoint}"
            payload = _resolve_placeholders(step.get('payload'), context)

            try:
                response = requests.request(
                    method=step['method'],
                    url=url,
                    json=payload,
                    timeout=15
                )
                
                actual_status = response.status_code
                step_report['actual_status'] = actual_status
                step_report['expected_status'] = step['expected_status']

                if actual_status == step['expected_status']:
                    step_report['status'] = "SUCCESS"
                    logger.info(f"  - Step '{step['step_name']}' SUCCEEDED")
                    # Capture data if rule exists
                    if 'capture' in step:
                        _capture_from_response(response.json(), step['capture'], context)
                else:
                    flow_report['status'] = "FAILURE"
                    report['overall_status'] = "FAILURE"
                    logger.error(f"  - Step '{step['step_name']}' FAILED. Expected {step['expected_status']}, got {actual_status}")
                    try:
                        step_report['response_body'] = response.json()
                    except json.JSONDecodeError:
                        step_report['response_body'] = response.text

            except requests.RequestException as e:
                flow_report['status'] = "FAILURE"
                report['overall_status'] = "FAILURE"
                step_report['error'] = str(e)
                logger.error(f"  - Step '{step['step_name']}' FAILED with exception: {e}")
            
            flow_report['steps'].append(step_report)
            if step_report['status'] == "FAILURE":
                break # Stop flow on failure
        
        report['flows'].append(flow_report)

    # Save the detailed report
    report_dir = 'reports'
    os.makedirs(report_dir, exist_ok=True)
    report_filename = f"e2e_report_{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}.json"
    report_path = os.path.join(report_dir, report_filename)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"--- E2E Test Suite Finished. Overall Status: {report['overall_status']} ---")
    logger.info(f"Detailed report saved to: {report_path}")
    
    return report
