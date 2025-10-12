
# UI & API Requirements Specification: System Observability Dashboard (v1.0)

## 1. Executive Summary

This document specifies the requirements for a new **System Observability Dashboard**. This dashboard will provide a real-time, granular view into the health of the entire document processing pipeline, including the status of internal systems (simulated Celery/Redis) and the detailed progress of individual documents as they move through workflows.

This functionality is critical for diagnosing bottlenecks, identifying errors, and gaining a deep understanding of the application's operational performance.

---

## 2. New API Endpoint: System Health

To power the dashboard, a new, read-only API endpoint is required.

### **Get System Health Snapshot**
- **Endpoint:** `GET /api/v1/system/health`
- **Description:** Returns a single JSON object that provides a simulated, real-time snapshot of the key internal systems. This endpoint should be polled by the UI at a regular interval (e.g., every 5 seconds).
- **Success Response (200 OK):**
```json
{
  "redis_status": {
    "status": "online",
    "ping_ms": 1.2,
    "memory_used_mb": 45.8
  },
  "celery_workers": [
    {
      "worker_id": "celery@worker-1.local",
      "status": "online",
      "active_tasks": 2
    },
    {
      "worker_id": "celery@worker-2.local",
      "status": "offline",
      "active_tasks": 0
    }
  ],
  "queue_depth": {
    "default_queue": 8,
    "priority_queue": 1
  }
}
```

---

## 3. UI Functional Requirements (v1.0)

The Observability Dashboard will be a new, dedicated page in the application. It will be composed of three primary components.

### 3.1. System Health Panel
- **Location:** Top of the Observability page.
- **Function:** To provide an at-a-glance overview of the internal pipeline components, using data from the `GET /api/v1/system/health` endpoint.
- **UI Mockup:**

```
+--------------------------------------------------------------------------+
| System Health                                                            |
+----------------------+--------------------------+------------------------+
| Redis                | Celery Workers           | Task Queues            |
| [ICON] Online        | [ICON] 2 / 3 Online      | [ICON] 9 Pending       |
| Ping: 1.2ms          |                          |                        |
| Memory: 45.8 MB      |                          |                        |
+----------------------+--------------------------+------------------------+
```

### 3.2. In-Flight Documents Panel
- **Location:** Middle of the Observability page.
- **Function:** To display all documents that are currently being processed (`status: "running"`). It uses the rich data model from `document_store.py` (v5.2) to show granular progress.
- **Data Source:** This view will be constructed by the UI by fetching the full Document Object for any document whose `status` is `running`.
- **UI Mockup:**

```
+--------------------------------------------------------------------------+
| In-Flight Documents                                                      |
+--------------------------------------------------------------------------+
| Document: doc_12345 (Playbook: invoice_processing_v2)                      |
| Worker: celery@worker-1.local                                            |
|                                                                          |
| Step 2/3: "Push to Accounting API"  [ RUNNING ] (1.5s)                     |
|   [================>------------------] 60%                                |
|                                                                          |
+--------------------------------------------------------------------------+
| Document: doc_67890 (Playbook: shipping_label_gen)                         |
| Worker: celery@worker-3.local                                            |
|                                                                          |
| Step 1/2: "Generate Barcode"        [ RUNNING ] (0.8s)                     |
|   [=============>-----------------] 50%                                    |
|                                                                          |
+--------------------------------------------------------------------------+
| Document: doc_ABCDE                                                        |
|                                                                          |
| Step 1/1: "Blind Extraction"        [ PENDING ] (In Queue for 0.2s)      |
|   [---------------------------------] 0%                                   |
|                                                                          |
+--------------------------------------------------------------------------+
```
- **UI Logic:**
  - For each document, the UI will iterate through the `steps` array in the most recent `playbook_run`.
  - It will display the `name` of the current step (the first step with status `running` or `pending`).
  - It will show the `status` of that step (e.g., "RUNNING", "PENDING").
  - It will calculate and display the time elapsed since the `start_time` (for `running` steps) or `queue_time` (for `pending` steps).
  - A progress bar should be used to provide a visual cue.

### 3.3. Document Drill-Down View (Modal)
- **Interaction:** Clicking on any document in the "In-Flight Documents" panel will open a modal window.
- **Function:** To provide a highly detailed, step-by-step log for a single document run, allowing for deep error analysis and performance tuning.
- **UI Mockup:**

```
+--------------------------------------------------------------------------+
| Run Details: doc_12345 / run_1698380700                                    |
+--------------------------------------------------------------------------+
| [SUCCESS] Step 1: "Extract Header Data"                                  |
|           Worker: celery@worker-2.local  Duration: 2.1s                  |
|           Output: { "invoice_number": "INV-2023-001" }                   |
+--------------------------------------------------------------------------+
| [RUNNING] Step 2: "Push to Accounting API"                               |
|           Worker: celery@worker-1.local  Elapsed: 1.8s                   |
|           Output: null                                                   |
+--------------------------------------------------------------------------+
| [PENDING] Step 3: "Send SMS Alert"                                       |
|           Queued: 2.5s ago                                               |
|           Output: null                                                   |
+--------------------------------------------------------------------------+
| [FAILURE] Step 4: "Archive Document" (PREVIOUS RUN)                      |
|           Worker: celery@worker-1.local  Duration: 0.5s                  |
|           Error Log: { "error": "Connection timed out to S3" }           |
+--------------------------------------------------------------------------+

```
- **UI Logic:**
  - The modal will display **all** steps for the selected `run_id`.
  - Each step will show its final `status`, `worker_id`, `duration_seconds`, and a preview of the `output` or `error_log`.

---

## 4. Summary of Changes

- **New Backend Endpoint:** `GET /api/v1/system/health` must be implemented.
- **New UI Page:** A dedicated Observability Dashboard page.
- **New UI Components:** System Health Panel, In-Flight Documents Panel, Document Drill-Down Modal.
- **Data Model Dependency:** The UI will heavily rely on the rich timing and status data introduced in `document_store.py` v5.2.
