"""FastAPI application for guardrails backend."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.config import Config
from app.models import AnalysisRequest, ScanResult
from app.analyzers import CodeAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Guardrails Backend",
    description="Enterprise guardrails for GitHub Copilot",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


@app.post("/api/analyze", response_model=dict)
async def analyze_code(request: Request):
    """
    Analyze code in a PR diff.
    
    Expected JSON body:
    {
        "repo_name": "owner/repo",
        "pr_number": 123,
        "commit_hash": "abc123",
        "files": {
            "path/to/file.py": "diff content..."
        },
        "copilot_generated_files": ["path/to/file.py"]  # optional
    }
    """
    try:
        data = await request.json()
        
        # Validate request
        required_fields = ["repo_name", "pr_number", "commit_hash", "files"]
        for field in required_fields:
            if field not in data:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Missing required field: {field}"
                )

        # Create analysis request
        analysis_request = AnalysisRequest(
            repo_name=data["repo_name"],
            pr_number=data["pr_number"],
            commit_hash=data["commit_hash"],
            files=data["files"],
            copilot_generated_files=data.get("copilot_generated_files"),
        )

        logger.info(
            f"Analyzing PR #{analysis_request.pr_number} in {analysis_request.repo_name}"
        )

        # Run analysis
        violations = CodeAnalyzer.analyze_files(analysis_request)

        # Create scan result
        scan_result = CodeAnalyzer.create_scan_result(analysis_request, violations)

        logger.info(f"Found {len(violations)} violations")

        return {
            "success": True,
            "scan_id": scan_result.scan_id,
            "repo_name": scan_result.repo_name,
            "pr_number": scan_result.pr_number,
            "violations": [v.to_dict() for v in violations],
            "violation_count": len(violations),
            "critical_count": sum(1 for v in violations if v.severity.value == "critical"),
            "high_count": sum(1 for v in violations if v.severity.value == "high"),
            "medium_count": sum(1 for v in violations if v.severity.value == "medium"),
            "low_count": sum(1 for v in violations if v.severity.value == "low"),
            "copilot_violations": sum(1 for v in violations if v.is_copilot_generated),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/rules")
async def get_rules():
    """Get available security rules."""
    rules = [
        {
            "rule_id": "SEC-001",
            "name": "Hardcoded Secrets",
            "severity": "critical",
            "category": "security",
            "description": "Detects hardcoded API keys, passwords, tokens, and AWS credentials",
            "cwe": "CWE-798",
            "owasp": "A02:2021 – Cryptographic Failures",
        },
        {
            "rule_id": "SEC-002",
            "name": "SQL Injection",
            "severity": "critical",
            "category": "security",
            "description": "Detects SQL injection vulnerabilities through string interpolation",
            "cwe": "CWE-89",
            "owasp": "A03:2021 – Injection",
        },
        {
            "rule_id": "SEC-003",
            "name": "Insecure Deserialization",
            "severity": "high",
            "category": "security",
            "description": "Detects unsafe deserialization of untrusted data",
            "cwe": "CWE-502",
            "owasp": "A08:2021 – Software and Data Integrity Failures",
        },
        {
            "rule_id": "SEC-004",
            "name": "Unsafe Code Execution",
            "severity": "critical",
            "category": "security",
            "description": "Detects use of eval(), exec(), os.system(), and shell execution",
            "cwe": "CWE-95",
            "owasp": "A03:2021 – Injection",
        },
        {
            "rule_id": "SEC-005",
            "name": "Weak Cryptography",
            "severity": "high",
            "category": "security",
            "description": "Detects use of weak or deprecated cryptographic algorithms",
            "cwe": "CWE-327",
            "owasp": "A02:2021 – Cryptographic Failures",
        },
    ]
    return {"rules": rules}


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG,
    )
