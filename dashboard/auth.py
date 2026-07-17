"""Authentication module for the dashboard.

Simple session-based auth using Streamlit's session_state.
Credentials are loaded from environment variables or a config file.
For production, replace with a proper identity provider (Auth0, Cognito, etc.).
"""

import os

import streamlit as st
from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

_DEFAULT_USERS = {
    "admin": {
        "password_hash": _pwd_context.hash("admin123"),
        "role": "admin",
        "name": "Administrator",
    },
    "viewer": {
        "password_hash": _pwd_context.hash("viewer123"),
        "role": "viewer",
        "name": "Viewer",
    },
}


def _load_users() -> dict:
    """Load user credentials from environment variables or defaults.

    Environment variables:
        AUTH_ADMIN_PASSWORD: Password for admin user.
        AUTH_VIEWER_PASSWORD: Password for viewer user.

    Returns:
        Dict of user credentials.
    """
    users = {}
    for username, defaults in _DEFAULT_USERS.items():
        env_var = f"AUTH_{username.upper()}_PASSWORD"
        password = os.getenv(env_var)
        if password:
            users[username] = {
                "password_hash": _pwd_context.hash(password),
                "role": defaults["role"],
                "name": defaults["name"],
            }
        else:
            users[username] = defaults
    return users


def _verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against an Argon2 hash.

    Args:
        password: Plain text password.
        password_hash: Argon2 hash to compare against.

    Returns:
        True if password matches the hash, False otherwise.
    """
    try:
        return _pwd_context.verify(password, password_hash)
    except Exception:
        return False


def is_authenticated() -> bool:
    """Check if the current session is authenticated.

    Returns:
        True if user is authenticated, False otherwise.
    """
    return st.session_state.get("authenticated", False)


def get_current_user() -> dict:
    """Get the current authenticated user info.

    Returns:
        Dict with 'username', 'role', and 'name' keys, or empty dict.
    """
    if not is_authenticated():
        return {}
    return {
        "username": st.session_state.get("username", ""),
        "role": st.session_state.get("role", ""),
        "name": st.session_state.get("user_name", ""),
    }


def require_auth():
    """Render login form if not authenticated, or return True if authenticated.

    Returns:
        True if authenticated, False if login form was rendered.
    """
    if is_authenticated():
        return True

    st.markdown(
        """
    <div class="login-container">
        <div class="login-title">DataFlow</div>
        <div class="login-subtitle">Sign in to access the dashboard</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    users = _load_users()

    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submitted = st.form_submit_button("Sign In", use_container_width=True)

        if submitted:
            user = users.get(username)
            if user and _verify_password(password, user["password_hash"]):
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.session_state["role"] = user["role"]
                st.session_state["user_name"] = user["name"]
                st.session_state["user_id"] = 1 if username == "admin" else 2
                st.session_state["permissions"] = (
                    ["*"] if user["role"] == "admin" else ["dashboards.view", "kpis.view"]
                )
                st.session_state["user"] = {
                    "username": username,
                    "role": user["role"],
                    "name": user["name"],
                    "permissions": st.session_state["permissions"],
                    "roles": [user["role"]],
                }
                st.rerun()
            else:
                st.error("Invalid username or password.")

    return False


def logout():
    """Clear the current session and log out the user."""
    st.session_state.clear()
    st.rerun()


def is_admin() -> bool:
    """Check if the current user has admin role.

    Returns:
        True if user is admin, False otherwise.
    """
    return get_current_user().get("role") == "admin"
