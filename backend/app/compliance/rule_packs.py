"""Pre-built compliance rule packs for regulated industries."""

from typing import List, Dict, Any
from app.models import Violation, SeverityLevel, RuleCategory


class BankingComplianceRulePack:
    """Compliance rules for banking and financial institutions."""

    BANKING_RULES = [
        {
            "rule_id": "BANK-001",
            "name": "PCI DSS: No hardcoded credentials",
            "severity": "critical",
            "category": "security",
            "description": "PCI DSS 3.2.1 - Render credentials unreadable in storage",
        },
        {
            "rule_id": "BANK-002",
            "name": "PCI DSS: Encryption in transit",
            "severity": "high",
            "category": "security",
            "description": "PCI DSS 4.1 - Data in transit must be encrypted",
        },
        {
            "rule_id": "BANK-003",
            "name": "PCI DSS: Audit logging",
            "severity": "high",
            "category": "compliance",
            "description": "PCI DSS 10.2 - Implement automated audit trails for access to all system components",
        },
        {
            "rule_id": "BANK-004",
            "name": "GDPR: Data retention",
            "severity": "high",
            "category": "compliance",
            "description": "GDPR Article 5 - Personal data must not be kept longer than necessary",
        },
    ]

    @staticmethod
    def get_rules() -> List[Dict[str, str]]:
        """Get banking compliance rules."""
        return BankingComplianceRulePack.BANKING_RULES


class HealthcareComplianceRulePack:
    """Compliance rules for healthcare providers (HIPAA)."""

    HEALTHCARE_RULES = [
        {
            "rule_id": "HIPAA-001",
            "name": "HIPAA: PHI encryption",
            "severity": "critical",
            "category": "security",
            "description": "45 CFR 164.312(a)(2)(ii) - Implement encryption for PHI",
        },
        {
            "rule_id": "HIPAA-002",
            "name": "HIPAA: Access controls",
            "severity": "high",
            "category": "security",
            "description": "45 CFR 164.312(a)(2)(i) - Implement access controls",
        },
        {
            "rule_id": "HIPAA-003",
            "name": "HIPAA: Audit logging",
            "severity": "high",
            "category": "compliance",
            "description": "45 CFR 164.312(b) - Implement audit controls",
        },
        {
            "rule_id": "HIPAA-004",
            "name": "HIPAA: Data breach notification",
            "severity": "critical",
            "category": "compliance",
            "description": "45 CFR 164.404 - Notify individuals of breaches",
        },
    ]

    @staticmethod
    def get_rules() -> List[Dict[str, str]]:
        """Get healthcare compliance rules."""
        return HealthcareComplianceRulePack.HEALTHCARE_RULES


class GovernmentComplianceRulePack:
    """Compliance rules for government agencies (FedRAMP, FISMA)."""

    GOVERNMENT_RULES = [
        {
            "rule_id": "FEDRAMP-001",
            "name": "FedRAMP: System security plan",
            "severity": "high",
            "category": "compliance",
            "description": "FedRAMP requirement - Maintain system security plan",
        },
        {
            "rule_id": "FISMA-001",
            "name": "FISMA: Minimum security controls",
            "severity": "high",
            "category": "security",
            "description": "FISMA - Implement NIST security controls",
        },
        {
            "rule_id": "FISMA-002",
            "name": "FISMA: Continuous monitoring",
            "severity": "high",
            "category": "compliance",
            "description": "FISMA - Implement continuous monitoring program",
        },
    ]

    @staticmethod
    def get_rules() -> List[Dict[str, str]]:
        """Get government compliance rules."""
        return GovernmentComplianceRulePack.GOVERNMENT_RULES


class TelecomComplianceRulePack:
    """Compliance rules for telecommunications providers."""

    TELECOM_RULES = [
        {
            "rule_id": "TELECOM-001",
            "name": "Data residency requirement",
            "severity": "critical",
            "category": "compliance",
            "description": "Telecom regulation - Customer data must remain in jurisdiction",
        },
        {
            "rule_id": "TELECOM-002",
            "name": "Network security requirements",
            "severity": "high",
            "category": "security",
            "description": "Telecom regulation - Implement network security measures",
        },
        {
            "rule_id": "TELECOM-003",
            "name": "Lawful intercept capabilities",
            "severity": "high",
            "category": "compliance",
            "description": "Telecom regulation - Maintain lawful intercept capabilities",
        },
    ]

    @staticmethod
    def get_rules() -> List[Dict[str, str]]:
        """Get telecom compliance rules."""
        return TelecomComplianceRulePack.TELECOM_RULES


class ComplianceRulePackManager:
    """Manager for industry-specific compliance rule packs."""

    RULE_PACKS = {
        "banking": BankingComplianceRulePack,
        "healthcare": HealthcareComplianceRulePack,
        "government": GovernmentComplianceRulePack,
        "telecom": TelecomComplianceRulePack,
    }

    @staticmethod
    def get_rule_pack(industry: str) -> List[Dict[str, str]]:
        """Get compliance rule pack for industry."""
        pack_class = ComplianceRulePackManager.RULE_PACKS.get(industry.lower())
        if not pack_class:
            raise ValueError(f"Unknown industry: {industry}")
        return pack_class.get_rules()

    @staticmethod
    def list_industries() -> List[str]:
        """List available industries."""
        return list(ComplianceRulePackManager.RULE_PACKS.keys())

    @staticmethod
    def get_combined_rules(industries: List[str]) -> List[Dict[str, str]]:
        """Get combined rules for multiple industries."""
        combined = []
        seen_ids = set()

        for industry in industries:
            rules = ComplianceRulePackManager.get_rule_pack(industry)
            for rule in rules:
                if rule["rule_id"] not in seen_ids:
                    combined.append(rule)
                    seen_ids.add(rule["rule_id"])

        return combined
