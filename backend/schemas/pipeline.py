"""
Enterprise Pipeline Logging and Progress Reporting Schema

Enhanced pipeline logging system for AI-driven design automation with enterprise-grade
audit trails, compliance reporting, and real-time progress tracking.

This module integrates with the formal ODL schema and enterprise topology validation
to provide comprehensive visibility into AI pipeline execution.
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

from pydantic import BaseModel, Field, ConfigDict


class LogLevel(str, Enum):
    """Severity levels for pipeline log entries with enterprise categorization."""
    DEBUG = "debug"          # Detailed execution traces
    INFO = "info"            # General progress information  
    WARNING = "warning"      # Non-critical issues requiring attention
    ERROR = "error"          # Critical errors that impact execution
    COMPLIANCE = "compliance" # Compliance-specific issues and validations


class PipelineStage(str, Enum):
    """Enhanced stages of the enterprise AI wiring pipeline."""
    INITIALIZATION = "initialization"
    COMPONENT_ANALYSIS = "component_analysis"
    PANEL_GROUPING = "panel_grouping"
    PATTERN_RETRIEVAL = "pattern_retrieval"
    SUGGESTION_GENERATION = "suggestion_generation"
    TOPOLOGY_GENERATION = "topology_generation"
    COMPLIANCE_VALIDATION = "compliance_validation"
    ENTERPRISE_VALIDATION = "enterprise_validation"
    OPTIMIZATION = "optimization"
    FINALIZATION = "finalization"


class ComplianceIssueType(str, Enum):
    """Categories of compliance issues for enterprise reporting."""
    ELECTRICAL_CODE = "electrical_code"        # NEC/IEC violations
    STRING_SIZING = "string_sizing"           # String length/sizing issues
    VOLTAGE_LIMITS = "voltage_limits"         # Voltage limit violations
    CURRENT_LIMITS = "current_limits"         # Current capacity issues
    GROUNDING = "grounding"                   # Grounding requirements
    PROTECTION = "protection"                 # Protection device requirements
    CONDUIT_FILL = "conduit_fill"            # Conduit fill calculations
    ACCESSIBILITY = "accessibility"           # Code accessibility requirements


@dataclass
class PerformanceMetric:
    """Performance metrics for pipeline execution tracking."""
    stage: PipelineStage
    start_time: datetime
    end_time: datetime
    memory_usage_mb: Optional[float] = None
    cpu_time_ms: Optional[float] = None
    items_processed: Optional[int] = None
    
    @property
    def duration_ms(self) -> float:
        """Calculate stage duration in milliseconds."""
        return (self.end_time - self.start_time).total_seconds() * 1000


class ComplianceIssue(BaseModel):
    """Enhanced compliance issue with detailed enterprise reporting."""
    
    issue_type: ComplianceIssueType
    severity: LogLevel = LogLevel.WARNING
    message: str
    component_ids: List[str] = Field(default_factory=list)
    code_reference: Optional[str] = None        # e.g., "NEC 690.7(A)"
    remediation: Optional[str] = None           # Suggested fix
    calculated_values: Dict[str, Any] = Field(default_factory=dict)
    
    # Enterprise tracking
    affects_approval: bool = False              # Requires manual approval
    risk_level: str = "medium"                 # low/medium/high/critical
    
    model_config = ConfigDict(extra="forbid")


class PipelineLogEntry(BaseModel):
    """Enhanced log entry with performance metrics and context."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    stage: PipelineStage
    message: str
    level: LogLevel = LogLevel.INFO
    
    # Enhanced context information
    component_ids: List[str] = Field(default_factory=list)
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Enterprise tracking
    operation_id: Optional[str] = None          # For correlation with ODL patches
    user_id: Optional[str] = None              # For audit trails
    
    model_config = ConfigDict(extra="forbid")


class PipelineExecutionSummary(BaseModel):
    """Summary statistics for pipeline execution."""
    
    total_duration_ms: float
    stages_completed: int
    components_processed: int
    edges_created: int
    compliance_issues_found: int
    performance_metrics: List[PerformanceMetric] = Field(default_factory=list)
    
    model_config = ConfigDict(extra="forbid")


