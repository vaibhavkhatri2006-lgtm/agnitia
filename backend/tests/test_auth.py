"""
CivicPulse Stage 2 Authentication & RBAC Test Suite
Covers:
- Demo users authentication
- Invalid login (wrong password, non-existent user, inactive user)
- Token validation (missing, malformed, invalid signature, expired)
- /auth/me profile retrieval
- Server-side RBAC enforcement:
  * citizen cannot perform authority actions
  * authority can perform authority actions
  * only admin can perform admin actions
  * community verifier role permissions
"""
import sys
from datetime import timedelta
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token

client = TestClient(app)


def test_demo_users_login():
    """Verify that all four demo accounts can authenticate successfully and receive valid tokens."""
    demo_accounts = [
        ("citizen@example.com", "Citizen123!", "citizen"),
        ("community@example.com", "Community123!", "community"),
        ("authority@example.com", "Authority123!", "authority"),
        ("admin@example.com", "Admin123!", "admin"),
    ]

    for email, password, expected_role in demo_accounts:
        response = client.post(
            "/auth/login",
            json={"email": email, "password": password},
        )
        assert response.status_code == 200, f"Login failed for {email}: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0
        assert data["user"]["email"] == email
        assert data["user"]["role"] == expected_role
        assert len(data["user"]["permissions"]) > 0


def test_invalid_login_credentials():
    """Verify rejection of invalid passwords and non-existent users."""
    # Wrong password
    bad_pw_resp = client.post(
        "/auth/login",
        json={"email": "citizen@example.com", "password": "WrongPassword999!"},
    )
    assert bad_pw_resp.status_code == 401
    assert "Incorrect email or password" in bad_pw_resp.json()["detail"]

    # Non-existent user
    unknown_user_resp = client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "AnyPassword!"},
    )
    assert unknown_user_resp.status_code == 401

    # Inactive user account rejection
    inactive_resp = client.post(
        "/auth/login",
        json={"email": "inactive@example.com", "password": "Inactive123!"},
    )
    assert inactive_resp.status_code == 403
    assert "inactive" in inactive_resp.json()["detail"].lower()


def test_missing_and_invalid_tokens():
    """Verify that protected endpoints reject missing, malformed, or fake tokens with 401."""
    # 1. Missing token
    resp_missing = client.get("/auth/me")
    assert resp_missing.status_code == 401

    # 2. Malformed token
    resp_malformed = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer not-a-valid-jwt-token"},
    )
    assert resp_malformed.status_code == 401

    # 3. Token signed with wrong secret key
    import jwt
    fake_token = jwt.encode({"sub": "1", "role": "admin"}, "completely-wrong-secret-key-32bytesmin!!", algorithm="HS256")
    resp_fake = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {fake_token}"},
    )
    assert resp_fake.status_code == 401


def test_expired_token_rejection():
    """Verify that an expired JWT is rejected with 401 Unauthorized."""
    # Create an already expired token (expired 5 minutes ago)
    expired_token = create_access_token(
        user_id=1,
        email="citizen@example.com",
        role="citizen",
        permissions=["data:read"],
        expires_delta=timedelta(minutes=-5),
    )

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()


def test_auth_me_endpoint():
    """Verify /auth/me returns accurate profile information for the authenticated user."""
    login_resp = client.post(
        "/auth/login",
        json={"email": "citizen@example.com", "password": "Citizen123!"},
    )
    token = login_resp.json()["access_token"]

    me_resp = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == "citizen@example.com"
    assert me_data["role"] == "citizen"
    assert "data:read" in me_data["permissions"]
    assert "report:create" in me_data["permissions"]


