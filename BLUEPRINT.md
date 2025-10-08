# Project Blueprint

This document outlines the development plan for the document processing application.

## Phase 1: Backend API Foundation

- [x] **1.1: Enhance Document Model:** Expand the backend to manage a list of documents with properties like `id`, `name`, `status` ('uploaded', 'categorizing', 'categorized', 'error'), `category`, and `kv_pairs`.
- [x] **1.2: Mock AI Services:** Create placeholder API endpoints for `POST /api/v1/documents/<id>/categorize` and `POST /api/v1/documents/<id>/extract`.
- [x] **1.3: Update Upload Endpoint:** The file upload process will now return a structured list of all documents and their current status.

## Phase 2: Frontend Dashboard and "Professional View"

- [x] **2.1: Dynamic Dashboard:** Connect the frontend dashboard to the new backend API to display a live list of documents and their processing status.
- [x] **2.2: Create Document View:** Build the "Professional View" component in Angular to display the extracted KV pairs for a selected document.

## Phase 3: AI Chat and Continuous Learning

- [x] **3.1: Develop Chat APIs:** Create backend APIs for the different chat functionalities (KV correction, global, and category-specific).
- [x] **3.2: Integrate Chat UI:** Build the chat interfaces in the frontend and connect them to the new chat APIs.
- [x] **3.3: Implement Training Feedback Loop:** Create the mechanism to send user corrections back to the AI for training.
