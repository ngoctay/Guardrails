"""Extended API endpoints for configuration and compliance."""

from fastapi import FastAPI, HTTPException, Request
import logging

from app.config.config_loader import ConfigLoader, RulePackManager
from app.compliance import ComplianceRulePackManager

logger = logging.getLogger(__name__)


def register_extended_endpoints(app: FastAPI):
    """Register extended API endpoints."""

    @app.get("/api/config/rulesets")
    async def list_rulesets():
        """List available rule sets."""
        try:
            # Load default ruleset
            default_rules = ConfigLoader.load("backend/guardrails-ruleset-default.yaml")
            return {
                "success": True,
                "rulesets": [
                    {
                        "name": default_rules.name,
                        "version": default_rules.version,
                        "description": default_rules.description,
                        "rule_count": len(default_rules.rules),
                    }
                ],
            }
        except Exception as e:
            logger.error(f"Error listing rulesets: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to list rulesets: {str(e)}")

    @app.get("/api/config/ruleset/{ruleset_name}")
    async def get_ruleset(ruleset_name: str):
        """Get a specific ruleset."""
        try:
            if ruleset_name == "default":
                ruleset = ConfigLoader.load("backend/guardrails-ruleset-default.yaml")
            else:
                ruleset = ConfigLoader.load(f"backend/guardrails-ruleset-{ruleset_name}.yaml")

            return {
                "success": True,
                "ruleset": ruleset.to_dict(),
            }
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Ruleset not found: {ruleset_name}")
        except Exception as e:
            logger.error(f"Error getting ruleset: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get ruleset: {str(e)}")

    @app.post("/api/config/ruleset")
    async def create_custom_ruleset(request: Request):
        """Create a custom ruleset."""
        try:
            data = await request.json()

            if "name" not in data or "rules" not in data:
                raise HTTPException(
                    status_code=400,
                    detail="name and rules are required",
                )

            from app.config.config_loader import RuleConfig, RuleSet

            rules = []
            for rule_data in data["rules"]:
                rule = RuleConfig(
                    rule_id=rule_data.get("rule_id"),
                    name=rule_data.get("name"),
                    enabled=rule_data.get("enabled", True),
                    severity=rule_data.get("severity", "medium"),
                    description=rule_data.get("description", ""),
                    category=rule_data.get("category", "security"),
                )
                rules.append(rule)

            ruleset = RuleSet(
                name=data["name"],
                version=data.get("version", "1.0.0"),
                description=data.get("description", ""),
                rules=rules,
            )

            return {
                "success": True,
                "ruleset": ruleset.to_dict(),
                "message": "Custom ruleset created successfully",
            }

        except Exception as e:
            logger.error(f"Error creating custom ruleset: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create ruleset: {str(e)}")

    @app.get("/api/compliance/industries")
    async def list_compliance_industries():
        """List available compliance rule packs."""
        try:
            industries = ComplianceRulePackManager.list_industries()
            return {
                "success": True,
                "industries": industries,
                "total": len(industries),
            }
        except Exception as e:
            logger.error(f"Error listing industries: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to list industries: {str(e)}")

    @app.get("/api/compliance/rules/{industry}")
    async def get_compliance_rules(industry: str):
        """Get compliance rules for an industry."""
        try:
            rules = ComplianceRulePackManager.get_rule_pack(industry)
            return {
                "success": True,
                "industry": industry,
                "rules": rules,
                "total": len(rules),
            }
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Error getting compliance rules: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get compliance rules: {str(e)}")

    @app.post("/api/compliance/check")
    async def check_compliance(request: Request):
        """Check code compliance against industry standards."""
        try:
            data = await request.json()

            if "industry" not in data or "violations" not in data:
                raise HTTPException(
                    status_code=400,
                    detail="industry and violations are required",
                )

            industry = data["industry"]
            violations = data["violations"]

            compliance_rules = ComplianceRulePackManager.get_rule_pack(industry)

            # Map violations to compliance rules
            compliance_check = {
                "industry": industry,
                "total_violations": len(violations),
                "compliance_rules": len(compliance_rules),
                "matching_violations": [],
                "passed_rules": [],
                "failed_rules": [],
            }

            # Check if violations match compliance rules
            violation_rule_ids = {v.get("rule_id") for v in violations}

            for rule in compliance_rules:
                if rule["rule_id"] in violation_rule_ids:
                    compliance_check["failing_rules"].append(rule)
                else:
                    compliance_check["passed_rules"].append(rule)

            compliance_check["compliance_status"] = (
                "compliant" if len(compliance_check["failing_rules"]) == 0 else "non-compliant"
            )

            return {
                "success": True,
                "compliance": compliance_check,
            }

        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Error checking compliance: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to check compliance: {str(e)}")

    @app.get("/api/plugins")
    async def list_plugins():
        """List registered plugins."""
        from app.plugins import get_plugin_registry

        try:
            registry = get_plugin_registry()
            return {
                "success": True,
                "plugins": {
                    "rules": registry.list_rule_plugins(),
                    "compliance": registry.list_compliance_plugins(),
                    "languages": registry.list_language_plugins(),
                    "custom_analyzers": list(registry.custom_analyzers.keys()),
                },
            }
        except Exception as e:
            logger.error(f"Error listing plugins: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to list plugins: {str(e)}")
