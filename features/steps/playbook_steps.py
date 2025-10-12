
from behave import given, when, then
import requests
import json

# Base URL of the running application
BASE_URL = "http://127.0.0.1:8080"

@given('the application is running')
def step_impl(context):
    # This step is more of a precondition. We can do a quick health check.
    try:
        response = requests.get(f"{BASE_URL}/api/v1/system/health")
        assert response.status_code == 200, f"Application health check failed with status {response.status_code}"
    except requests.ConnectionError:
        assert False, "Application is not running or not accessible at " + BASE_URL

@when('I make a POST request to "{endpoint}" with the following data:')
def step_impl(context, endpoint):
    url = BASE_URL + endpoint
    # context.text contains the multiline string from the Gherkin step
    payload = json.loads(context.text)
    context.response = requests.post(url, json=payload)

@then('the response status code should be {status_code}')
def step_impl(context, status_code):
    expected_code = int(status_code)
    assert context.response.status_code == expected_code, f"Expected status code {expected_code}, but got {context.response.status_code}"

@then('the response body should contain a "{field}" field with the value "{value}"')
def step_impl(context, field, value):
    response_json = context.response.json()
    assert field in response_json, f"Response body does not contain the field '{field}'
    assert str(response_json[field]) == value, f"Expected field '{field}' to have value '{value}', but got '{response_json[field]}'"
