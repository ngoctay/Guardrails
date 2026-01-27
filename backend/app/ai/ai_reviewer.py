"""AI-assisted code review engine."""

import os
import logging
from typing import List, Optional, Dict, Tuple
from google import genai
from app.models import Violation, SeverityLevel

logger = logging.getLogger(__name__)


class AIReviewer:
    """AI-assisted code review engine using Google Gemini (Gen AI SDK v1)."""

    def __init__(self):
        """Initialize Google Gen AI Client."""
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.use_ai = self.api_key is not None
        
        if self.use_ai:
            # Using the new google.genai API
            self.model_name = "gemini-3-flash-preview" 
            # Create client with API key
            self.client = genai.Client(api_key=self.api_key)
            self.model = self.client.models.generate_content

    def suggest_fix(self, violation: Violation) -> Tuple[str, str]:
        """
        Generate a suggested fix for a violation using AI.
        Returns (suggested_code, explanation).
        """
        if self.use_ai:
            return self._ai_suggest_fix(violation)
        else:
            return self._rule_based_suggest_fix(violation)

    def _ai_suggest_fix(self, violation: Violation) -> Tuple[str, str]:
        """Generate fix using Google Gemini API."""
        try:
            prompt = f"""
Analyze this code violation and provide a fix.

Rule: {violation.rule_name}
Severity: {violation.severity.value}
Message: {violation.message}
Code: {violation.line_content}
File: {violation.file_path}

Provide:
1. A corrected version of the code
2. A brief explanation of why it was vulnerable
3. Best practices to prevent similar issues

Format your response exactly as:
CORRECTED_CODE:
[code here]

EXPLANATION:
[explanation here]

BEST_PRACTICES:
[practices here]
"""
            # Call Gemini API using the new client
            # Try primary model first, fall back to alternatives if needed
            model_to_use = self.model_name
            try:
                response = self.client.models.generate_content(
                    model=model_to_use,
                    contents=prompt,
                    config={
                        "temperature": 0.3,
                        "max_output_tokens": 1000,
                    }
                )
            except Exception as e:
                # If model not found, try gemini-pro as fallback
                if "404" in str(e) or "not found" in str(e).lower():
                    logger.info(f"Model {model_to_use} not found, trying gemini-pro")
                    model_to_use = "gemini-pro"
                    response = self.client.models.generate_content(
                        model=model_to_use,
                        contents=prompt,
                        config={
                            "temperature": 0.3,
                            "max_output_tokens": 1000,
                        }
                    )
                else:
                    raise
            
            # Access text directly from the response object
            return self._parse_ai_response(response.text)

        except Exception as e:
            # Fall back to rule-based approach on error (e.g., Safety filters or API limits)
            logger.warning(
                f"Failed to generate AI suggestion for {violation.rule_id}: {type(e).__name__}: {e}. "
                f"Using rule-based fallback."
            )
            return self._rule_based_suggest_fix(violation)

    def _parse_ai_response(self, response_text: str) -> Tuple[str, str]:
        """Parse Gemini response into components."""
        if not response_text:
            return "", "AI generation returned empty response."

        suggested_code = ""
        explanation = ""

        lines = response_text.split("\n")
        section = None

        for line in lines:
            if "CORRECTED_CODE:" in line:
                section = "code"
            elif "EXPLANATION:" in line:
                section = "explanation"
            elif "BEST_PRACTICES:" in line:
                section = "best_practices"
            elif section == "code":
                # Strip markdown code blocks if Gemini includes them
                clean_line = line.replace("```python", "").replace("```", "")
                if clean_line.strip() or not line.startswith("```"):
                    suggested_code += clean_line + "\n"
            elif section == "explanation":
                explanation += line + "\n"

        return suggested_code.strip(), explanation.strip()

    def analyze_context(self, violation: Violation, surrounding_code: str) -> str:
        """Analyze the context of a violation using Gemini."""
        if not self.use_ai:
            return ""

        try:
            prompt = f"""
Analyze the following code violation in context:

Violation: {violation.rule_name}
Message: {violation.message}

Code Context:
{surrounding_code}

Is this violation a false positive? Could it be a legitimate use case?
Provide your analysis in 2-3 sentences.
"""
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text.strip()
        except Exception:
            return ""

    def _rule_based_suggest_fix(self, violation: Violation) -> Tuple[str, str]:
        """Generate rule-based fix suggestions."""
        fixes = {
            "SEC-001": (
                "# Use environment variables for secrets\nimport os\napi_key = os.getenv('API_KEY')",
                "Hardcoded secrets expose sensitive data. Always use environment variables or secret management systems.",
            ),
            "SEC-002": (
                "# Use parameterized queries\nquery = 'SELECT * FROM users WHERE id = %s'\ncursor.execute(query, (user_id,))",
                "SQL injection allows attackers to manipulate queries. Always use parameterized queries with prepared statements.",
            ),
            "SEC-003": (
                "import json\ndata = json.loads(user_input)  # JSON is safe\n# For YAML, use yaml.safe_load()",
                "Insecure deserialization can execute arbitrary code. Use safe deserializers or validate input.",
            ),
            "SEC-004": (
                "# Avoid eval and exec\nimport ast\ntree = ast.parse(user_input, mode='eval')",
                "eval() and exec() execute arbitrary Python code. Use ast.parse() or other safe alternatives.",
            ),
            "SEC-005": (
                "import hashlib\nhash_obj = hashlib.sha256(data)  # Use SHA256 instead",
                "MD5 and SHA1 are cryptographically broken. Use SHA256 or stronger algorithms.",
            ),
            "AI-001": (
                "# Implement full logic instead of leaving as TODO\ndef handle_request(request):\n    # Your implementation here",
                "Incomplete AI-generated code can cause runtime errors. Always implement full logic.",
            ),
            "IP-001": (
                "# Properly attribute source code\n# Source: [https://github.com/owner/repo](https://github.com/owner/repo)\n# License: MIT",
                "Always include proper attribution and verify license compatibility when using external code.",
            ),
        }

        return fixes.get(violation.rule_id, ("# Review code", violation.message))

    def generate_explanation(self, violation: Violation) -> str:
        """Generate a developer-friendly explanation for a violation."""
        explanations = {
            "SEC-001": "Hardcoded credentials can be exposed in version control. Store secrets in environment variables.",
            "SEC-002": "SQL injection allows attackers to manipulate database queries. Always use parameterized queries.",
            "SEC-003": "Unsafe deserialization can lead to remote code execution. Use safe alternatives like json.loads().",
            "SEC-004": "eval() and exec() execute arbitrary code. Avoid them in production.",
            "SEC-005": "MD5 and SHA1 are weak. Use SHA256 or stronger algorithms.",
            "SEC-006": "Insecure headers can enable attacks. Set appropriate security headers.",
            "SEC-007": "Unsafe file operations can enable directory traversal or XXE attacks.",
            "SEC-008": "random module is not cryptographically secure. Use secrets module instead.",
            "SEC-009": "Logging sensitive data can expose secrets. Sanitize logs.",
            "SEC-010": "SSL verification disabled allows MITM attacks. Always verify certificates.",
            "AI-001": "Incomplete AI-generated code needs full implementation.",
            "IP-001": "Always verify license compatibility when using external code.",
        }

        return explanations.get(violation.rule_id, violation.message)

    def suggest_category_link(self, violation: Violation) -> Optional[str]:
        """Suggest documentation link for a violation category."""
        links = {
            "SEC": "[https://owasp.org/Top10/](https://owasp.org/Top10/)",
            "CWE": "[https://cwe.mitre.org/](https://cwe.mitre.org/)",
            "PERF": "[https://docs.python.org/3/library/profile.html](https://docs.python.org/3/library/profile.html)",
            "AI": "[https://github.com/github/copilot-safety](https://github.com/github/copilot-safety)",
            "IP": "[https://opensource.org/licenses/](https://opensource.org/licenses/)",
        }

        for prefix, link in links.items():
            if violation.rule_id.startswith(prefix):
                return link

        return None