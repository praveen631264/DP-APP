# Autonomous Research Agent: Requirements & Build Plan

This document specifies the requirements and provides a detailed prompt for building the "Autonomous Research Agent," a high-power data acquisition system.

## 1. Requirements Document

**1.1. Introduction & Objective**

The primary objective is to build an automated agent capable of performing a high-level research query (e.g., "latest news on semiconductor manufacturing"), navigating the web to find relevant sources, and extracting all valuable data (text, PDFs, CSVs, etc.) from those sources.

The system must be robust, capable of bypassing common anti-bot mechanisms, and designed for modularity to allow for future enhancements.

**1.2. Key Features & User Stories**

- **As a user, I can:**
    - Provide a single, high-level research query.
    - Specify the number of top search results to investigate.
    - Launch the agent to perform the research task.
    - Find all extracted text and downloaded files organized in a local directory for later processing.
- **The Agent must be able to:**
    - Accept a search query and navigate to a search engine (e.g., Google).
    - Parse the search results page to extract the primary URLs.
    - For each URL, navigate to the corresponding webpage.
    - Intelligently extract the main article text, ignoring boilerplate (navbars, ads, footers).
    - Scan the page for any links pointing to downloadable files (`.pdf`, `.csv`, `.xlsx`).
    - Reliably download any discovered files.
    - Handle common web complexities like JavaScript-rendered pages and cookie consent dialogs.
    - Employ sophisticated anti-bot evasion techniques to ensure successful data extraction from protected sites.

**1.3. Core Components & Architecture**

The solution will be a Python application composed of several distinct modules:

1.  **Orchestrator (`main.py`):** The main entry point. Manages the overall workflow, configuration, and coordinates the other modules.
2.  **Configuration (`config.py`):** Manages all user-configurable parameters, such as search queries, download directories, API keys for proxy services, etc.
3.  **Navigation Module:** A browser automation module powered by Playwright. Responsible for all browser-based actions: visiting pages, clicking elements, and running searches.
4.  **Evasion Module:** Integrates with the Navigation Module to provide anti-bot capabilities. This includes using `playwright-stealth` and configuring residential proxies.
5.  **Extraction Module:** Responsible for parsing HTML content to extract main text and identify links to downloadable files.
6.  **Persistence Module:** Manages saving all collected data (text files, PDFs, CSVs) to a structured local directory.

**1.4. Recommended Technical Stack**

-   **Browser Automation:** Playwright
-   **Anti-Bot Evasion (Base):** `playwright-stealth`
-   **Anti-Bot Evasion (Advanced):** A commercial residential proxy provider (e.g., Bright Data, Oxylabs) or a Web Unlocker service.
-   **File/Data Parsing:** `pypdf` for PDFs, `pandas` for CSV/Excel.
-   **Configuration Management:** Python's built-in `argparse` or a simple config file.

**1.5. Workflow**

1.  User launches the Orchestrator with a research query.
2.  Orchestrator initializes the Navigation module with evasion capabilities enabled (stealth + proxy).
3.  Navigation module performs a Google search.
4.  Extraction module parses the search results page to get a list of URLs.
5.  Orchestrator loops through each URL:
    a.  Navigation module navigates to the URL.
    b.  Extraction module extracts the main text and saves it via the Persistence module.
    c.  Extraction module finds all downloadable file links on the page.
    d.  For each file link, the Navigation module clicks the link and intercepts the download, saving it via the Persistence module.
6.  The process repeats for all top search results.

---

## 2. Prompt for AI Code Generator

You are an expert Python engineer specializing in building robust, industrial-scale data acquisition systems. Your task is to build a complete "Autonomous Research Agent" based on the detailed requirements below. The solution must be modular, resilient, and include sophisticated error handling and anti-bot evasion techniques.

**High-Level Goal:** Create a Python script that takes a search query, performs a Google search, and then "deep dives" into the top results to extract all text and download all linked PDF, CSV, and Excel files.

Here are the step-by-step instructions. Please generate the complete code for each file.

**Step 1: Project Structure**

First, define the project structure. All the code should be organized into the following files:

-   `config.py`: For all user settings.
-   `research_agent.py`: The main script containing all logic.
-   `requirements.txt`: To list all dependencies.

**Step 2: Create the `requirements.txt` file**

Generate the content for `requirements.txt`. It must include `playwright`, `playwright-stealth`, `pypdf`, `pandas`, and `openpyxl`.

**Step 3: Create the `config.py` file**

This file should contain all user-configurable parameters. Do not hard-code values in the main script. Include detailed comments explaining each setting.

-   `SEARCH_QUERY`: The research topic to search for.
-   `MAX_RESULTS_TO_PROCESS`: The number of top Google results to process.
-   `DOWNLOAD_DIR`: The root directory to save all extracted data.
-   `HEADLESS_BROWSER`: A boolean to run the browser in visible or headless mode.
-   `PROXY_ENABLED`: A boolean to enable or disable the use of a proxy.
-   `PROXY_SERVER`: The proxy server address (e.g., from Bright Data). Leave it as an empty string if disabled.

**Step 4: Create the `research_agent.py` script**

This is the core of the project. Build it using the following logic, making sure to import from `config.py`.

1.  **Imports:** Import all necessary libraries: `asyncio`, `os`, `re`, `playwright.async_api`, `playwright_stealth`, `pandas`, `pypdf`, and all variables from `config.py`.

2.  **Setup & Initialization:**
    -   Create the main `async def main():` function.
    -   Inside `main`, ensure the `DOWNLOAD_DIR` exists, creating it if necessary.
    -   Set up the Playwright browser launch. It MUST be configurable to use the proxy settings from `config.py` if `PROXY_ENABLED` is true.

3.  **Stealth Application:**
    -   After creating a new browser page, immediately apply the `stealth_async(page)` patch to it. This is critical for evasion.

4.  **Google Search Functionality:**
    -   Navigate to Google.
    -   Handle any potential cookie consent pop-ups robustly.
    -   Fill the search box with the `SEARCH_QUERY` and execute the search.
    -   Wait for the search results container to load.
    -   Parse the page to extract the href attributes from the top `MAX_RESULTS_TO_PROCESS` search result links. Store these in a list called `urls_to_visit`. Handle cases where a link might not be a valid URL.

5.  **Deep Dive Loop:**
    -   Create a loop to iterate through each `url` in `urls_to_visit`.
    -   Inside the loop, add extensive `try...except` blocks for each major operation (navigation, text extraction, file download) to ensure the agent doesn't crash on a single failed page.
    -   Log progress clearly (e.g., "Processing URL (1/5): ...").

6.  **Text Extraction Logic:**
    -   For each page, find the main article text. Use a heuristic like checking for `<article>`, `<main>`, or the `<body>` tag.
    -   Save the extracted text to a `.txt` file in a subdirectory named after the article's domain. Use a sanitized version of the URL for the filename.

7.  **File Download Logic:**
    -   On the same page, find all `<a>` tags.
    -   Iterate through them and check if the `href` attribute ends with `.pdf`, `.csv`, or `.xlsx`.
    -   For each match, create the full, absolute URL for the file.
    -   Use the `page.expect_download()` context manager while clicking the link to reliably capture the download.
    -   Save the downloaded file to the same subdirectory, preserving its original name.
    -   Include robust error handling in case a download fails or times out.

8.  **Main Execution Block:**
    -   Use `if __name__ == "__main__":` to run the `asyncio.run(main())` function.

Please generate the complete, production-quality code for all three files based on these detailed instructions.