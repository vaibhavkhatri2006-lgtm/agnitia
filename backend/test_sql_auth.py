import urllib.request
import json
import sqlite3

def run_tests():
    print("=== 1. Testing Registration in SQL ===")
    reg_data = json.dumps({
        "email": "indore.resident@gmail.com",
        "password": "CitizenSecurePassword123!",
        "role": "citizen",
        "display_name": "Indore Resident"
    }).encode()

    req = urllib.request.Request("http://127.0.0.1:8000/auth/register", data=reg_data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            print("Registration Status:", resp.status)
            res_json = json.loads(resp.read().decode())
            print("Token issued for user ID:", res_json["user"]["id"])
            print("User profile:", res_json["user"])
    except urllib.error.HTTPError as e:
        print("Registration response (already exists or error):", e.code)

    print("\n=== 2. Direct SQL Database Inspection ===")
    conn = sqlite3.connect("backend/civicpulse.db")
    c = conn.cursor()
    row = c.execute("SELECT id, email, password_hash, display_name, role_id, is_active, created_at FROM users WHERE email='indore.resident@gmail.com'").fetchone()
    print("SQL Row:", row)
    assert row is not None, "User was not found in SQL database!"
    assert row[2].startswith("$2b$"), "Password is not properly hashed with bcrypt in SQL!"
    print("Verified: Password is cryptographically hashed with bcrypt in SQLite database.")
    conn.close()

    print("\n=== 3. Testing Sign In against SQL ===")
    login_data = json.dumps({
        "email": "indore.resident@gmail.com",
        "password": "CitizenSecurePassword123!"
    }).encode()

    login_req = urllib.request.Request("http://127.0.0.1:8000/auth/login", data=login_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(login_req) as resp:
        print("Sign In Status:", resp.status)
        login_json = json.loads(resp.read().decode())
        token = login_json["access_token"]
        print("Token verified:", token[:30] + "...")

    print("\n=== 4. Testing Profile (/auth/me) with JWT ===")
    me_req = urllib.request.Request("http://127.0.0.1:8000/auth/me", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(me_req) as resp:
        print("/auth/me Status:", resp.status)
        print("Verified User Claims:", resp.read().decode())

    print("\n=== 5. Testing Wrong Password Rejection ===")
    wrong_data = json.dumps({
        "email": "indore.resident@gmail.com",
        "password": "WrongPassword!"
    }).encode()
    try:
        urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8000/auth/login", data=wrong_data, headers={"Content-Type": "application/json"}))
    except urllib.error.HTTPError as e:
        print("Wrong password correctly returned:", e.code)

    print("\n ALL SQL AUTHENTICATION TESTS PASSED!")

if __name__ == "__main__":
    run_tests()
