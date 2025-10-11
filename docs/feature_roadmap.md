
# Feature Roadmap: From Demo Feedback to a Robust Platform

This document outlines a strategic plan to address the valuable feedback received during the recent product demo. The feedback is a clear guide to evolving this product from a promising concept into a powerful, defensible, and highly valuable platform. We will proceed with the project by implementing the features outlined below in a phased approach.

---

## Phase 1: Core Enhancements (Short-Term, High-Impact)

This phase focuses on immediately addressing the most critical feedback around customizability and trust.

### Feature 1: Customizable Prompts per Category

**Goal:** Address the feedback: "if we have provisions to include a prompt on a category or a document that would help many downstream apps." This turns our generic tool into a flexible one.

**Plan:**

1.  **Data Model:** Add a new optional field to the `Category` model called `prompt_template` (type: text).
2.  **UI/UX:** In the category management section of the application, for each category, add a text area allowing users to write and save a custom prompt template.
3.  **Backend Logic:**
    *   When processing a document, retrieve the `prompt_template` for the document's assigned category.
    *   If a custom template exists, use it. If not, fall back to a default, generic prompt.
    *   Inject the document's text into the template before sending it to the AI model.

**Sample Prompt Structure:**

The backend will wrap the user's custom prompt with the document content.

```
You are an expert assistant specialized in handling documents for the category: '{category_name}'.

Your instructions are to follow the user's prompt below to analyze the provided document text.

---
**User's Custom Prompt:**
{user_defined_prompt}
---

---
**Document Text:**
{document_text}
---
```

### Feature 2: Human-in-the-Loop Approval Workflow

**Goal:** Address the feedback: "a category should be one field and post approval it has to actually categorized." This builds user trust and generates valuable data for future improvements.

**Plan:**

1.  **Data Model:** Modify the `Document` model.
    *   Rename the current `category_id` to `suggested_category_id`.
    *   Add a new `final_category_id` (nullable).
    *   Add a `status` field with possible values like `'pending_review'`, `'approved'`, `'rejected'`.
2.  **Backend Logic:** When the AI first processes a document, it should populate `suggested_category_id` and set the `status` to `'pending_review'`.
3.  **UI/UX:**
    *   Create a "Review Queue" page that displays all documents with the `'pending_review'` status.
    *   For each document, show the content/preview and the AI's suggested category.
    *   Provide two main actions:
        *   **Approve:** On click, the `suggested_category_id` is copied to `final_category_id`, and the `status` is changed to `'approved'`.
        *   **Re-categorize:** On click, present a dropdown of all categories. The user's selection is saved to `final_category_id`, and the `status` is changed to `'approved'`.

---

## Phase 2: Advanced Capabilities (Mid-Term)

This phase focuses on security and laying the groundwork for a proprietary AI model.

### Feature 3: Data Collection for "Silent Model" Training

**Goal:** Address the feedback: "there should be a silent model which should gets trained progressively." We will use the data from the approval workflow (Feature 2).

**Plan:**

1.  **Data Store:** Create a new table or database collection named `VerifiedTrainingData`.
2.  **Backend Logic:** Every time a user 'Approves' or 'Re-categorizes' a document, create a new entry in `VerifiedTrainingData`.
3.  **Data Schema:** Each entry should contain:
    *   `document_content` (or a reference to it).
    *   `ai_suggested_category_id`.
    *   `human_verified_category_id` (this is the ground truth).
    *   `timestamp`.
    *   `user_id` (of the user who verified it).
4.  **Next Steps:** This collected data becomes the fuel for fine-tuning an open-source model (like DistilBERT or a similar transformer) in the future.

### Feature 4: Implement Retrieval-Augmented Generation (RAG) for Security & Privacy

**Goal:** Address the feedback regarding data security ("internal data which goes outside") and the mention of "vector RAG". This makes the product enterprise-ready.

**Plan:**

1.  **Infrastructure:** Integrate a vector database (e.g., ChromaDB, Weaviate, Pinecone).
2.  **Ingestion Pipeline:**
    *   When a document is uploaded, it must be chunked into smaller, coherent paragraphs.
    *   Use a sentence-embedding model (which can be run locally and for free, like `all-MiniLM-L6-v2`) to turn each text chunk into a vector.
    *   Store these vectors and their corresponding text chunks in the vector database.
3.  **RAG-based Processing:** The core document processing logic will change significantly:
    *   **Old way:** Send the entire document to the AI.
    *   **New way (RAG):**
        1.  Take the user's task/query (e.g., "Summarize this document" or a custom prompt from Feature 1).
        2.  Convert this query into a vector using the same sentence-embedding model.
        3.  Search the vector database for the most relevant text chunks from the document based on the query vector.
        4.  Construct a new prompt that includes *only* these highly relevant, retrieved chunks.

**Sample Prompt for RAG:**

```
You are a helpful AI assistant. Answer the user's question based *only* on the provided context snippets from the document.

---
**Context Snippets:**
- {retrieved_chunk_1}
- {retrieved_chunk_2}
- {retrieved_chunk_3}
---

**User's Question/Task:**
{user_question_or_task}
```

---

## Phase 3: Automation & Intelligence (Long-Term)

This phase focuses on building advanced, multi-step automated workflows.

### Feature 5: Inter-Agent Workflows

**Goal:** Address the feedback: "we should have agents between categories they speak together and pass this files."

**Plan:**

1.  **Data Model:**
    *   `Workflow` table: To define a workflow (e.g., "New Customer Onboarding").
    *   `WorkflowStep` table: To define the steps in a workflow. Each step would have a `source_category`, a `target_category`, and a `prompt_template` for the agent performing the step.
2.  **UI/UX:** Create a "Workflow Builder" interface where users can chain categories and agents together. (e.g., `If category is 'Initial Complaint' -> run 'Sentiment Analysis' agent -> result is 'Negative Sentiment Complaint'`).
3.  **Orchestration Engine (Backend):**
    *   A service that monitors documents that have been assigned a `final_category`.
    *   If a document's category matches the `source_category` of a workflow step, the orchestrator automatically triggers the next agent in the sequence, using the prompt defined for that step.

**Example Multi-Step Prompt Workflow:**

*   **Step 1: Categorization Agent.**
    *   *Result:* Document is categorized as `Legal Contract`.
*   **Step 2: Workflow triggers "Key Clause Extraction" Agent.**
    *   **Prompt for Step 2:**
        ```
        This document is a legal contract. Your task is to extract the 'Governing Law', 'Termination Conditions', and 'Liability Limitations' clauses. Output the result in JSON format.

        ---
        Document Text:
        {document_text}
        ---
        ```
    *   *Result:* A JSON object with the extracted clauses.
