"""License and IP compliance checking."""

import re
from typing import List, Dict, Tuple, Optional
from app.models import Violation, SeverityLevel, RuleCategory


class LicenseCompliance:
    """Check for license and IP compliance violations."""

    # Common SPDX license identifiers
    PERMISSIVE_LICENSES = {
        "MIT",
        "Apache-2.0",
        "Apache-2.0-only",
        "BSD-2-Clause",
        "BSD-3-Clause",
        "ISC",
        "MPL-2.0",
        "LGPL-2.1",
        "LGPL-3.0",
    }

    RESTRICTIVE_LICENSES = {
        "GPL-2.0",
        "GPL-2.0-only",
        "GPL-3.0",
        "GPL-3.0-only",
        "AGPL-3.0",
        "AGPL-3.0-only",
    }

    INCOMPATIBLE_LICENSES = {
        "UNKNOWN": "License not identified",
        "PROPRIETARY": "Proprietary license detected",
        "COMMERCIAL": "Commercial license with restrictions",
    }

    # Import patterns that might indicate copied code
    SUSPICIOUS_IMPORTS = [
        (r"from\s+some_library\s+import", "Placeholder import - likely from copied code"),
        (r"import\s+TODO\s+", "Placeholder import with TODO marker"),
        (r"import\s+\*\s+#\s*All", "Wildcard import - code review recommended"),
    ]

    # Patterns that indicate copied or template code
    COPY_PASTE_INDICATORS = [
        (r"# This is copied from", "Copied code marker"),
        (r"# Source:\s*", "Attribution comment (good practice)"),
        (r"# Based on", "Code derivative marker"),
        (r"/\*.*[Cc]opyright\s+\d{4}-\d{4}\s+\w+", "Copyright header - verify license compatibility"),
    ]

    @staticmethod
    def detect_license_declarations(code: str, file_path: str) -> List[Dict[str, str]]:
        """
        Detect license declarations in code.
        Returns list of detected license declarations.
        """
        licenses = []
        license_patterns = [
            (r"SPDX-License-Identifier:\s*([A-Za-z0-9\.\-]+)", "SPDX"),
            (r"License:\s*([A-Za-z0-9\.\-\s]+)", "License Comment"),
            (r"MIT", "MIT"),
            (r"Apache-2\.0|Apache License 2\.0", "Apache-2.0"),
            (r"GPL-3\.0|GNU General Public License v3", "GPL-3.0"),
        ]

        for line in code.split("\n"):
            for pattern, license_type in license_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    detected_license = match.group(1) if match.lastindex else license_type
                    licenses.append({
                        "type": license_type,
                        "detected": detected_license,
                        "line": line.strip(),
                    })

        return licenses

    @staticmethod
    def check_license_compatibility(
        detected_licenses: List[str],
        allowed_licenses: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Check if detected licenses are compatible with allowed list.
        Returns (is_compatible, incompatible_licenses).
        """
        incompatible = []
        for license_str in detected_licenses:
            if license_str not in allowed_licenses:
                incompatible.append(license_str)

        return len(incompatible) == 0, incompatible

    @staticmethod
    def detect_ip_risks(code: str, file_path: str) -> List[Violation]:
        """
        Detect potential IP and license compliance risks.
        """
        violations = []
        lines = code.split("\n")

        for line_number, line in enumerate(lines, 1):
            # Check for copy-paste indicators
            for pattern, message in LicenseCompliance.COPY_PASTE_INDICATORS:
                if re.search(pattern, line, re.IGNORECASE):
                    # If it's a proper attribution, it's informational
                    if "Source:" in line or "Based on" in line:
                        severity = SeverityLevel.INFO
                    else:
                        severity = SeverityLevel.MEDIUM

                    violation = Violation(
                        rule_id="IP-001",
                        rule_name="Code Derivative Detection",
                        category=RuleCategory.LICENSE,
                        severity=severity,
                        message=f"IP compliance check: {message}. Verify license compatibility.",
                        file_path=file_path,
                        line_number=line_number,
                        line_content=line.strip(),
                        cwe_id="CWE-1104",
                        owasp_category="IP/License Risk",
                    )
                    violations.append(violation)

            # Check for suspicious imports
            for pattern, message in LicenseCompliance.SUSPICIOUS_IMPORTS:
                if re.search(pattern, line, re.IGNORECASE):
                    violation = Violation(
                        rule_id="IP-002",
                        rule_name="Suspicious Import Pattern",
                        category=RuleCategory.LICENSE,
                        severity=SeverityLevel.MEDIUM,
                        message=f"IP risk: {message}",
                        file_path=file_path,
                        line_number=line_number,
                        line_content=line.strip(),
                        cwe_id="CWE-1104",
                        owasp_category="IP/License Risk",
                    )
                    violations.append(violation)

        return violations

    @staticmethod
    def detect_license_from_dependency(
        dependency_line: str,
        dependency_licenses: Dict[str, str]
    ) -> Optional[str]:
        """
        Detect license from a dependency line.
        dependency_licenses: dict mapping package names to their licenses.
        """
        for package, license_name in dependency_licenses.items():
            if package.lower() in dependency_line.lower():
                return license_name

        return None

    @staticmethod
    def check_license_violations(
        code: str,
        file_path: str,
        allowed_licenses: List[str]
    ) -> List[Violation]:
        """
        Check for license violations in code.
        """
        violations = []
        detected_licenses = LicenseCompliance.detect_license_declarations(code, file_path)

        for license_info in detected_licenses:
            detected = license_info["detected"]
            if detected not in allowed_licenses:
                violation = Violation(
                    rule_id="LICENSE-001",
                    rule_name="Incompatible License Detected",
                    category=RuleCategory.LICENSE,
                    severity=SeverityLevel.HIGH,
                    message=f"Detected license '{detected}' not in allowed list: {', '.join(allowed_licenses)}",
                    file_path=file_path,
                    line_number=1,
                    line_content=license_info["line"],
                    cwe_id="CWE-1104",
                    owasp_category="IP/License Risk",
                )
                violations.append(violation)

        return violations
