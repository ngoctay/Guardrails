"""Security rules for detecting common vulnerabilities."""

import re
from typing import List, Tuple
from app.models import Violation, SeverityLevel, RuleCategory


class SecurityRuleEngine:
    """Engine for applying security rules to code."""

    # Rule definitions
    HARDCODED_SECRET_PATTERNS = [
        (r"api[_-]?key\s*=\s*['\"]([^'\"]+)['\"]", "Hardcoded API Key"),
        (r"password\s*=\s*['\"]([^'\"]+)['\"]", "Hardcoded Password"),
        (r"secret\s*=\s*['\"]([^'\"]+)['\"]", "Hardcoded Secret"),
        (r"token\s*=\s*['\"]([^'\"]+)['\"]", "Hardcoded Token"),
        (r"(AKIA[0-9A-Z]{16})", "AWS Access Key ID"),
        (r"aws_secret_access_key\s*=\s*['\"]([^'\"]+)['\"]", "AWS Secret Key"),
    ]

    SQL_INJECTION_PATTERNS = [
        (r"execute\s*\(\s*['\"].*\{.*\}.*['\"]", "SQL Injection: String interpolation in query"),
        (r"query\s*\(\s*f['\"].*\{.*\}.*['\"]", "SQL Injection: F-string in SQL query"),
        (r"SELECT.*\+.*str\(", "SQL Injection: String concatenation in query"),
    ]

    INSECURE_DESERIALIZATION_PATTERNS = [
        (r"pickle\.loads\s*\(", "Insecure Deserialization: pickle.loads() with untrusted data"),
        (r"json\.loads\s*\(\s*user_input", "Insecure JSON deserialization of user input"),
        (r"yaml\.load\s*\(\s*[^,]*\)", "Insecure YAML deserialization: Missing Loader"),
    ]

    UNSAFE_EXECUTION_PATTERNS = [
        (r"eval\s*\(", "Unsafe Code Execution: eval()"),
        (r"exec\s*\(", "Unsafe Code Execution: exec()"),
        (r"subprocess\.call\s*\(\s*cmd\s*,\s*shell\s*=\s*True", "Unsafe Shell Execution"),
        (r"os\.system\s*\(", "Unsafe System Command Execution: os.system()"),
    ]

    WEAK_CRYPTO_PATTERNS = [
        (r"hashlib\.md5\s*\(", "Weak Cryptography: MD5 is insecure"),
        (r"hashlib\.sha1\s*\(", "Weak Cryptography: SHA1 is deprecated"),
        (r"DES\s*\(", "Weak Cryptography: DES is insecure"),
    ]

    @staticmethod
    def scan_line(
        line: str,
        file_path: str,
        line_number: int,
        patterns: List[Tuple[str, str]],
        rule_id: str,
        cwe_id: str,
        owasp_category: str,
        severity: SeverityLevel,
    ) -> List[Violation]:
        """Scan a single line against patterns."""
        violations = []

        for pattern, message in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                violation = Violation(
                    rule_id=rule_id,
                    rule_name=message,
                    category=RuleCategory.SECURITY,
                    severity=severity,
                    message=f"{message}. This could expose sensitive data or enable attacks.",
                    file_path=file_path,
                    line_number=line_number,
                    line_content=line.strip(),
                    cwe_id=cwe_id,
                    owasp_category=owasp_category,
                )
                violations.append(violation)
                break

        return violations

    @staticmethod
    def scan_code(code: str, file_path: str) -> List[Violation]:
        """Scan code for security violations."""
        violations = []
        lines = code.split("\n")

        for line_number, line in enumerate(lines, 1):
            # Skip comments and empty lines
            if line.strip().startswith("#") or line.strip().startswith("//") or not line.strip():
                continue

            # Check hardcoded secrets
            violations.extend(
                SecurityRuleEngine.scan_line(
                    line,
                    file_path,
                    line_number,
                    SecurityRuleEngine.HARDCODED_SECRET_PATTERNS,
                    "SEC-001",
                    "CWE-798",
                    "A02:2021 – Cryptographic Failures",
                    SeverityLevel.CRITICAL,
                )
            )

            # Check SQL injection
            violations.extend(
                SecurityRuleEngine.scan_line(
                    line,
                    file_path,
                    line_number,
                    SecurityRuleEngine.SQL_INJECTION_PATTERNS,
                    "SEC-002",
                    "CWE-89",
                    "A03:2021 – Injection",
                    SeverityLevel.CRITICAL,
                )
            )

            # Check insecure deserialization
            violations.extend(
                SecurityRuleEngine.scan_line(
                    line,
                    file_path,
                    line_number,
                    SecurityRuleEngine.INSECURE_DESERIALIZATION_PATTERNS,
                    "SEC-003",
                    "CWE-502",
                    "A08:2021 – Software and Data Integrity Failures",
                    SeverityLevel.HIGH,
                )
            )

            # Check unsafe execution
            violations.extend(
                SecurityRuleEngine.scan_line(
                    line,
                    file_path,
                    line_number,
                    SecurityRuleEngine.UNSAFE_EXECUTION_PATTERNS,
                    "SEC-004",
                    "CWE-95",
                    "A03:2021 – Injection",
                    SeverityLevel.CRITICAL,
                )
            )

            # Check weak cryptography
            violations.extend(
                SecurityRuleEngine.scan_line(
                    line,
                    file_path,
                    line_number,
                    SecurityRuleEngine.WEAK_CRYPTO_PATTERNS,
                    "SEC-005",
                    "CWE-327",
                    "A02:2021 – Cryptographic Failures",
                    SeverityLevel.HIGH,
                )
            )

        return violations
