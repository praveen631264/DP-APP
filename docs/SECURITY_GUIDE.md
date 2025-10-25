# Security Architecture Guide

This document provides a comprehensive overview of the authentication, authorization, and security mechanisms implemented in the IntelliDocs application.

---

## 1. Core Technology

The security layer is built upon **Flask-Security-Too**, a powerful, well-maintained library that provides a robust foundation for:
-   User and Role Management
-   Password Hashing (defaulting to `bcrypt`)
-   Session Management (via secure cookies)
-   Two-Factor Authentication (MFA/TOTP)
-   Passwordless login, registration, and confirmation features.

We use **MongoEngine** as the Object-Document Mapper (ODM) to interact with our `User` and `Role` models in MongoDB.

---

## 2. Configuration Details

This section provides specific configuration examples for enabling the different authentication and security features. All configuration should be managed via environment variables and loaded in `config.py`.

### 2.1 Basic Authentication Configuration (Default)

This is the default setup. It requires a user to register and then be approved by an administrator before they can log in with an email and password.

**`.env` file:**
```ini
# A strong, random string is required for session security.
SECRET_KEY="change-this-to-a-very-long-and-random-string"

# No other security-specific variables are needed for the default setup.
```

**`config.py`:**
The `Config` class should load the `SECRET_KEY`. `Flask-Security-Too` is automatically enabled by the `Security(app, user_datastore)` call in `app/__init__.py`.

### 2.2 Two-Factor Authentication (MFA/TOTP) Configuration

To enable Time-based One-Time Passwords (TOTP) via authenticator apps (Google/Microsoft Authenticator), you must add the following settings.

**`.env` file:**
```ini
SECRET_KEY="change-this-to-a-very-long-and-random-string"

# --- MFA/TOTP Configuration ---
SECURITY_TWO_FACTOR=True
SECURITY_TOTP_ISSUER="IntelliDocs"
```

**`config.py`:**
Your `Config` class must load these new variables.
```python
class Config:
    # ... existing config ...
    SECURITY_TWO_FACTOR = os.environ.get('SECURITY_TWO_FACTOR', 'False').lower() in ('true', '1', 't')
    SECURITY_TOTP_ISSUER = os.environ.get('SECURITY_TOTP_ISSUER', 'YourAppName')
```

With these settings, logged-in users will be able to navigate to the `/tf-setup` endpoint to enable MFA on their account.

### 2.3 Enterprise SSO / Federated Identity Configuration

Integrating with an enterprise IdP like Ping Identity (SAML) or Okta/Azure AD (OIDC) is an advanced setup that requires adding a library like `Authlib`. The strategy is to use the IdP as the source of truth and provision users in our local database "Just-In-Time" (JIT).

**Required Information from the Client:**
Before starting integration, you MUST request the following from the client's IT department:
-   **Protocol:** Is it SAML 2.0 or OpenID Connect (OIDC)?
-   **Metadata URL:** A URL that provides all the necessary endpoints and certificates for the IdP.
-   **Client ID & Secret:** Credentials for our application (the "Service Provider") to securely communicate with their IdP.
-   **Attribute Mapping:** A list of attributes they will send in the token after a user logs in. We absolutely require `email`. We strongly recommend they also send `roles` and any attributes needed for AACL (e.g., `department`, `region`, `cost_center`).

**`.env` file (Example for OIDC):**
```ini
SECRET_KEY="change-this-to-a-very-long-and-random-string"

# --- OIDC/SSO Configuration ---
OIDC_CLIENT_ID="your-client-id-from-the-idp"
OIDC_CLIENT_SECRET="your-client-secret-from-the-idp"
OIDC_METADATA_URL="https://idp.example.com/.well-known/openid-configuration"
```

**Architectural Changes (in `app/__init__.py`):**
You would then initialize `Authlib` within the application factory and create a new blueprint to handle the `/login` and `/sso/callback` routes. The callback endpoint would contain the JIT provisioning logic described in the strategy section below.

## 2. Authentication

Authentication is the process of verifying a user's identity. IntelliDocs supports multiple methods.

### 2.1 Basic Authentication (Username/Password)

This is the standard form of authentication.

-   **How it Works**: A user provides their email and password to a login endpoint. `Flask-Security-Too` hashes the provided password and compares it to the stored hash in the database.
-   **API Access**: Upon successful login, the server creates a session and returns a session cookie (`session`). For subsequent API requests, this cookie must be included in the `Cookie` header. The Flask application will automatically validate this cookie to identify the user.
-   **Endpoints**: `Flask-Security-Too` automatically provides several endpoints (e.g., `/login`, `/logout`, `/register`). You can interact with these via a front-end application or API client.

