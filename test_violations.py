# Test file with security violations for Guardrails scanning

api_key = "sk-1234567890-test"  # SEC-001: Hardcoded API Key
password = "admin_password_123"  # SEC-001: Hardcoded Password  
token = "ghp_abcdef123456"  # SEC-001: Hardcoded Token

# This should trigger violations
import sqlite3

def login(user_input):
    db = sqlite3.connect(":memory:")
    # SEC-002: SQL Injection
    query = f"SELECT * FROM users WHERE username = '{user_input}'"
    db.execute(query)
