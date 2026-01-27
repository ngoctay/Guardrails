"""Plugin system for extensibility."""

from app.plugins.plugin_system import (
    RulePlugin,
    CompliancePlugin,
    LanguagePlugin,
    PluginRegistry,
    get_plugin_registry,
    register_rule_plugin,
    register_compliance_plugin,
    register_language_plugin,
    register_custom_analyzer,
)

__all__ = [
    "RulePlugin",
    "CompliancePlugin",
    "LanguagePlugin",
    "PluginRegistry",
    "get_plugin_registry",
    "register_rule_plugin",
    "register_compliance_plugin",
    "register_language_plugin",
    "register_custom_analyzer",
]
