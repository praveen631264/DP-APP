## UI Specification: Intelligent Document Assistant (IDA) - v6.0 (Interactive Chat Update)

### 1. Overview

This document outlines the UI for the Intelligent Document Assistant (IDA), version 6.0. This version introduces a powerful, context-aware AI chat experience, moving beyond simple Q&A to an interactive partnership between the user and the AI. The UI will be a **Single Page Application (SPA)** with a primary navigation sidebar and a dynamic content area.

### 2. Global Layout

A two-column layout consisting of a **navigation sidebar** on the left and a main content area on the right.

### 3. Navigation Sidebar

*   **Description:** The sidebar is the primary navigation and management hub.
*   **Static Links:**
    *   **Dashboard (`/`):** The main overview page.
    *   **Global Chat (`/chat`):** A link to the conversational AI interface for asking questions across **all** documents.
    *   **Trash (`/trash`):** A view for managing soft-deleted documents.
*   **Dynamic Categories:**
    *   An editable list of document categories. Clicking a category filters the document list in the main content area.

### 4. Main Content Area

#### 4.1. Document List View

*   When a category is selected, this view displays a list of documents within that category.
*   Provides options for sorting, filtering, and uploading new documents.

#### 4.2. Document Detail View (`/documents/<doc_id>`)

*   **Triggered by:** Clicking on a single document from the list view.
*   **Layout:** A multi-panel interface designed for deep interaction with a single document.
    *   **Panel 1: Interactive KVP Editor (Left)**
        *   Displays the Key-Value Pairs (KVPs) extracted by the AI.
        *   Each KVP is an editable field.
        *   Buttons to **Add**, **Update**, and **Delete** KVPs. Changes made here are recorded as feedback for the AI.
    *   **Panel 2: Document Viewer (Center)**
        *   Renders the original document (e.g., PDF, DOCX).
        *   Highlights the text corresponding to the selected KVP.
    *   **Panel 3: Document-Specific AI Chat (Right)**
        *   **Header:** "Chat with [document_filename]"
        *   **Functionality:** This is the core of the interactive AI experience. It allows a user to have a conversation specifically about the document currently being viewed.
        *   **Interactive KVP Extraction:**
            *   **User Prompt:** "I don't see the 'Invoice Number'. Can you find it?"
            *   **AI Action:** The AI re-analyzes the document text to find the missing information.
            *   **UI Update:** If found, the AI suggests the new KVP ("Invoice Number": "INV-12345"). The user can **accept** or **reject** this suggestion. If accepted, the KVP is added to the editor, and the change is saved as a training example for future documents.
        *   **Interactive KVP Modification:**
            *   **User Prompt:** "The 'Total Amount' is wrong. It should be $550.00."
            *   **AI Action:** The AI validates the user's correction against the document text.
            *   **UI Update:** The AI updates the KVP in the editor and asks for confirmation. This correction is also saved as a training example.
        *   **Interactive KVP Deletion:**
            *   **User Prompt:** "Remove the 'Fax Number' key. It's not relevant."
            *   **AI Action:** The AI marks the KVP for deletion.
            *   **UI Update:** The KVP is removed from the editor, and this is logged as feedback.
        *   **General Q&A:** Users can also ask general questions about the document, e.g., "Summarize the key findings in this report." The AI will answer based only on the content of the current document.

### 5. AI Feedback Loop

All user-driven interactions in the Document Detail View (adding, updating, or deleting KVPs, either manually or via chat) are critical. The system must capture these events as **high-quality training data**. This data will be used to fine-tune the AI model, improving its accuracy on subsequent document processing tasks, fulfilling a core business requirement.
