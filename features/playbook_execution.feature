
Feature: Playbook Execution API
  As a user of the Bugger Agent system
  I want to be able to run playbooks against documents
  So that I can process and analyze my data.

  Scenario: Successfully run a playbook on a new document
    Given the application is running
    When I make a POST request to "/api/v1/documents/run-playbook" with the following data:
      """
      {
        "document_id": "bdd-test-doc-123",
        "playbook_id": "pb_analyze_text",
        "catalog_id": "cat_text_analysis"
      }
      """
    Then the response status code should be 200
    And the response body should contain a "status" field with the value "completed"

  Scenario: Attempt to run a playbook with invalid data
    Given the application is running
    When I make a POST request to "/api/v1/documents/run-playbook" with the following data:
      """
      {
        "document_id": "bdd-test-doc-456"
      }
      """
    Then the response status code should be 400
    And the response body should contain an "error" field with the value "Missing required fields"
