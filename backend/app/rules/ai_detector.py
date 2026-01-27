"""AI/Copilot-generated code detection and analysis."""

import re
from typing import List, Tuple, Optional
from app.models import Violation, SeverityLevel, RuleCategory


class AIDetector:
    """Detector for AI-generated code patterns and issues."""

    # Patterns that indicate Copilot-generated code
    COPILOT_INDICATORS = [
        (r"# This is a\s+", "Copilot starter comment pattern"),
        (r"# TODO: Implement", "Generic TODO comment pattern"),
        (r"# Replace with your", "Placeholder pattern"),
        (r"# Add your logic here", "Generic implementation placeholder"),
        (r"pass\s*#\s*TODO", "Incomplete stub with TODO"),
    ]

    # Suspicious patterns common in AI-generated code
    AI_RISK_PATTERNS = [
        (r"@app\.route.*\n\s+def\s+\w+\(\):\s*\n\s+return", "Oversimplified route handler"),
        (r"except\s*:\s*pass", "Bare except without handling"),
        (r"except\s+Exception\s*:\s*pass", "Generic exception suppression"),
        (r"if\s+\w+:\s*pass\s*else:", "Empty if branch"),
        (r"# type:\s*ignore", "Type checking ignored"),
        (r"# noqa", "Linting warning suppressed"),
    ]

    # Patterns that suggest incomplete AI implementation
    INCOMPLETE_PATTERNS = [
        (r"def\s+\w+\([^)]*\):\s*pass\s*$", "Empty function stub"),
        (r"raise\s+NotImplementedError", "Unimplemented required method"),
        (r"def\s+\w+\([^)]*\):\s*\.\.\.\s*$", "Ellipsis placeholder function"),
        (r"TODO.*CRITICAL", "Critical unfinished work"),
    ]

    @staticmethod
    def detect_ai_indicators(code: str, file_path: str) -> List[Tuple[str, int, str]]:
        """
        Detect indicators that code might be AI-generated.
        Returns list of (indicator_type, line_number, pattern).
        """
        indicators = []
        lines = code.split("\n")

        for line_number, line in enumerate(lines, 1):
            for pattern, indicator_type in AIDetector.COPILOT_INDICATORS:
                if re.search(pattern, line, re.IGNORECASE):
                    indicators.append((indicator_type, line_number, line.strip()))

        return indicators

    @staticmethod
    def detect_ai_risks(code: str, file_path: str) -> List[Violation]:
        """
        Detect risky patterns in AI-generated code.
        """
        violations = []
        lines = code.split("\n")

        for line_number, line in enumerate(lines, 1):
            # Skip comments and empty lines
            if line.strip().startswith("#") or not line.strip():
                continue

            # Check for incomplete implementations
            for pattern, message in AIDetector.INCOMPLETE_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    violation = Violation(
                        rule_id="AI-001",
                        rule_name="Incomplete AI-Generated Code",
                        category=RuleCategory.CODE_QUALITY,
                        severity=SeverityLevel.MEDIUM,
                        message=f"Potentially incomplete AI-generated implementation: {message}",
                        file_path=file_path,
                        line_number=line_number,
                        line_content=line.strip(),
                        cwe_id="CWE-1077",
                        owasp_category="A06:2021 – Vulnerable and Outdated Components",
                        is_copilot_generated=True,
                    )
                    violations.append(violation)

            # Check for risky patterns in AI code
            for pattern, message in AIDetector.AI_RISK_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    violation = Violation(
                        rule_id="AI-002",
                        rule_name="Risky AI-Generated Pattern",
                        category=RuleCategory.CODE_QUALITY,
                        severity=SeverityLevel.MEDIUM,
                        message=f"AI-generated code with risky pattern: {message}",
                        file_path=file_path,
                        line_number=line_number,
                        line_content=line.strip(),
                        cwe_id="CWE-1050",
                        owasp_category="Code Quality Issue",
                        is_copilot_generated=True,
                    )
                    violations.append(violation)

        return violations

    @staticmethod
    def suggest_copilot_context(violations: List[Violation]) -> str:
        """
        Generate context for stricter guardrails on Copilot-generated code.
        """
        context = ""
        copilot_violations = [v for v in violations if v.is_copilot_generated]

        if copilot_violations:
            context = f"\n⚠️ **AI-Generated Code Alert**: {len(copilot_violations)} issues found in Copilot-generated code.\n"
            context += "This code received stricter analysis due to AI origin. Human review recommended.\n"

        return context
