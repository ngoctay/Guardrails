"""Security rules for detecting common vulnerabilities."""

import re
from typing import List, Tuple, Optional
from app.models import Violation, SeverityLevel, RuleCategory


class SecurityRuleEngine:
    """Engine for applying security rules to code."""

    # Rule definitions
    HARDCODED_SECRET_PATTERNS = [
        (r"api[_-]?key\s*=\s*['\"]([^'\"]{8,})['\"]", "Hardcoded API Key"),
        (r"password\s*=\s*['\"]([^'\"]{8,})['\"]", "Hardcoded Password"),
        (r"secret\s*=\s*['\"]([^'\"]{8,})['\"]", "Hardcoded Secret"),
        (r"token\s*=\s*['\"]([^'\"]{8,})['\"]", "Hardcoded Token"),
        (r"(AKIA[0-9A-Z]{16})", "AWS Access Key ID"),
        (r"aws_secret_access_key\s*=\s*['\"]([^'\"]+)['\"]", "AWS Secret Key"),
        (r"private[_-]?key\s*=\s*['\"]", "Hardcoded Private Key"),
        (r"github[_-]?token\s*=\s*['\"]", "Hardcoded GitHub Token"),
        (r"docker[_-]?password\s*=\s*['\"]", "Hardcoded Docker Password"),
        (r"database[_-]?url\s*=.*://.*:.*@", "Database credentials in connection string"),
    ]

    SQL_INJECTION_PATTERNS = [
        (r"execute\s*\(\s*['\"].*\{.*\}.*['\"]", "SQL Injection: String interpolation in query"),
        (r"query\s*\(\s*f['\"].*\{.*\}.*['\"]", "SQL Injection: F-string in SQL query"),
        (r"SELECT\s+.*\+\s*str\(", "SQL Injection: String concatenation in query"),
        (r"\.format\s*\(\s*.*\)\s*\)", "SQL Injection: format() in SQL query"),
        (r"execute.*\(\s*user_input", "SQL Injection: Direct user input in execute"),
    ]

    INSECURE_DESERIALIZATION_PATTERNS = [
        (r"pickle\.loads\s*\(", "Insecure Deserialization: pickle.loads() with untrusted data"),
        (r"json\.loads\s*\(\s*user_input", "Insecure JSON deserialization of user input"),
        (r"yaml\.load\s*\(\s*[^,]*\)", "Insecure YAML deserialization: Missing Loader"),
        (r"cPickle\.loads\s*\(", "Insecure deserialization: cPickle.loads()"),
        (r"marshal\.loads\s*\(", "Insecure deserialization: marshal.loads()"),
    ]

    UNSAFE_EXECUTION_PATTERNS = [
        (r"eval\s*\(", "Unsafe Code Execution: eval()"),
        (r"exec\s*\(", "Unsafe Code Execution: exec()"),
        (r"subprocess\.call\s*\(\s*cmd\s*,\s*shell\s*=\s*True", "Unsafe Shell Execution"),
        (r"subprocess\.Popen\s*\(.*shell\s*=\s*True", "Unsafe subprocess execution with shell"),
        (r"os\.system\s*\(", "Unsafe System Command Execution: os.system()"),
        (r"os\.popen\s*\(", "Unsafe pipe execution: os.popen()"),
    ]

    WEAK_CRYPTO_PATTERNS = [
        (r"hashlib\.md5\s*\(", "Weak Cryptography: MD5 is insecure"),
        (r"hashlib\.sha1\s*\(", "Weak Cryptography: SHA1 is deprecated"),
        (r"DES\s*\(", "Weak Cryptography: DES is insecure"),
        (r"RSA\.generate\s*\(\s*512", "Weak Cryptography: RSA key size < 2048"),
        (r"ECB", "Weak Cryptography: ECB mode is insecure"),
    ]

    INSECURE_HEADERS_PATTERNS = [
        (r"X-Frame-Options.*ALLOW", "Insecure Header: X-Frame-Options allows framing"),
        (r"Strict-Transport-Security.*\s*=\s*0", "Missing HSTS header"),
        (r"X-Content-Type-Options.*nosniff", "Missing X-Content-Type-Options header"),
    ]

    UNSAFE_FILE_OPERATIONS_PATTERNS = [
        (r"open\s*\(\s*user_input", "Unsafe file operation with user input"),
        (r"\.readlines\(\)", "Potential XXE vulnerability: Reading file without validation"),
        (r"zipfile\.ZipFile\s*\(\s*user_input", "Unsafe ZIP file handling"),
    ]

    INSECURE_RANDOM_PATTERNS = [
        (r"random\.randint\s*\(", "Weak randomness: random module is not cryptographically secure"),
        (r"random\.choice\s*\(", "Weak randomness: random module should not be used for security"),
        (r"random\.seed\s*\(\s*['\"]", "Weak randomness: seeding with predictable value"),
    ]

    COMPLIANCE_PATTERNS = [
        (r"TODO.*SECURITY", "Security TODO found - needs resolution"),
        (r"FIXME.*SECURITY", "Security FIXME found - needs resolution"),
        (r"HACK.*SECURITY", "Security HACK found - needs immediate resolution"),
        (r"BUG.*SECURITY", "Security BUG found - needs immediate resolution"),
    ]

    LOGGING_PATTERNS = [
        (r"print\s*\(\s*.*password", "Logging potential sensitive data: password"),
        (r"print\s*\(\s*.*token", "Logging potential sensitive data: token"),
        (r"print\s*\(\s*.*secret", "Logging potential sensitive data: secret"),
        (r"print\s*\(\s*.*key", "Logging potential sensitive data: key"),
    ]

    DEPENDENCY_PATTERNS = [
        (r"requests\.get\s*\(\s*url\s*,\s*verify\s*=\s*False", "Insecure HTTPS: SSL verification disabled"),
        (r"urllib\.urlopen\s*\(\s*url\s*\)", "Deprecated urllib usage"),
    ]

    PERFORMANCE_PATTERNS = [
        (r"SELECT\s+\*\s+FROM", "Performance: SELECT * should specify columns"),
        (r"for\s+\w+\s+in\s+\w+:\s+.*query", "Performance: Query in loop detected"),
        (r"\.count\(\)\s*==\s*0", "Performance: Use .exists() instead of .count() == 0"),
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

            # Check insecure headers
            violations.extend(
                SecurityRuleEngine.scan_line(
                    line,
                    file_path,
                    line_number,
                    SecurityRuleEngine.INSECURE_HEADERS_PATTERNS,
                    "SEC-006",
                    "CWE-693",
                    "A05:2021 – Broken Access Control",
                    SeverityLevel.MEDIUM,
                )
            )

            # Check unsafe file operations
            violations.extend(
                SecurityRuleEngine.scan_line(
                    line,
                    file_path,
                    line_number,
                    SecurityRuleEngine.UNSAFE_FILE_OPERATIONS_PATTERNS,
                    "SEC-007",
                    "CWE-434",
                    "A04:2021 – Insecure Deserialization",
                    SeverityLevel.HIGH,
                )
            )

            # Check insecure random
            violations.extend(
                SecurityRuleEngine.scan_line(
                    line,
                    file_path,
                    line_number,
                    SecurityRuleEngine.INSECURE_RANDOM_PATTERNS,
                    "SEC-008",
                    "CWE-338",
                    "A02:2021 – Cryptographic Failures",
                    SeverityLevel.HIGH,
                )
            )

            # Check compliance issues
            violations.extend(
                SecurityRuleEngine.scan_line(
                    line,
                    file_path,
                    line_number,
                    SecurityRuleEngine.COMPLIANCE_PATTERNS,
                    "COMP-001",
                    "CWE-TODO",
                    "Development Process Issue",
                    SeverityLevel.MEDIUM,
                )
            )

            # Check logging issues
            violations.extend(
                SecurityRuleEngine.scan_line(
                    line,
                    file_path,
                    line_number,
                    SecurityRuleEngine.LOGGING_PATTERNS,
                    "SEC-009",
                    "CWE-532",
                    "A09:2021 – Logging and Monitoring Failures",
                    SeverityLevel.MEDIUM,
                )
            )

            # Check dependency issues
            violations.extend(
                SecurityRuleEngine.scan_line(
                    line,
                    file_path,
                    line_number,
                    SecurityRuleEngine.DEPENDENCY_PATTERNS,
                    "SEC-010",
                    "CWE-295",
                    "A02:2021 – Cryptographic Failures",
                    SeverityLevel.HIGH,
                )
            )

            # Check performance issues
            violations.extend(
                SecurityRuleEngine.scan_line(
                    line,
                    file_path,
                    line_number,
                    SecurityRuleEngine.PERFORMANCE_PATTERNS,
                    "PERF-001",
                    "CWE-1061",
                    "Performance Issue",
                    SeverityLevel.LOW,
                )
            )

        return violations
