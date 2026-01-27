"""Plugin system for extensibility."""

from typing import Dict, List, Type, Callable, Optional, Any
from abc import ABC, abstractmethod
from app.models import Violation


class RulePlugin(ABC):
    """Base class for rule plugins."""

    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Get rule ID."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Get rule name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Get rule description."""
        pass

    @property
    @abstractmethod
    def supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        pass

    @abstractmethod
    def analyze(self, code: str, file_path: str) -> List[Violation]:
        """
        Analyze code and return violations.
        Implementation must return list of Violation objects.
        """
        pass

    @abstractmethod
    def is_applicable(self, file_path: str) -> bool:
        """Check if rule applies to this file."""
        pass


class CompliancePlugin(ABC):
    """Base class for compliance checking plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Get compliance framework name."""
        pass

    @abstractmethod
    def check_compliance(self, violations: List[Violation]) -> Dict[str, Any]:
        """
        Check compliance against framework.
        Returns compliance report.
        """
        pass


class LanguagePlugin(ABC):
    """Base class for language-specific analyzers."""

    @property
    @abstractmethod
    def language(self) -> str:
        """Get language identifier."""
        pass

    @abstractmethod
    def parse(self, code: str) -> Any:
        """Parse code and return AST or parsed representation."""
        pass

    @abstractmethod
    def extract_features(self, parsed: Any) -> Dict[str, Any]:
        """Extract features from parsed code."""
        pass


class PluginRegistry:
    """Registry for managing plugins."""

    def __init__(self):
        """Initialize plugin registry."""
        self.rule_plugins: Dict[str, RulePlugin] = {}
        self.compliance_plugins: Dict[str, CompliancePlugin] = {}
        self.language_plugins: Dict[str, LanguagePlugin] = {}
        self.custom_analyzers: Dict[str, Callable] = {}

    def register_rule_plugin(self, plugin: RulePlugin) -> None:
        """Register a rule plugin."""
        self.rule_plugins[plugin.rule_id] = plugin

    def register_compliance_plugin(self, plugin: CompliancePlugin) -> None:
        """Register a compliance plugin."""
        self.compliance_plugins[plugin.name] = plugin

    def register_language_plugin(self, plugin: LanguagePlugin) -> None:
        """Register a language plugin."""
        self.language_plugins[plugin.language] = plugin

    def register_custom_analyzer(self, name: str, analyzer: Callable) -> None:
        """Register a custom analyzer function."""
        self.custom_analyzers[name] = analyzer

    def get_rule_plugin(self, rule_id: str) -> Optional[RulePlugin]:
        """Get a rule plugin by ID."""
        return self.rule_plugins.get(rule_id)

    def get_compliance_plugin(self, name: str) -> Optional[CompliancePlugin]:
        """Get a compliance plugin by name."""
        return self.compliance_plugins.get(name)

    def get_language_plugin(self, language: str) -> Optional[LanguagePlugin]:
        """Get a language plugin by language."""
        return self.language_plugins.get(language)

    def get_custom_analyzer(self, name: str) -> Optional[Callable]:
        """Get a custom analyzer by name."""
        return self.custom_analyzers.get(name)

    def get_applicable_rules(self, file_path: str) -> List[RulePlugin]:
        """Get all applicable rules for a file."""
        applicable = []
        for plugin in self.rule_plugins.values():
            if plugin.is_applicable(file_path):
                applicable.append(plugin)
        return applicable

    def list_rule_plugins(self) -> List[str]:
        """List all registered rule plugins."""
        return list(self.rule_plugins.keys())

    def list_compliance_plugins(self) -> List[str]:
        """List all registered compliance plugins."""
        return list(self.compliance_plugins.keys())

    def list_language_plugins(self) -> List[str]:
        """List all registered language plugins."""
        return list(self.language_plugins.keys())

    def analyze_with_plugins(
        self,
        code: str,
        file_path: str
    ) -> List[Violation]:
        """
        Analyze code using applicable plugins.
        """
        violations = []
        applicable_rules = self.get_applicable_rules(file_path)

        for rule in applicable_rules:
            try:
                rule_violations = rule.analyze(code, file_path)
                violations.extend(rule_violations)
            except Exception as e:
                print(f"Error in rule plugin {rule.rule_id}: {e}")

        return violations


# Global plugin registry
_registry: Optional[PluginRegistry] = None


def get_plugin_registry() -> PluginRegistry:
    """Get or create the global plugin registry."""
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry


def register_rule_plugin(plugin: RulePlugin) -> None:
    """Register a rule plugin globally."""
    get_plugin_registry().register_rule_plugin(plugin)


def register_compliance_plugin(plugin: CompliancePlugin) -> None:
    """Register a compliance plugin globally."""
    get_plugin_registry().register_compliance_plugin(plugin)


def register_language_plugin(plugin: LanguagePlugin) -> None:
    """Register a language plugin globally."""
    get_plugin_registry().register_language_plugin(plugin)


def register_custom_analyzer(name: str, analyzer: Callable) -> None:
    """Register a custom analyzer globally."""
    get_plugin_registry().register_custom_analyzer(name, analyzer)