### 2.2 Two-Factor Authentication (MFA/TOTP)

For enhanced security, the system supports Time-based One-Time Passwords (TOTP) via authenticator apps like Google Authenticator or Microsoft Authenticator.

-   **Setup**: `Flask-Security-Too` provides an endpoint (`/tf-setup`) where a logged-in user can enable two-factor authentication. The API will return a QR code (or a secret key) to be scanned by their authenticator app.
-   **Login Flow**: Once MFA is enabled, the login process becomes a two-step flow:
    1.  User provides email and password.
    2.  If correct, the server responds with a request for a TOTP code.
    3.  The user provides the 6-digit code from their authenticator app to a second endpoint (`/tf-login`) to complete the login and establish a session.

### 2.3 Enterprise SSO / Federated Identity (SAML/OIDC)

For enterprise clients, integrating with their existing Identity Provider (IdP) like Ping Identity, Okta, or Azure AD is crucial. Our architecture is designed to be extensible for this.

**How it Works (Strategy):**

1.  **Federation**: The IntelliDocs application acts as a **Service Provider (SP)**. The client's system (e.g., Ping) is the **Identity Provider (IdP)**. A trust relationship is established by exchanging metadata.
2.  **Login Initiation**: The user attempts to log in to IntelliDocs. Instead of a password form, they are redirected to the company's SSO login page.
3.  **Authentication at IdP**: The user authenticates with their corporate credentials (and MFA) at the IdP.
4.  **Token Issuance**: Upon success, the IdP sends the user back to a special callback URL on our application (e.g., `/sso/callback`). This request contains a secure token (a SAML assertion or OIDC ID Token).
5.  **Just-In-Time (JIT) Provisioning**: Our callback endpoint does the following:
    -   It validates the token from the IdP.
    -   It extracts user attributes from the token. **Crucially, we need the IdP to send us `email`, `roles`, and any attributes needed for AACL (e.g., `department`, `region`).**
    -   It searches our local `User` database for a user with the matching email.
    -   **If the user does not exist**: A new `User` is created in our database. Their password field is left empty (as they will always log in via SSO), and their roles and attributes are set based on the token.
    -   **If the user exists**: Their roles and attributes are updated to match the information from the IdP. This ensures our local user record is always in sync with the enterprise directory.
    -   The application then uses `Flask-Security-Too`'s `login_user()` function to create a session for this user, without needing a password.

**Implementation**: This would be achieved by adding a library like `Authlib` to handle the complexities of the SAML or OIDC protocols within the callback endpoint. The key is that the SSO flow results in a valid, populated `User` object in our database, which allows all our internal authorization logic to work seamlessly.

## 3. Authorization

Authorization is the process of determining what an authenticated user is allowed to do.

### 3.1 Role-Based Access Control (RBAC)

`Flask-Security-Too` provides standard RBAC decorators like `@roles_required('admin')`. We use a more powerful, custom system.

### 3.2 Attribute-Based Access Control (AACL)

Our primary authorization mechanism is AACL, implemented via the `@attribute_required` decorator.

-   **How it Works**: This decorator checks the `attributes` dictionary on the `current_user` object against the policy defined for the resource.
    -   **Example**: An endpoint decorated with `@attribute_required({"department": "finance", "region": "EMEA"})` will only grant access to users whose `attributes` field contains `{"department": "finance", ...}` and `{"region": "EMEA", ...}`.
-   **Flexibility**: This is extremely powerful because access is not tied to a static role. A user's access can change dynamically based on their attributes, which can be updated automatically via the SSO JIT provisioning process.

## 4. User Registration & Approval

To prevent unauthorized access, especially in a fintech context, a manual approval workflow is enforced.

-   **Signup**: When a new user registers via the `/register` endpoint, their account is created with `active=True` but `approved=False`.
-   **Auto-Approval (Optional)**: The registration logic can be configured to check the user's email domain. If it matches a trusted company domain (e.g., `@my-company.com`), the `approved` flag can be set to `True` automatically.
-   **Manual Approval**: For all other users, an administrator must use the secure `/api/v1/admin/users/<user_id>/approve` endpoint to set `approved=True`.
-   **Login Enforcement**: The login process checks for `user.approved`. If `False`, access is denied even with a correct password.