class PipelineLog(BaseModel):
    """Enterprise-grade aggregate log for pipeline runs with comprehensive tracking."""

    # Core identification
    session_id: str
    pipeline_id: str = Field(default_factory=lambda: f"pipeline_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
    
    # Execution tracking
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    status: str = "running"  # running, completed, failed, cancelled
    
    # Log entries and issues
    entries: List[PipelineLogEntry] = Field(default_factory=list)
    compliance_issues: List[ComplianceIssue] = Field(default_factory=list)
    
    # Enterprise features
    execution_summary: Optional[PipelineExecutionSummary] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)  # Pipeline config used
    
    # Audit and governance
    requesting_user: Optional[str] = None
    approval_required: bool = False
    export_metadata: Dict[str, Any] = Field(default_factory=dict)  # For audit exports
    
    model_config = ConfigDict(extra="forbid")
    
    def add_entry(
        self, 
        stage: PipelineStage, 
        message: str, 
        level: LogLevel = LogLevel.INFO,
        **kwargs
    ) -> None:
        """Add a log entry with automatic timestamp."""
        entry = PipelineLogEntry(
            stage=stage,
            message=message,
            level=level,
            **kwargs
        )
        self.entries.append(entry)
    
    def add_compliance_issue(
        self,
        issue_type: ComplianceIssueType,
        message: str,
        severity: LogLevel = LogLevel.WARNING,
        **kwargs
    ) -> None:
        """Add a compliance issue and corresponding log entry."""
        issue = ComplianceIssue(
            issue_type=issue_type,
            severity=severity,
            message=message,
            **kwargs
        )
        self.compliance_issues.append(issue)
        
        # Also add as log entry for chronological tracking
        self.add_entry(
            stage=PipelineStage.COMPLIANCE_VALIDATION,
            message=f"[{issue_type.value.upper()}] {message}",
            level=severity
        )
    
    def complete_execution(self) -> None:
        """Mark pipeline execution as completed and generate summary."""
        self.completed_at = datetime.utcnow()
        self.status = "completed"
        
        # Generate execution summary
        total_duration = (self.completed_at - self.started_at).total_seconds() * 1000
        
        self.execution_summary = PipelineExecutionSummary(
            total_duration_ms=total_duration,
            stages_completed=len(set(entry.stage for entry in self.entries)),
            components_processed=len(set().union(*[entry.component_ids for entry in self.entries])),
            edges_created=sum(1 for entry in self.entries if "edge" in entry.message.lower()),
            compliance_issues_found=len(self.compliance_issues)
        )
    
    def get_critical_issues(self) -> List[ComplianceIssue]:
        """Get compliance issues that require immediate attention."""
        return [issue for issue in self.compliance_issues 
                if issue.severity in [LogLevel.ERROR, LogLevel.COMPLIANCE] or issue.affects_approval]
    
    def export_for_audit(self) -> Dict[str, Any]:
        """Export log in format suitable for enterprise audit systems."""
        return {
            "pipeline_execution": {
                "id": self.pipeline_id,
                "session_id": self.session_id,
                "started_at": self.started_at.isoformat(),
                "completed_at": self.completed_at.isoformat() if self.completed_at else None,
                "status": self.status,
                "requesting_user": self.requesting_user
            },
            "execution_summary": self.execution_summary.model_dump() if self.execution_summary else None,
            "timeline": [
                {
                    "timestamp": entry.timestamp.isoformat(),
                    "stage": entry.stage.value,
                    "level": entry.level.value,
                    "message": entry.message,
                    "duration_ms": entry.duration_ms,
                    "components": entry.component_ids
                }
                for entry in self.entries
            ],
            "compliance_report": [
                {
                    "type": issue.issue_type.value,
                    "severity": issue.severity.value,
                    "message": issue.message,
                    "code_reference": issue.code_reference,
                    "components_affected": issue.component_ids,
                    "remediation": issue.remediation,
                    "risk_level": issue.risk_level,
                    "requires_approval": issue.affects_approval
                }
                for issue in self.compliance_issues
            ],
            "configuration": self.configuration,
            "export_metadata": {
                **self.export_metadata,
                "exported_at": datetime.utcnow().isoformat(),
                "schema_version": "1.0.0"
            }
        }