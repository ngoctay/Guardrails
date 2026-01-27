"""Audit logging for compliance and traceability."""

import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict
from dataclasses import dataclass, asdict
import os


@dataclass
class AuditEvent:
    """Represents an audit event."""
    event_id: str
    timestamp: str
    repo_name: str
    pr_number: int
    commit_hash: str
    violation_count: int
    critical_count: int
    high_count: int
    enforcement_action: str  # "advisory", "warning", "blocking"
    blocked: bool
    override_applied: bool = False
    override_reason: Optional[str] = None
    pr_url: Optional[str] = None
    scan_id: Optional[str] = None
    violations_summary: Optional[List[Dict]] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class AuditLogger:
    """Logger for audit events."""

    def __init__(self, log_dir: str = "audit_logs"):
        """Initialize audit logger."""
        self.log_dir = log_dir
        self.events: List[AuditEvent] = []
        self._ensure_log_dir()
        self.load_audit_logs(self.log_dir)

    def _ensure_log_dir(self) -> None:
        """Ensure log directory exists."""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)

    def log_scan(
        self,
        repo_name: str,
        pr_number: int,
        commit_hash: str,
        violation_count: int,
        critical_count: int,
        high_count: int,
        enforcement_action: str,
        blocked: bool,
        scan_id: str,
        violations_summary: Optional[List[Dict]] = None,
        pr_url: Optional[str] = None,
    ) -> AuditEvent:
        """
        Log a code scan event.
        """
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            repo_name=repo_name,
            pr_number=pr_number,
            commit_hash=commit_hash,
            violation_count=violation_count,
            critical_count=critical_count,
            high_count=high_count,
            enforcement_action=enforcement_action,
            blocked=blocked,
            pr_url=pr_url,
            scan_id=scan_id,
            violations_summary=violations_summary,
        )
        self.events.append(event)
        self._write_event(event)
        return event

    def log_override(
        self,
        repo_name: str,
        pr_number: int,
        override_reason: str,
        override_token: str,
    ) -> AuditEvent:
        """
        Log a policy override event.
        """
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            repo_name=repo_name,
            pr_number=pr_number,
            commit_hash="",
            violation_count=0,
            critical_count=0,
            high_count=0,
            enforcement_action="override",
            blocked=False,
            override_applied=True,
            override_reason=override_reason,
        )
        self.events.append(event)
        self._write_event(event)
        return event

    def _write_event(self, event: AuditEvent) -> None:
        """Write event to log file."""
        filename = f"{self.log_dir}/audit_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
        with open(filename, "a") as f:
            f.write(event.to_json() + "\n")

    def get_events_by_repo(self, repo_name: str) -> List[AuditEvent]:
        """Get all audit events for a repository."""
        return [e for e in self.events if e.repo_name == repo_name]

    def get_events_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> List[AuditEvent]:
        """Get audit events within a date range."""
        events = []
        for event in self.events:
            event_time = datetime.fromisoformat(event.timestamp)
            if start_date <= event_time <= end_date:
                events.append(event)
        return events

    def get_violations_summary(self) -> Dict:
        """Get summary of violations across all scans."""
        summary = {
            "total_scans": len(self.events),
            "total_violations": sum(e.violation_count for e in self.events),
            "total_critical": sum(e.critical_count for e in self.events),
            "total_high": sum(e.high_count for e in self.events),
            "total_blocked": sum(1 for e in self.events if e.blocked),
            "total_overrides": sum(1 for e in self.events if e.override_applied),
        }
        return summary

    def export_audit_log(self, filename: str) -> str:
        """
        Export audit log to file.
        Supports JSON and CSV formats based on extension.
        """
        if filename.endswith(".json"):
            return self._export_json(filename)
        elif filename.endswith(".csv"):
            return self._export_csv(filename)
        else:
            raise ValueError("Unsupported format. Use .json or .csv")

    def _export_json(self, filename: str) -> str:
        """Export audit log as JSON."""
        with open(filename, "w") as f:
            json.dump([e.to_dict() for e in self.events], f, indent=2)
        return filename

    def _export_csv(self, filename: str) -> str:
        """Export audit log as CSV."""
        import csv

        if not self.events:
            return filename

        with open(filename, "w", newline="") as f:
            fieldnames = [
                "event_id",
                "timestamp",
                "repo_name",
                "pr_number",
                "violation_count",
                "critical_count",
                "high_count",
                "enforcement_action",
                "blocked",
                "override_applied",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for event in self.events:
                row = {k: event.to_dict()[k] for k in fieldnames}
                writer.writerow(row)

        return filename

    def load_audit_logs(self, log_dir: str) -> None:
        """
        Load audit logs from directory. Handles multi-line JSON objects.
        """
        if not os.path.exists(log_dir):
            return

        for filename in os.listdir(log_dir):
            if filename.endswith(".jsonl"):
                filepath = os.path.join(log_dir, filename)
                with open(filepath, "r") as f:
                    content = f.read()
                    # Split objects by pattern: }\n{ which indicates end of one object and start of another
                    # First, we need to find all JSON objects
                    objects = []
                    current_obj_start = 0
                    brace_count = 0
                    
                    for i, char in enumerate(content):
                        if char == '{':
                            if brace_count == 0:
                                current_obj_start = i
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                # Found a complete object
                                obj_str = content[current_obj_start:i+1]
                                objects.append(obj_str)
                    
                    # Parse each object
                    for obj_str in objects:
                        try:
                            event_dict = json.loads(obj_str)
                            self._create_event_from_dict(event_dict)
                        except (json.JSONDecodeError, ValueError) as e:
                            print(f"Error parsing object: {e}")

    def _create_event_from_dict(self, event_dict: dict) -> None:
        """Helper method to create an AuditEvent from a dictionary."""
        try:
            event = AuditEvent(
                event_id=event_dict["event_id"],
                timestamp=event_dict["timestamp"],
                repo_name=event_dict["repo_name"],
                pr_number=event_dict["pr_number"],
                commit_hash=event_dict["commit_hash"],
                violation_count=event_dict["violation_count"],
                critical_count=event_dict["critical_count"],
                high_count=event_dict["high_count"],
                enforcement_action=event_dict["enforcement_action"],
                blocked=event_dict["blocked"],
                override_applied=event_dict.get("override_applied", False),
                override_reason=event_dict.get("override_reason"),
                pr_url=event_dict.get("pr_url"),
                scan_id=event_dict.get("scan_id"),
                violations_summary=event_dict.get("violations_summary"),
            )
            self.events.append(event)
        except (KeyError, ValueError) as e:
            print(f"Error creating event from dict: {e}")
