"""Code analyzer for processing diffs and detecting violations."""

import re
from typing import List, Dict
from app.models import Violation, ScanResult, AnalysisRequest, SeverityLevel
from app.rules import SecurityRuleEngine
from datetime import datetime
import uuid


class CodeAnalyzer:
    """Main analyzer for scanning code."""

    @staticmethod
    def parse_diff(diff_content: str, file_path: str) -> str:
        """Extract the added/modified lines from a unified diff."""
        lines = diff_content.split("\n")
        added_code = []

        for line in lines:
            # Lines starting with '+' are additions (but skip '+++')
            if line.startswith("+") and not line.startswith("+++"):
                added_code.append(line[1:])  # Remove the leading '+'

        return "\n".join(added_code)

    @staticmethod
    def analyze_files(request: AnalysisRequest) -> List[Violation]:
        """Analyze files in the request for violations."""
        all_violations = []

        for file_path, diff_content in request.files.items():
            # Skip non-code files
            if not CodeAnalyzer._is_code_file(file_path):
                continue

            # Parse diff to get added code
            added_code = CodeAnalyzer.parse_diff(diff_content, file_path)

            if not added_code.strip():
                continue

            # Run security analysis
            violations = SecurityRuleEngine.scan_code(added_code, file_path)

            # Mark if this file is Copilot-generated
            if request.copilot_generated_files and file_path in request.copilot_generated_files:
                for violation in violations:
                    violation.is_copilot_generated = True

            all_violations.extend(violations)

        return all_violations

    @staticmethod
    def _is_code_file(file_path: str) -> bool:
        """Check if file is a code file we should analyze."""
        code_extensions = {
            ".py",
            ".js",
            ".ts",
            ".tsx",
            ".jsx",
            ".java",
            ".cs",
            ".cpp",
            ".c",
            ".go",
            ".rb",
            ".php",
            ".sql",
            ".scala",
            ".kt",
        }
        return any(file_path.endswith(ext) for ext in code_extensions)

    @staticmethod
    def create_scan_result(
        request: AnalysisRequest, violations: List[Violation]
    ) -> ScanResult:
        """Create a scan result from analysis."""
        return ScanResult(
            scan_id=str(uuid.uuid4()),
            repo_name=request.repo_name,
            pr_number=request.pr_number,
            commit_hash=request.commit_hash,
            violations=violations,
            timestamp=datetime.utcnow(),
            scan_status="completed",
        )
