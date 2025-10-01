# Blueprint: Intelligent Document Assistant (IDA) v6.0

## 1. Project Overview

This document outlines the plan for building the Intelligent Document Assistant (IDA), a Single Page Application (SPA). The core of this version is a powerful, interactive AI chat experience that allows users to collaborate with the AI to manage and extract information from their documents. The UI will be built using the latest Angular standards, including standalone components, signals, and native control flow.

---

## 2. Global Layout

- **Primary Structure:** A persistent two-column layout.
    - **Left Column:** A global navigation sidebar.
    - **Right Column:** A dynamic main content area that displays the content for the selected route.

### 2.1. Global Navigation Sidebar
- **Description:** The application's primary, static navigation hub on the far left of the screen.
- **Static Links:**
    - **Dashboard (`/`):** High-level overview page.
    - **Documents (`/documents`):** Navigates to the main document workspace.
    - **Global Chat (`/chat`):** A conversational AI interface for asking questions across **all** documents.
    - **Trash (`/trash`):** A view for managing soft-deleted documents.
- **Dynamic Content:**
    - **Categories List:** A list of document categories below the static links. Categories are read-only and managed by the backend. Clicking a category name filters the document grid within the `/documents` workspace.

---

## 3. Main Content Area & Routes

### 3.1. Document Workspace (`/documents`)
- **Description:** This is the main area for managing documents. It has its own internal two-panel layout.
- **Layout:**
    - **Left Panel (Documents Sidebar):**
        - Displays a list of **Recent Documents** and their status.
    - **Right Panel (Document Grid & Upload):**
        - Contains the **Upload Document** feature.
        - Displays the main grid or list of all documents.
        - The documents shown here are filtered by the category selected in the Global Navigation Sidebar.
- **User Flow:** Clicking on a document row in the grid navigates the user to the `Document Detail View` (`/documents/<doc_id>`).

### 3.2. Document Detail View (`/documents/<doc_id>`)
- **Description:** A sophisticated, multi-panel interface for deep interaction with a single selected document. This view takes over the main content area.
- **Layout:** A three-panel interface.
    - **Panel 1: Interactive KVP Editor (Left):**
        - Displays Key-Value Pairs (KVPs) extracted by the AI.
        - Each KVP is an editable field.
        - Provides controls to **Add**, **Update**, and **Delete** KVPs manually.
    - **Panel 2: Document Viewer (Center):**
        - Renders the original source document (e.g., PDF).
        - **Highlighting:** Must be capable of highlighting the specific text in the document that corresponds to a KVP selected in the editor.
    - **Panel 3: Document-Specific AI Chat (Right):**
        - **Context:** This chat is scoped *only* to the document currently being viewed.
        - **Header:** Will display "Chat with [document_filename]".
        - **Interactive AI Functions:**
            - **Extraction:** User can ask the AI to find missing information.
            - **Modification:** User can ask the AI to correct a value.
            - **Deletion:** User can ask the AI to remove an irrelevant KVP.
            - **General Q&A:** User can ask summary or lookup questions about the document's content.

## 4. AI Feedback Loop (Business Requirement)

- **Core Mandate:** All user interactions within the Document Detail View that modify KVPs (whether done manually in the editor or via the AI chat) **must** be captured as training data for the backend AI model.

## 5. Architectural Plan & Style Guide

- **Standalone Components, OnPush Change Detection, Native Control Flow, Signal-Based Architecture, `inject()` function, and Strict Typing** are all mandatory, non-negotiable rules for all development.
