"""AI-assisted code review engine."""

import os
from typing import List, Optional, Dict, Tuple
import google.genai as genai
from app.models import Violation, SeverityLevel


class AIReviewer:
    """AI-assisted code review engine using Google Gemini."""

    def __init__(self):
        """Initialize Gemini AI reviewer."""
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.use_ai = self.api_key is not None
        
        if self.use_ai:
            genai.configure(api_key=self.api_key)
            # Using 1.5-flash for speed/cost, or 1.5-pro for deeper reasoning
            self.model_name = "gemini-1.5-flash" 
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction="You are a security expert reviewing code for vulnerabilities."
            )

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
            # Gemini generation config
            generation_config = genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=1000,
            )

            response = self.model.generate_content(
                prompt, 
                generation_config=generation_config
            )
            
            return self._parse_ai_response(response.text)

        except Exception as e:
            # Fall back to rule-based approach on error (e.g., Safety filters or API limits)
            print(f"Gemini Error: {e}")
            return self._rule_based_suggest_fix(violation)

    def _parse_ai_response(self, response_text: str) -> Tuple[str, str]:
        """Parse Gemini response into components."""
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
            response = self.model.generate_content(prompt)
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
                "# Properly attribute source code\n# Source: https://github.com/owner/repo\n# License: MIT",
                "Always include proper attribution and verify license compatibility when using external code.",
            ),
        }

        return fixes.get(violation.rule_id, ("# Review code", violation.message))

    def analyze_context(
        self,
        violation: Violation,
        surrounding_code: str
    ) -> Optional[str]:
        """
        Analyze the context of a violation using AI.
        Returns additional context or reasoning.

        Falls back to empty string if AI unavailable.
        """
        if self.use_openai:
            return self._ai_analyze_context(violation, surrounding_code)
        else:
            return ""

    def _ai_analyze_context(self, violation: Violation, surrounding_code: str) -> str:
        """Analyze context using OpenAI API."""
        try:
            import openai

            openai.api_key = self.openai_api_key

            prompt = f"""
Analyze the following code violation in context:

Violation: {violation.rule_name}
Message: {violation.message}

Code Context:
{surrounding_code}

Is this violation a false positive? Could it be a legitimate use case?
Provide your analysis in 2-3 sentences.
"""

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a security expert analyzing code violations.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=200,
            )

            return response.choices[0].message.content.strip()

        except Exception:
            return ""

    def generate_explanation(self, violation: Violation) -> str:
        """Generate a developer-friendly explanation for a violation."""
        explanations = {
            "SEC-001": "Hardcoded credentials can be exposed in version control. Store secrets in environment variables or secret management systems.",
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
            "SEC": "https://owasp.org/Top10/",
            "CWE": "https://cwe.mitre.org/",
            "PERF": "https://docs.python.org/3/library/profile.html",
            "AI": "https://github.com/github/copilot-safety",
            "IP": "https://opensource.org/licenses/",
        }

        for prefix, link in links.items():
            if violation.rule_id.startswith(prefix):
                return link

        return None
