
# Bugger Agent: Automated Monitoring & Self-Healing System

This project is a Python-based web application that includes an automated monitoring and response system called the "Bugger Agent." The system is designed to watch for errors in application logs, automatically attempt self-healing actions, and create incidents for issues that require manual intervention. It also features a complete end-to-end (E2E) and Behavior-Driven Development (BDD) testing framework.

## Core Features

- **Flask Web Server**: A core API built with Python and Flask to manage documents and playbooks.
- **Structured Logging**: Centralized, JSON-formatted logging for reliable, machine-readable logs.
- **Bugger Monitoring Agent**: A standalone agent (`monitoring_agent.py`) that tails the application log, detects critical errors, and triggers automated responses.
- **Self-Healing & Escalation**: The agent can perform predefined self-healing actions or escalate issues by creating formal incidents.
- **Live Incident Dashboard**: A frontend UI (built with HTML, CSS, and vanilla JS) that provides a live, auto-refreshing view of all incidents.
- **E2E Testing Framework**: An API-driven test runner (`/api/v1/testing/run`) that executes a full suite of tests defined in `e2e_tests.json` and generates detailed reports.
- **BDD Testing with Behave**: Human-readable feature tests written in Gherkin for clear, behavior-focused testing.

## Project Structure

```
.
├── app.log                 # Main application log file, monitored by the agent
├── data_store.json         # Persistent JSON database for incidents and records
├── devserver.sh            # Script to run the Flask development server
├── document_store.py       # Handles data persistence
├── e2e_test_runner.py      # Core logic for the E2E testing framework
├── e2e_tests.json          # "Kit" defining all E2E test flows
├── features/               # Directory for BDD tests (Behave)
│   ├── playbook_execution.feature  # Gherkin feature file
│   └── steps/
│       └── playbook_steps.py   # Python step definitions for the feature
├── logging_config.py       # Configures structured JSON logging
├── main.py                 # Main Flask application, serves the UI and API
├── monitoring_agent.py     # The Bugger Agent script
├── notification_service.py # Service for sending incident notifications
├── playbooks.py            # Logic for running application playbooks
├── reports/                # Directory where E2E test reports are saved
├── requirements.txt        # Python project dependencies
├── static/                 # Frontend assets
│   ├── app.js
│   └── style.css
└── templates/
    └── index.html          # Main HTML for the incident dashboard
```

## Setup and Installation

1.  **Activate Virtual Environment**: The project is set up to use a Python virtual environment. You must activate it first.
    ```bash
    source .venv/bin/activate
    ```

2.  **Install Dependencies**: Install all required Python packages.
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

The system requires two separate processes to be run in two different terminals.

**Terminal 1: Start the Web Server & UI**

This command runs the Flask server, which also serves the API and the frontend dashboard.

```bash
./devserver.sh
```

- The UI will be available at the URL provided in the preview panel.

**Terminal 2: Start the Bugger Monitoring Agent**

This command starts the agent, which will begin monitoring `app.log` for errors.

```bash
# Make sure to activate the virtual environment in this terminal too!
source .venv/bin/activate

python monitoring_agent.py
```

## How to Use the Testing Frameworks

Make sure the web server is running before executing any tests.

### 1. End-to-End (E2E) Tests

To run the entire suite of E2E tests defined in `e2e_tests.json`, send a POST request to the testing endpoint. A full report will be returned in the response, and a copy will be saved in the `reports/` directory.

```bash
curl -X POST http://localhost:8080/api/v1/testing/run
```

### 2. Behavior-Driven Development (BDD) Tests

To run the Gherkin feature tests, use the `behave` command.

```bash
# Make sure to activate the virtual environment first
source .venv/bin/activate

behave
```

The results will be printed directly to your terminal.

## API Endpoints

- `GET /`: Serves the incident dashboard UI.
- `POST /api/v1/documents/run-playbook`: Executes a playbook.
- `GET /api/v1/incidents`: Returns a list of all recorded incidents.
- `POST /api/v1/testing/run`: **Triggers the full E2E test suite.**
