"""Policy management and enforcement engine."""

from typing import List, Dict, Optional
from enum import Enum
from app.models import Violation, SeverityLevel, EnforcementMode


class PolicyEngine:
    """Engine for managing and enforcing policies."""

    def __init__(self):
        """Initialize policy engine."""
        self.policies: Dict[str, "Policy"] = {}
        self.default_policy = self._create_default_policy()

    def _create_default_policy(self) -> "Policy":
        """Create default policy."""
        return Policy(
            name="default",
            enforcement_mode=EnforcementMode.WARNING,
            block_on_critical=True,
            block_on_high=False,
            enable_security_checks=True,
            enable_compliance_checks=True,
            enable_quality_checks=False,
            allowed_licenses=["MIT", "Apache-2.0", "GPL-3.0", "BSD-3-Clause"],
        )

    def register_policy(self, policy: "Policy") -> None:
        """Register a policy."""
        self.policies[policy.name] = policy

    def get_policy(self, repo_name: str) -> "Policy":
        """Get policy for a repository."""
        # Check for repo-specific policy
        if repo_name in self.policies:
            return self.policies[repo_name]
        # Fall back to organization policy
        org_name = repo_name.split("/")[0]
        if org_name in self.policies:
            return self.policies[org_name]
        # Use default
        return self.default_policy

    def enforce_policy(
        self,
        violations: List[Violation],
        repo_name: str
    ) -> "EnforcementResult":
        """
        Enforce policy on violations.
        Returns EnforcementResult with enforcement decisions.
        """
        policy = self.get_policy(repo_name)
        result = EnforcementResult()

        # Filter violations based on policy
        filtered_violations = []
        for violation in violations:
            # Check if this category is enabled
            if violation.category.value == "security" and not policy.enable_security_checks:
                result.filtered_violations.append(violation)
                continue
            if violation.category.value == "compliance" and not policy.enable_compliance_checks:
                result.filtered_violations.append(violation)
                continue
            if violation.category.value == "code_quality" and not policy.enable_quality_checks:
                result.filtered_violations.append(violation)
                continue

            filtered_violations.append(violation)

        result.violations = filtered_violations

        # Determine enforcement level
        critical_count = sum(1 for v in filtered_violations if v.severity == SeverityLevel.CRITICAL)
        high_count = sum(1 for v in filtered_violations if v.severity == SeverityLevel.HIGH)

        result.enforcement_mode = policy.enforcement_mode

        if policy.block_on_critical and critical_count > 0:
            result.should_block = True
            result.block_reason = f"Blocking due to {critical_count} critical violation(s)"

        elif policy.block_on_high and high_count > 0:
            result.should_block = True
            result.block_reason = f"Blocking due to {high_count} high severity violation(s)"

        # Check license violations
        license_violations = [v for v in filtered_violations if v.category.value == "license"]
        if license_violations and policy.enforcement_mode == EnforcementMode.BLOCKING:
            result.should_block = True
            result.block_reason = f"License violations detected: {len(license_violations)}"

        return result

    def create_override_token(self, repo_name: str, reason: str) -> str:
        """Create an override token for blocking violations."""
        import hashlib
        import json
        from datetime import datetime, timedelta

        payload = {
            "repo": repo_name,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
            "expires": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
        }
        payload_str = json.dumps(payload)
        token = hashlib.sha256(payload_str.encode()).hexdigest()
        return token

    def validate_override_token(self, token: str, repo_name: str) -> bool:
        """Validate an override token."""
        # In production, verify token signature and expiration
        # This is a simplified implementation
        return len(token) == 64  # SHA256 hex length


class Policy:
    """Represents a policy for code review enforcement."""

    def __init__(
        self,
        name: str,
        enforcement_mode: EnforcementMode = EnforcementMode.WARNING,
        block_on_critical: bool = True,
        block_on_high: bool = False,
        enable_security_checks: bool = True,
        enable_compliance_checks: bool = True,
        enable_quality_checks: bool = False,
        allowed_licenses: Optional[List[str]] = None,
        custom_rules: Optional[Dict] = None,
    ):
        """Initialize policy."""
        self.name = name
        self.enforcement_mode = enforcement_mode
        self.block_on_critical = block_on_critical
        self.block_on_high = block_on_high
        self.enable_security_checks = enable_security_checks
        self.enable_compliance_checks = enable_compliance_checks
        self.enable_quality_checks = enable_quality_checks
        self.allowed_licenses = allowed_licenses or ["MIT", "Apache-2.0", "GPL-3.0", "BSD-3-Clause"]
        self.custom_rules = custom_rules or {}

    def to_dict(self) -> dict:
        """Convert policy to dictionary."""
        return {
            "name": self.name,
            "enforcement_mode": self.enforcement_mode.value,
            "block_on_critical": self.block_on_critical,
            "block_on_high": self.block_on_high,
            "enable_security_checks": self.enable_security_checks,
            "enable_compliance_checks": self.enable_compliance_checks,
            "enable_quality_checks": self.enable_quality_checks,
            "allowed_licenses": self.allowed_licenses,
            "custom_rules": self.custom_rules,
        }


class EnforcementResult:
    """Result of policy enforcement."""

    def __init__(self):
        """Initialize enforcement result."""
        self.violations: List[Violation] = []
        self.filtered_violations: List[Violation] = []  # Violations filtered by policy
        self.should_block: bool = False
        self.block_reason: Optional[str] = None
        self.enforcement_mode: EnforcementMode = EnforcementMode.WARNING
        self.override_token: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert result to dictionary."""
        return {
            "violation_count": len(self.violations),
            "filtered_count": len(self.filtered_violations),
            "should_block": self.should_block,
            "block_reason": self.block_reason,
            "enforcement_mode": self.enforcement_mode.value,
            "violations": [v.to_dict() for v in self.violations],
        }
