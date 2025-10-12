# Changelog & Deprecation Notice

This document records significant changes and deprecations made to the project. 

## **Major Refactoring: Unified Intelligence Platform**

The entire application was refactored to implement the vision of a Unified Business Intelligence & Automation Platform. As part of this major architectural overhaul, numerous legacy files and components were removed to eliminate technical debt, reduce complexity, and align the codebase with the new, three-pillar architecture.

### **Removed Components & Justification**

| File / Directory Removed      | Justification for Removal                                                                                                                                                           |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `config.py`                   | The application now uses a centralized configuration model within the `create_app` factory in `main.py`. This file, referencing an old MongoDB setup, was entirely obsolete.          |
| `api/task_runner.py`          | This file was part of the previous, simplistic task execution system. It has been completely replaced by the robust, scalable Celery architecture implemented in `tasks.py`.              |
| `run_cloud.sh`                | This deployment script was specific to the old architecture and is no longer relevant. Deployment is now handled via standard container practices defined in `Dockerfile`.              |
| `run_local.sh`                | Superseded by `devserver.sh` and the application factory pattern, which provide a more standardized way to run the development server.                                                  |
| `run_onprem.sh`               | An obsolete deployment script from the previous architecture.                                                                                                                       |
| `index.html` (root)           | This was a stray file from a previous development iteration. The application's user interface is served exclusively from the `templates/` directory.                                      |
| `view.html`                   | Another deprecated UI file that was not connected to the main Flask application.                                                                                                    |
| `docs/architecture.md`        | This document described the old system architecture and was therefore highly misleading. The new architecture is documented in the `quickstart_guide.md`.                             |
| `docs/project_blueprint.md`   | An outdated planning document that does not reflect the final, implemented system.                                                                                                  |
| `docs/local_setup.md`         | The setup instructions in this file were for the old, deprecated system. Correct setup procedures are now part of the main `README.md` and `quickstart_guide.md`.                      |
| `node_modules/`               | This directory, containing frontend dependencies, was removed to resolve critical disk space issues (`ENOSPC`). It is not required for backend operation and can be regenerated if needed. |
