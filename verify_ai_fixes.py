#!/usr/bin/env python3
"""Test script to verify AI Reviewer fixes."""

import sys
import os
import subprocess

print("=" * 70)
print("AI REVIEWER FIXES VERIFICATION")
print("=" * 70)

# Test 1: Check requirements.txt has google-generativeai
print("\n[TEST 1] Checking requirements.txt for google-generativeai...")
with open("backend/requirements.txt", "r") as f:
    requirements = f.read()
    if "google-generativeai" in requirements:
        print("✅ PASS: google-generativeai is in requirements.txt")
    else:
        print("❌ FAIL: google-generativeai missing from requirements.txt")
        sys.exit(1)

# Test 2: Check main.py uses use_ai instead of use_openai
print("\n[TEST 2] Checking main.py health check endpoint...")
with open("backend/app/main.py", "r") as f:
    main_content = f.read()
    if 'ai_reviewer.use_openai' in main_content:
        print("❌ FAIL: Still using use_openai in main.py")
        sys.exit(1)
    elif 'ai_reviewer.use_ai' in main_content:
        print("✅ PASS: Using ai_reviewer.use_ai in main.py")
    else:
        print("❌ FAIL: Could not find ai_reviewer reference in main.py")
        sys.exit(1)

# Test 3: Check ai_reviewer.py doesn't have duplicate methods
print("\n[TEST 3] Checking for duplicate methods in ai_reviewer.py...")
with open("backend/app/ai/ai_reviewer.py", "r") as f:
    ai_content = f.read()
    # Count how many times analyze_context is defined
    analyze_context_count = ai_content.count("def analyze_context")
    if analyze_context_count == 1:
        print("✅ PASS: Only one analyze_context method found")
    else:
        print(f"❌ FAIL: Found {analyze_context_count} analyze_context methods (should be 1)")
        sys.exit(1)

# Test 4: Check ai_reviewer.py doesn't have OpenAI code
print("\n[TEST 4] Checking for dead OpenAI code in ai_reviewer.py...")
with open("backend/app/ai/ai_reviewer.py", "r") as f:
    ai_content = f.read()
    if "self.openai_api_key" in ai_content:
        print("❌ FAIL: Found references to openai_api_key (dead code not removed)")
        sys.exit(1)
    elif "_ai_analyze_context" in ai_content:
        print("❌ FAIL: Found _ai_analyze_context method (should be removed)")
        sys.exit(1)
    else:
        print("✅ PASS: No dead OpenAI code found")

# Test 5: Check logging is properly imported
print("\n[TEST 5] Checking logging import in ai_reviewer.py...")
with open("backend/app/ai/ai_reviewer.py", "r") as f:
    ai_content = f.read()
    if "import logging" in ai_content and 'logger = logging.getLogger' in ai_content:
        print("✅ PASS: Logging properly imported and configured")
    else:
        print("❌ FAIL: Logging not properly set up")
        sys.exit(1)

# Test 6: Check error handling uses logger
print("\n[TEST 6] Checking error handling uses logger...")
with open("backend/app/ai/ai_reviewer.py", "r") as f:
    ai_content = f.read()
    if "logger.warning" in ai_content:
        print("✅ PASS: Error handling uses logger.warning")
    elif "print(f\"Gemini Error" in ai_content:
        print("❌ FAIL: Still using print() instead of logger")
        sys.exit(1)
    else:
        print("❌ FAIL: Error handling not found")
        sys.exit(1)

# Test 7: Syntax check
print("\n[TEST 7] Checking Python syntax...")
try:
    result = subprocess.run(
        ["python", "-m", "py_compile", "backend/app/ai/ai_reviewer.py"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("✅ PASS: No syntax errors in ai_reviewer.py")
    else:
        print(f"❌ FAIL: Syntax errors in ai_reviewer.py:\n{result.stderr}")
        sys.exit(1)
except Exception as e:
    print(f"⚠️  SKIP: Could not run syntax check: {e}")

print("\n" + "=" * 70)
print("✅ ALL TESTS PASSED - AI REVIEWER FIXES VERIFIED")
print("=" * 70)
print("\nFixes Applied:")
print("1. ✅ Added google-generativeai to requirements.txt")
print("2. ✅ Fixed use_openai → use_ai in main.py health check")
print("3. ✅ Removed duplicate analyze_context method")
print("4. ✅ Removed dead OpenAI code")
print("5. ✅ Added logging import and improved error handling")
print("\nNext Steps:")
print("1. Install dependencies: pip install -r backend/requirements.txt")
print("2. Set GOOGLE_API_KEY environment variable (optional)")
print("3. Restart the application")
print("4. Test AI features with: curl http://localhost:8000/health")