def test_role_authorization_citizen_cannot_perform_authority_action():
    """Verify server-side RBAC: Citizen CANNOT access authority-protected endpoints."""
    # Log in as citizen
    login_resp = client.post(
        "/auth/login",
        json={"email": "citizen@example.com", "password": "Citizen123!"},
    )
    citizen_token = login_resp.json()["access_token"]

    # Attempt to access authority-only endpoint
    resp = client.get(
        "/auth/verify-role/authority",
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert resp.status_code == 403, f"Expected 403 for citizen accessing authority endpoint, got {resp.status_code}"
    assert "requires one of the following roles" in resp.json()["detail"]


def test_role_authorization_authority_can_perform_required_actions():
    """Verify server-side RBAC: Authority CAN access authority-protected endpoints."""
    # Log in as authority
    login_resp = client.post(
        "/auth/login",
        json={"email": "authority@example.com", "password": "Authority123!"},
    )
    authority_token = login_resp.json()["access_token"]

    # Access authority-only endpoint
    resp = client.get(
        "/auth/verify-role/authority",
        headers={"Authorization": f"Bearer {authority_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "authorized"
    assert data["role"] == "authority"


def test_role_authorization_admin_privileges():
    """Verify that admin can access both authority and admin endpoints, while non-admins are rejected."""
    # Log in as admin
    admin_login = client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "Admin123!"},
    )
    admin_token = admin_login.json()["access_token"]

    # Admin accesses authority endpoint -> 200
    auth_resp = client.get(
        "/auth/verify-role/authority",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert auth_resp.status_code == 200

    # Admin accesses admin endpoint -> 200
    admin_resp = client.get(
        "/auth/verify-role/admin",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_resp.status_code == 200

    # Authority attempts to access admin endpoint -> 403
    authority_login = client.post(
        "/auth/login",
        json={"email": "authority@example.com", "password": "Authority123!"},
    )
    authority_token = authority_login.json()["access_token"]
    forbidden_resp = client.get(
        "/auth/verify-role/admin",
        headers={"Authorization": f"Bearer {authority_token}"},
    )
    assert forbidden_resp.status_code == 403


def test_role_authorization_community():
    """Verify community role authorization on community endpoints."""
    # Community user
    comm_login = client.post(
        "/auth/login",
        json={"email": "community@example.com", "password": "Community123!"},
    )
    comm_token = comm_login.json()["access_token"]
    comm_resp = client.get(
        "/auth/verify-role/community",
        headers={"Authorization": f"Bearer {comm_token}"},
    )
    assert comm_resp.status_code == 200

    # Citizen accessing community endpoint -> 403
    cit_login = client.post(
        "/auth/login",
        json={"email": "citizen@example.com", "password": "Citizen123!"},
    )
    cit_token = cit_login.json()["access_token"]
    cit_resp = client.get(
        "/auth/verify-role/community",
        headers={"Authorization": f"Bearer {cit_token}"},
    )
    assert cit_resp.status_code == 403


def test_register_user_lifecycle():
    """Verify that new users can register, receive tokens, and subsequently authenticate."""
    import time
    unique_email = f"testuser_{int(time.time() * 1000)}@civicpulse.org"

    # 1. Successful registration
    reg_resp = client.post(
        "/auth/register",
        json={
            "email": unique_email,
            "password": "Password123!",
            "role": "citizen",
            "display_name": "Test Citizen",
        },
    )
    assert reg_resp.status_code in (200, 201), f"Registration failed: {reg_resp.text}"
    reg_data = reg_resp.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == unique_email
    assert reg_data["user"]["role"] == "citizen"
    assert reg_data["user"]["display_name"] == "Test Citizen"

    # 2. Duplicate registration rejection
    dup_resp = client.post(
        "/auth/register",
        json={
            "email": unique_email,
            "password": "AnotherPassword123!",
            "role": "citizen",
        },
    )
    assert dup_resp.status_code == 400
    assert "already exists" in dup_resp.json()["detail"].lower()

    # 3. Invalid email rejection
    bad_email_resp = client.post(
        "/auth/register",
        json={
            "email": "not-an-email",
            "password": "Password123!",
            "role": "citizen",
        },
    )
    assert bad_email_resp.status_code == 400

    # 4. Successful login with registered credentials
    login_resp = client.post(
        "/auth/login",
        json={
            "email": unique_email,
            "password": "Password123!",
        },
    )
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert login_data["user"]["email"] == unique_email

    # 5. Token works for /auth/me
    token = login_data["access_token"]
    me_resp = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == unique_email

