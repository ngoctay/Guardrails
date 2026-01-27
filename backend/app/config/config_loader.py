"""Rule configuration management and loader."""

import json
import os
from typing import Dict, List, Any, Optional
import yaml

from app.models import EnforcementMode


class RuleConfig:
    """Represents a single rule configuration."""

    def __init__(
        self,
        rule_id: str,
        name: str,
        enabled: bool = True,
        severity: str = "medium",
        description: str = "",
        pattern: Optional[str] = None,
        category: str = "security",
        cwe_id: Optional[str] = None,
        owasp_category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        languages: Optional[List[str]] = None,
        custom_message: Optional[str] = None,
    ):
        """Initialize rule configuration."""
        self.rule_id = rule_id
        self.name = name
        self.enabled = enabled
        self.severity = severity
        self.description = description
        self.pattern = pattern
        self.category = category
        self.cwe_id = cwe_id
        self.owasp_category = owasp_category
        self.tags = tags or []
        self.languages = languages or []
        self.custom_message = custom_message

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "enabled": self.enabled,
            "severity": self.severity,
            "description": self.description,
            "pattern": self.pattern,
            "category": self.category,
            "cwe_id": self.cwe_id,
            "owasp_category": self.owasp_category,
            "tags": self.tags,
            "languages": self.languages,
            "custom_message": self.custom_message,
        }


class RuleSet:
    """Represents a complete ruleset."""

    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        description: str = "",
        rules: Optional[List[RuleConfig]] = None,
        overrides: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        """Initialize ruleset."""
        self.name = name
        self.version = version
        self.description = description
        self.rules = rules or []
        self.overrides = overrides or {}

    def get_rule(self, rule_id: str) -> Optional[RuleConfig]:
        """Get rule by ID."""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                return rule
        return None

    def get_enabled_rules(self) -> List[RuleConfig]:
        """Get all enabled rules."""
        return [r for r in self.rules if r.enabled]

    def disable_rule(self, rule_id: str) -> None:
        """Disable a rule."""
        rule = self.get_rule(rule_id)
        if rule:
            rule.enabled = False

    def enable_rule(self, rule_id: str) -> None:
        """Enable a rule."""
        rule = self.get_rule(rule_id)
        if rule:
            rule.enabled = True

    def override_severity(self, rule_id: str, new_severity: str) -> None:
        """Override severity for a rule."""
        rule = self.get_rule(rule_id)
        if rule:
            rule.severity = new_severity

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "rules": [r.to_dict() for r in self.rules],
            "overrides": self.overrides,
        }


class ConfigLoader:
    """Loader for rule configurations from YAML/JSON files."""

    @staticmethod
    def load_yaml(filepath: str) -> RuleSet:
        """Load configuration from YAML file."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Configuration file not found: {filepath}")

        with open(filepath, "r") as f:
            data = yaml.safe_load(f)

        return ConfigLoader._parse_config(data)

    @staticmethod
    def load_json(filepath: str) -> RuleSet:
        """Load configuration from JSON file."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Configuration file not found: {filepath}")

        with open(filepath, "r") as f:
            data = json.load(f)

        return ConfigLoader._parse_config(data)

    @staticmethod
    def load(filepath: str) -> RuleSet:
        """Load configuration from file (auto-detect format)."""
        if filepath.endswith(".yaml") or filepath.endswith(".yml"):
            return ConfigLoader.load_yaml(filepath)
        elif filepath.endswith(".json"):
            return ConfigLoader.load_json(filepath)
        else:
            raise ValueError(f"Unsupported file format: {filepath}")

    @staticmethod
    def _parse_config(data: dict) -> RuleSet:
        """Parse configuration dictionary into RuleSet."""
        rules = []

        for rule_data in data.get("rules", []):
            rule = RuleConfig(
                rule_id=rule_data.get("rule_id"),
                name=rule_data.get("name"),
                enabled=rule_data.get("enabled", True),
                severity=rule_data.get("severity", "medium"),
                description=rule_data.get("description", ""),
                pattern=rule_data.get("pattern"),
                category=rule_data.get("category", "security"),
                cwe_id=rule_data.get("cwe_id"),
                owasp_category=rule_data.get("owasp_category"),
                tags=rule_data.get("tags", []),
                languages=rule_data.get("languages", []),
                custom_message=rule_data.get("custom_message"),
            )
            rules.append(rule)

        ruleset = RuleSet(
            name=data.get("name", "custom-ruleset"),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            rules=rules,
            overrides=data.get("overrides", {}),
        )

        return ruleset

    @staticmethod
    def save_yaml(ruleset: RuleSet, filepath: str) -> None:
        """Save ruleset to YAML file."""
        with open(filepath, "w") as f:
            yaml.dump(ruleset.to_dict(), f, default_flow_style=False)

    @staticmethod
    def save_json(ruleset: RuleSet, filepath: str) -> None:
        """Save ruleset to JSON file."""
        with open(filepath, "w") as f:
            json.dump(ruleset.to_dict(), f, indent=2)


class RepositoryPolicyLoader:
    """Load policy configuration from repository."""

    POLICY_FILES = [
        ".guardrails/policy.yaml",
        ".guardrails/policy.yml",
        ".guardrails/policy.json",
        "guardrails.yaml",
        "guardrails.yml",
        "guardrails.json",
    ]

    @staticmethod
    def find_policy_file(repo_path: str) -> Optional[str]:
        """Find policy file in repository."""
        for policy_file in RepositoryPolicyLoader.POLICY_FILES:
            filepath = os.path.join(repo_path, policy_file)
            if os.path.exists(filepath):
                return filepath
        return None

    @staticmethod
    def load_policy(repo_path: str) -> Optional[dict]:
        """Load policy from repository."""
        policy_file = RepositoryPolicyLoader.find_policy_file(repo_path)
        if not policy_file:
            return None

        try:
            if policy_file.endswith(".json"):
                with open(policy_file, "r") as f:
                    return json.load(f)
            else:  # YAML
                with open(policy_file, "r") as f:
                    return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading policy file: {e}")
            return None


class RulePackManager:
    """Manage rule packs (collections of rulesets)."""

    def __init__(self):
        """Initialize rule pack manager."""
        self.rulesets: Dict[str, RuleSet] = {}
        self.active_ruleset: Optional[str] = None

    def register_ruleset(self, ruleset: RuleSet) -> None:
        """Register a ruleset."""
        self.rulesets[ruleset.name] = ruleset
        if self.active_ruleset is None:
            self.active_ruleset = ruleset.name

    def get_ruleset(self, name: str) -> Optional[RuleSet]:
        """Get a ruleset by name."""
        return self.rulesets.get(name)

    def get_active_ruleset(self) -> Optional[RuleSet]:
        """Get the active ruleset."""
        if self.active_ruleset:
            return self.rulesets.get(self.active_ruleset)
        return None

    def set_active_ruleset(self, name: str) -> None:
        """Set the active ruleset."""
        if name in self.rulesets:
            self.active_ruleset = name
        else:
            raise ValueError(f"Ruleset not found: {name}")

    def list_rulesets(self) -> List[str]:
        """List all registered rulesets."""
        return list(self.rulesets.keys())

    def get_enabled_rules(self) -> List[RuleConfig]:
        """Get all enabled rules from the active ruleset."""
        ruleset = self.get_active_ruleset()
        if ruleset:
            return ruleset.get_enabled_rules()
        return []
