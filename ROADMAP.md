
# Architectural Roadmap & Future Enhancements

This document outlines the proposed architectural improvements to evolve this project into a robust, scalable, and enterprise-grade AI application.

## 1. Frictionless Onboarding & Interactive Learning Loop

- **Objective:** Fix the critical initial user experience flaw by providing immediate value and creating a system that learns from user interaction.

- **Phase 1: The "Default Ingestion Pool"**
    - **Problem:** New users cannot get immediate value; they are forced to create categories and playbooks before uploading a file.
    - **Solution:**
        - Create a default, pre-configured "General Analysis" category for all new users.
        - When a user uploads their first document, it automatically goes into this pool.
        - This pool executes a default playbook: full-text indexing for Q&A and a best-effort, zero-shot Key-Value extraction using a powerful LLM prompt.
        - The user can immediately begin asking questions on their document, seeing value in seconds.

- **Phase 2: The "Human-in-the-Loop" Correction Agent**
    - **Problem:** If the initial automated extraction misses a key piece of information, the system fails statically. There is no way to correct it.
    - **Solution:**
        - When a user points out a missing key (e.g., "You missed the Project ID"), trigger an interactive "Correction Agent."
        - This agent will engage in a clarifying dialogue:
            - *"I am sorry I missed that. To help me find it, could you tell me which page it might be on?"*
            - Based on the user's hint, it will re-scan the document and present findings: *"I see the text 'PROJ-987' on page 3. Is this the Project ID you are referring to?"*

- **Phase 3: The "Learning Engine"**
    - **Problem:** A correction should not be a one-time fix; the system must get smarter.
    - **Solution:**
        - When the user confirms the correction (e.g., "Yes, that's it"), the system will perform two actions:
            1.  **Immediate Update:** Add the correct key-value pair to the metadata of the current document.
            2.  **Long-Term Learning:** The system will store this interaction as a new, positive example. This example will be dynamically added to the few-shot prompt for the Key-Value extractor on all future documents. The system learns from its mistakes and improves its accuracy over time.

## 2. AI-Powered Conversational System Administration

- **Objective:** Empower the chat AI to act as a conversational system administrator, capable of managing core application resources based on user commands. This transforms the chat from a passive Q&A bot into an active, operational partner.

- **Phase 1: Tool & Function Development**
    - **Problem:** The AI agent lacks the fundamental tools to interact with the application's administrative functions.
    - **Solution:**
        - Develop a comprehensive suite of "tools" (Python functions) that provide a secure and robust API for managing the system. This includes functions for:
            - **User & Role Management:** `create_user`, `assign_role`, `list_users`, etc.
            - **Category Management:** `create_category`, `list_categories`, `delete_category`.
            - **Playbook Management:** `create_playbook`, `list_playbooks`, `get_playbook_details`, `add_step_to_playbook`.

- **Phase 2: Agent Integration & Prompt Engineering**
    - **Problem:** The AI needs to be given access to the new tools and taught how and when to use them safely.
    - **Solution:**
        - Integrate the newly created tools into the Global Chat Agent's tool registry.
        - Engineer a new, sophisticated system prompt (`AGENT_PROMPT`) that instructs the AI on its role as a system administrator. This prompt will include strict guidelines on:
            - Asking for confirmation before making any changes.
            - Handling errors gracefully.
            - Understanding multi-step commands.

- **Phase 3: Conversational UI Enhancements**
    - **Problem:** Simple text responses are not always sufficient for administrative tasks.
    - **Solution:**
        - Enhance the chat UI to render structured data from the AI. For example, when listing playbooks, the AI should be able to return a formatted list that the UI can display as a clickable table.
        - Implement confirmation dialogues in the UI for destructive actions (e.g., "Are you sure you want to delete the 'Ad-Hoc' category?").

## 3. Core Pipeline Migration to LlamaIndex

- **Objective:** Replace the current, manually-assembled pipeline (`langchain`, `PyPDF2`, `fastembed`, etc.) with the unified LlamaIndex framework. This is a foundational step to enable many of the advanced features outlined below.

## 4. Building the Value Layer: Beyond the LlamaIndex Core

- **Objective:** Create a defensible, high-value product by building an intelligent layer of processing *before* and *after* the LlamaIndex core.

- **Pre-Processing: Intelligent Ingestion Pipeline**
    - **Multi-Modal Document Understanding:** Use OCR and Image-to-Text models to understand images, charts, and tables.
    - **Automated PII Redaction & Entity Tagging:** Automatically find and scrub sensitive data and extract key entities for better filtering.

- **Post-Processing: Enhanced Response & User Experience**
    - **Answer Validation & Confidence Scoring:** Cross-reference the LLM's answer against the source documents to provide a "confidence score."
    - **True Conversational Memory:** Implement a robust chat history management system for handling follow-up questions.
    - **Dynamic UI Generation:** Analyze the LLM's response and dynamically generate rich UI components like tables or charts.

## 5. Implement Advanced Retrieval Strategies

- **Objective:** Dramatically improve answer accuracy with Reranking and Hybrid Search.

## 6. Develop an Intelligent Routing Engine

- **Objective:** Improve efficiency and accuracy by routing queries to specialized indexes.

## 7. Migrate Vector Store to PGVector

- **Objective:** Replace MongoDB with PostgreSQL and `pgvector` for a unified data layer.

## 8. Migrate API Framework to FastAPI

- **Objective:** Upgrade from Flask to FastAPI for significant performance and development speed.

## 9. Self-Host AI Models for Full Privacy and Offline Capability

- **Objective:** Eliminate reliance on external API providers by running a powerful open-source model directly within the application using `llama-cpp-python`.

## 10. Integrate a Formal Evaluation Framework

- **Objective:** Move from subjective feelings to objective, data-driven improvements by integrating a framework like Ragas or DeepEval.
