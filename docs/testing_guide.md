# Testing Guide

This document outlines the strategy and tools for testing the IntelliDocs application. A robust testing process is crucial for ensuring code quality, reliability, and maintainability.

## 1. Testing Philosophy

We follow a multi-layered testing approach, commonly known as the "Testing Pyramid," which prioritizes different types of tests:

1.  **Unit Tests**: These form the base of the pyramid. They are fast, isolated, and test the smallest units of code (e.g., a single function or method) in isolation from their dependencies.

2.  **Integration Tests**: These tests verify the interaction between different components of the system, such as the Flask application's interaction with the database or the Celery worker's ability to process a task.

3.  **End-to-End (E2E) Tests**: These simulate a full user journey. For our back-end system, this involves making API calls to an endpoint and verifying that the entire data flow—from API request to database update—works as expected.

## 2. Tools and Frameworks

*   **`pytest`**: The primary framework for writing and running all our tests. Its fixture model is particularly useful for managing test setup and teardown.
*   **`pytest-flask`**: A pytest plugin for testing Flask applications. It provides a test client to make requests to the application without running a live server.
*   **`mongomock`**: Used for unit tests to mock MongoDB interactions. This allows us to test database logic without needing a running MongoDB instance, making the tests faster and more reliable.
*   **`requests`**: Used in E2E tests to make HTTP calls to the live API endpoints.

## 3. Test Structure

All tests are located in the `tests/` directory, which mirrors the application's structure:

```
/tests
|-- /unit
|   |-- test_doc_utils.py
|-- /integration
|   |-- test_api_endpoints.py
|   |-- test_celery_tasks.py
|-- /e2e
|   |-- test_full_workflow.py
|-- conftest.py
```

*   **`tests/unit/`**: Contains unit tests. These tests should use `mongomock` and should not make any external network or database calls.
*   **`tests/integration/`**: Contains integration tests. These tests will connect to the actual database and Redis instances provided by the Docker Compose environment.
*   **`tests/e2e/`**: Contains end-to-end tests that simulate real-world usage by making API calls to the running application.
*   **`conftest.py`**: A special pytest file used to define shared fixtures available across all test files (e.g., fixtures for setting up the Flask app instance or a test database).

## 4. How to Run Tests

### Prerequisites

1.  Ensure your Docker Compose environment is running, as integration and E2E tests depend on the `mongo` and `redis` services.

    ```bash
    docker-compose up -d
    ```

2.  Install the development dependencies, which include `pytest` and other testing tools.

    ```bash
    pip install -r requirements.txt
    ```

### Running All Tests

To run the entire test suite, simply execute `pytest` from the project root:

```bash
pytest
```

### Running Specific Tests

*   **Run a specific test file**:

    ```bash
    pytest tests/unit/test_doc_utils.py
    ```

*   **Run tests marked with a specific marker** (e.g., run only integration tests):

    ```bash
    pytest -m integration
    ```

    *(Note: This requires adding `@pytest.mark.integration` to your integration test functions.)*

## 5. Writing Tests: Best Practices

*   **Isolate, Isolate, Isolate**: Unit tests must not have external dependencies. Use mocks (`unittest.mock`) and fakes (`mongomock`) extensively.
*   **Use Fixtures**: Use pytest fixtures for setup and teardown logic. For example, a fixture can provide a clean database for each integration test.
*   **Clear Assertions**: Write clear and specific assertions. Instead of `assert result is True`, prefer `assert result == expected_value`.
*   **Test Both Success and Failure**: For every feature, test both the happy path (where everything works) and the sad path (where errors are expected). For example, when testing an API endpoint, check that it returns a `400` error for invalid input.
*   **Keep Tests Fast**: Slow tests discourage developers from running them frequently. Prioritize unit tests and use integration tests for more complex scenarios.
