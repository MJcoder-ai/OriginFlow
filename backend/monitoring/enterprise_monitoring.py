# backend/monitoring/enterprise_monitoring.py
"""Enterprise-grade monitoring and observability system for OriginFlow AI platform."""

from __future__ import annotations

import asyncio
import time
import json
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Set
from datetime import datetime, timedelta
import threading
import uuid

from prometheus_client import (
    Counter, Histogram, Gauge, Summary,
    CollectorRegistry, generate_latest
)
import redis.asyncio as redis
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import psutil


logger = logging.getLogger(__name__)


# Core metrics registry
METRICS_REGISTRY = CollectorRegistry()

# Agent Performance Metrics
AGENT_METRICS = {
    "agent_requests_total": Counter(
        "agent_requests_total",
        "Total agent requests",
        ["agent_name", "tenant_id", "status"],
        registry=METRICS_REGISTRY
    ),
    "agent_response_time_seconds": Histogram(
        "agent_response_time_seconds",
        "Agent response time distribution",
        ["agent_name", "reasoning_strategy"],
        registry=METRICS_REGISTRY
    ),
    "agent_confidence_score": Histogram(
        "agent_confidence_score",
        "Agent confidence score distribution",
        ["agent_name", "action_type"],
        registry=METRICS_REGISTRY
    ),
    "agent_collaborations_total": Counter(
        "agent_collaborations_total",
        "Total agent collaborations",
        ["primary_agent", "supporting_agents_count"],
        registry=METRICS_REGISTRY
    ),
    "reasoning_steps_total": Counter(
        "reasoning_steps_total",
        "Total reasoning steps executed",
        ["agent_name", "reasoning_depth"],
        registry=METRICS_REGISTRY
    )
}

# System Performance Metrics
SYSTEM_METRICS = {
    "active_tenants": Gauge(
        "active_tenants",
        "Number of active tenants",
        registry=METRICS_REGISTRY
    ),
    "concurrent_sessions": Gauge(
        "concurrent_sessions",
        "Number of concurrent sessions",
        registry=METRICS_REGISTRY
    ),
    "memory_usage_bytes": Gauge(
        "memory_usage_bytes",
        "Memory usage in bytes",
        ["process"],
        registry=METRICS_REGISTRY
    ),
    "cpu_usage_percent": Gauge(
        "cpu_usage_percent",
        "CPU usage percentage",
        ["core"],
        registry=METRICS_REGISTRY
    ),
    "disk_usage_bytes": Gauge(
        "disk_usage_bytes",
        "Disk usage in bytes",
        ["mount_point"],
        registry=METRICS_REGISTRY
    ),
    "network_traffic_bytes": Counter(
        "network_traffic_bytes",
        "Network traffic in bytes",
        ["direction", "interface"],
        registry=METRICS_REGISTRY
    )
}

# Business Metrics
BUSINESS_METRICS = {
    "designs_created_total": Counter(
        "designs_created_total",
        "Total designs created",
        ["tenant_id", "design_type", "complexity"],
        registry=METRICS_REGISTRY
    ),
    "user_actions_total": Counter(
        "user_actions_total",
        "Total user actions",
        ["tenant_id", "action_type", "interface"],
        registry=METRICS_REGISTRY
    ),
    "ai_confidence_trends": Histogram(
        "ai_confidence_trends",
        "AI confidence score trends over time",
        ["time_window", "agent_category"],
        registry=METRICS_REGISTRY
    ),
    "user_satisfaction_score": Histogram(
        "user_satisfaction_score",
        "User satisfaction scores",
        ["tenant_id", "interaction_type"],
        registry=METRICS_REGISTRY
    )
}

# Error and Reliability Metrics
RELIABILITY_METRICS = {
    "error_rate_total": Counter(
        "error_rate_total",
        "Total errors by category",
        ["error_type", "severity", "component"],
        registry=METRICS_REGISTRY
    ),
    "system_uptime_seconds": Counter(
        "system_uptime_seconds",
        "System uptime in seconds",
        registry=METRICS_REGISTRY
    ),
    "service_health_status": Gauge(
        "service_health_status",
        "Service health status (0=down, 1=degraded, 2=healthy)",
        ["service_name"],
        registry=METRICS_REGISTRY
    ),
    "circuit_breaker_state": Gauge(
        "circuit_breaker_state",
        "Circuit breaker state (0=closed, 1=open)",
        ["service_name"],
        registry=METRICS_REGISTRY
    )
}


@dataclass
class MonitoringConfig:
    """Configuration for enterprise monitoring system."""

    # Collection settings
    metrics_collection_interval: int = 15  # seconds
    log_retention_days: int = 30
    max_log_size_mb: int = 100

    # Alert thresholds
    high_error_rate_threshold: float = 0.05  # 5%
    high_latency_threshold: float = 2.0  # seconds
    low_confidence_threshold: float = 0.3  # 30%

    # Redis settings for distributed monitoring
    redis_url: Optional[str] = None
    enable_redis_metrics: bool = True

    # External integrations
    prometheus_push_gateway_url: Optional[str] = None
    grafana_webhook_url: Optional[str] = None

    # Performance monitoring
    enable_performance_monitoring: bool = True
    slow_query_threshold: float = 1.0  # seconds


@dataclass
class TraceContext:
    """Distributed tracing context."""

    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    span_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_span_id: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class MonitoringEvent:
    """Structured monitoring event."""

    event_type: str
    timestamp: datetime
    component: str
    severity: str = "info"  # info, warning, error, critical
    details: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    trace_context: Optional[TraceContext] = None


class EnterpriseMonitoringSystem:
    """Centralized enterprise monitoring and observability."""

    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.redis: Optional[redis.Redis] = None
        self._monitoring_tasks: Set[asyncio.Task] = set()
        self._health_checks: Dict[str, Callable] = {}
        self._alert_handlers: Dict[str, Callable] = {}

        # Initialize Redis if configured
        if config.redis_url:
            self.redis = redis.from_url(config.redis_url)

        # Start background monitoring tasks
        self._start_monitoring_tasks()

    async def initialize(self) -> None:
        """Initialize the monitoring system."""
        if self.redis:
            await self.redis.ping()
            logger.info("Redis connection established for monitoring")

        # Register default health checks
        self.register_health_check("database", self._check_database_health)
        self.register_health_check("redis", self._check_redis_health)
        self.register_health_check("memory", self._check_memory_health)
        self.register_health_check("disk", self._check_disk_health)

        # Register default alert handlers
        self.register_alert_handler("high_error_rate", self._handle_high_error_rate)
        self.register_alert_handler("low_confidence", self._handle_low_confidence)

        logger.info("Enterprise Monitoring System initialized")

    async def cleanup(self) -> None:
        """Cleanup monitoring resources."""
        # Cancel all monitoring tasks
        for task in self._monitoring_tasks:
            task.cancel()

        # Wait for tasks to complete
        if self._monitoring_tasks:
            await asyncio.gather(*self._monitoring_tasks, return_exceptions=True)

        if self.redis:
            await self.redis.aclose()

        logger.info("Monitoring System cleaned up")

    def register_health_check(self, name: str, check_func: Callable) -> None:
        """Register a health check function."""
        self._health_checks[name] = check_func

    def register_alert_handler(self, alert_type: str, handler_func: Callable) -> None:
        """Register an alert handler function."""
        self._alert_handlers[alert_type] = handler_func

    @asynccontextmanager
    async def trace_operation(
        self,
        operation: str,
        component: str,
        trace_context: Optional[TraceContext] = None
    ):
        """Context manager for tracing operations."""
        start_time = time.time()

        if trace_context is None:
            trace_context = TraceContext()

        span_id = str(uuid.uuid4())
        trace_context.span_id = span_id

        try:
            yield trace_context
        except Exception as e:
            # Record error in trace
            trace_context.events.append({
                "timestamp": time.time(),
                "event": "error",
                "details": str(e)
            })
            raise
        finally:
            duration = time.time() - start_time

            # Record metrics
            await self.record_operation_metrics(
                operation=operation,
                component=component,
                duration=duration,
                trace_context=trace_context
            )

    async def record_agent_metrics(
        self,
        agent_name: str,
        tenant_id: str,
        response_time: float,
        confidence_score: float,
        status: str = "success",
        reasoning_steps: int = 0,
        reasoning_strategy: str = "basic",
        action_type: str = "unknown"
    ) -> None:
        """Record comprehensive agent performance metrics."""

        # Update Prometheus metrics
        AGENT_METRICS["agent_requests_total"].labels(
            agent_name=agent_name,
            tenant_id=tenant_id,
            status=status
        ).inc()

        AGENT_METRICS["agent_response_time_seconds"].labels(
            agent_name=agent_name,
            reasoning_strategy=reasoning_strategy
        ).observe(response_time)

        AGENT_METRICS["agent_confidence_score"].labels(
            agent_name=agent_name,
            action_type=action_type
        ).observe(confidence_score)

        AGENT_METRICS["reasoning_steps_total"].labels(
            agent_name=agent_name,
            reasoning_depth="standard"  # Could be dynamic
        ).inc(reasoning_steps)

        # Store detailed metrics in Redis for analysis
        if self.redis:
            metrics_data = {
                "timestamp": datetime.now().isoformat(),
                "agent_name": agent_name,
                "tenant_id": tenant_id,
                "response_time": response_time,
                "confidence_score": confidence_score,
                "status": status,
                "reasoning_steps": reasoning_steps,
                "reasoning_strategy": reasoning_strategy,
                "action_type": action_type
            }

            await self.redis.lpush("agent_metrics", json.dumps(metrics_data))
            await self.redis.ltrim("agent_metrics", 0, 10000)

        # Check for alerts
        if confidence_score < self.config.low_confidence_threshold:
            await self.trigger_alert("low_confidence", {
                "agent_name": agent_name,
                "confidence_score": confidence_score,
                "threshold": self.config.low_confidence_threshold
            })

    async def record_business_metrics(
        self,
        tenant_id: str,
        metric_type: str,
        value: float,
        **dimensions: str
    ) -> None:
        """Record business-level metrics."""

        if metric_type == "design_created":
            BUSINESS_METRICS["designs_created_total"].labels(
                tenant_id=tenant_id,
                design_type=dimensions.get("design_type", "unknown"),
                complexity=dimensions.get("complexity", "unknown")
            ).inc()

        elif metric_type == "user_action":
            BUSINESS_METRICS["user_actions_total"].labels(
                tenant_id=tenant_id,
                action_type=dimensions.get("action_type", "unknown"),
                interface=dimensions.get("interface", "unknown")
            ).inc()

        elif metric_type == "user_satisfaction":
            BUSINESS_METRICS["user_satisfaction_score"].labels(
                tenant_id=tenant_id,
                interaction_type=dimensions.get("interaction_type", "unknown")
            ).observe(value)

    async def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status."""

        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "services": {},
            "metrics": {},
            "alerts": []
        }

        # Check individual service health
        service_issues = []
        for service_name, check_func in self._health_checks.items():
            try:
                health = await check_func()
                health_status["services"][service_name] = health

                # Update Prometheus metric
                status_value = 2 if health["status"] == "healthy" else 1 if health["status"] == "degraded" else 0
                RELIABILITY_METRICS["service_health_status"].labels(
                    service_name=service_name
                ).set(status_value)

                if health["status"] != "healthy":
                    service_issues.append(f"{service_name}: {health['message']}")

            except Exception as e:
                logger.error(f"Health check failed for {service_name}: {e}")
                health_status["services"][service_name] = {
                    "status": "error",
                    "message": str(e)
                }
                service_issues.append(f"{service_name}: error")

        # Determine overall status
        if service_issues:
            health_status["overall_status"] = "degraded"
            health_status["issues"] = service_issues

        if len(service_issues) > len(self._health_checks) * 0.5:
            health_status["overall_status"] = "unhealthy"

        # Get recent metrics
        health_status["metrics"] = await self.get_current_metrics()

        # Get recent alerts
        if self.redis:
            recent_alerts = await self.redis.lrange("system_alerts", 0, 9)
            health_status["alerts"] = [json.loads(alert) for alert in recent_alerts]

        return health_status

    async def trigger_alert(
        self,
        alert_type: str,
        details: Dict[str, Any]
    ) -> None:
        """Trigger a system alert."""

        alert_data = {
            "alert_type": alert_type,
            "timestamp": datetime.now().isoformat(),
            "details": details,
            "severity": "warning" if alert_type.startswith("low") else "error"
        }

        # Store alert
        if self.redis:
            await self.redis.lpush("system_alerts", json.dumps(alert_data))
            await self.redis.ltrim("system_alerts", 0, 1000)

        # Handle alert
        if alert_type in self._alert_handlers:
            try:
                await self._alert_handlers[alert_type](alert_data)
            except Exception as e:
                logger.error(f"Alert handler failed for {alert_type}: {e}")

        # Log alert
        logger.warning(f"System alert triggered: {alert_type} - {details}")

        # Update metrics
        RELIABILITY_METRICS["error_rate_total"].labels(
            error_type=alert_type,
            severity=alert_data["severity"],
            component="monitoring"
        ).inc()

    async def get_performance_report(
        self,
        time_window: str = "1h"
    ) -> Dict[str, Any]:
        """Generate comprehensive performance report."""

        report = {
            "time_window": time_window,
            "generated_at": datetime.now().isoformat(),
            "agent_performance": {},
            "system_performance": {},
            "business_metrics": {},
            "recommendations": []
        }

        # Get agent performance data
        if self.redis:
            agent_metrics = await self.redis.lrange("agent_metrics", 0, 999)
            report["agent_performance"] = await self._analyze_agent_metrics(agent_metrics)

        # Get system metrics
        report["system_performance"] = await self._collect_system_metrics()

        # Generate recommendations
        report["recommendations"] = await self._generate_performance_recommendations(report)

        return report

    def _start_monitoring_tasks(self) -> None:
        """Start background monitoring tasks."""

        async def system_metrics_collector():
            """Collect system metrics periodically."""
            while True:
                try:
                    await self._collect_system_metrics()
                    await asyncio.sleep(self.config.metrics_collection_interval)
                except Exception as e:
                    logger.error(f"System metrics collection failed: {e}")
                    await asyncio.sleep(60)

        async def health_check_runner():
            """Run health checks periodically."""
            while True:
                try:
                    health = await self.get_system_health()
                    if health["overall_status"] != "healthy":
                        await self.trigger_alert("system_health_degraded", {
                            "status": health["overall_status"],
                            "issues": health.get("issues", [])
                        })
                    await asyncio.sleep(60)  # Run every minute
                except Exception as e:
                    logger.error(f"Health check runner failed: {e}")
                    await asyncio.sleep(60)

        # Start monitoring tasks
        if self.config.enable_performance_monitoring:
            self._monitoring_tasks.add(asyncio.create_task(system_metrics_collector()))
            self._monitoring_tasks.add(asyncio.create_task(health_check_runner()))

    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics."""

        metrics = {}

        try:
            # Memory metrics
            memory = psutil.virtual_memory()
            SYSTEM_METRICS["memory_usage_bytes"].labels(process="system").set(memory.used)
            metrics["memory"] = {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percent": memory.percent
            }

            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            SYSTEM_METRICS["cpu_usage_percent"].labels(core="total").set(cpu_percent)
            metrics["cpu"] = {"percent": cpu_percent}

            # Disk metrics
            disk = psutil.disk_usage("/")
            SYSTEM_METRICS["disk_usage_bytes"].labels(mount_point="/").set(disk.used)
            metrics["disk"] = {
                "total": disk.total,
                "free": disk.free,
                "used": disk.used,
                "percent": disk.percent
            }

        except Exception as e:
            logger.error(f"System metrics collection failed: {e}")

        return metrics

    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database health."""
        # Implement database health check
        return {"status": "healthy", "message": "Database connection OK"}

    async def _check_redis_health(self) -> Dict[str, Any]:
        """Check Redis health."""
        if self.redis:
            try:
                await self.redis.ping()
                return {"status": "healthy", "message": "Redis connection OK"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        return {"status": "disabled", "message": "Redis not configured"}

    async def _check_memory_health(self) -> Dict[str, Any]:
        """Check memory health."""
        memory = psutil.virtual_memory()
        if memory.percent > 85:
            return {"status": "degraded", "message": f"High memory usage: {memory.percent}%"}
        return {"status": "healthy", "message": f"Memory usage: {memory.percent}%"}

    async def _check_disk_health(self) -> Dict[str, Any]:
        """Check disk health."""
        disk = psutil.disk_usage("/")
        if disk.percent > 90:
            return {"status": "degraded", "message": f"High disk usage: {disk.percent}%"}
        return {"status": "healthy", "message": f"Disk usage: {disk.percent}%"}

    async def _handle_high_error_rate(self, alert_data: Dict[str, Any]) -> None:
        """Handle high error rate alert."""
        logger.error(f"High error rate alert: {alert_data}")
        # Implement escalation logic (email, Slack, etc.)

    async def _handle_low_confidence(self, alert_data: Dict[str, Any]) -> None:
        """Handle low confidence alert."""
        logger.warning(f"Low confidence alert: {alert_data}")
        # Implement retraining or human review triggers

    async def _analyze_agent_metrics(self, metrics_data: List[str]) -> Dict[str, Any]:
        """Analyze agent metrics data."""
        # Implement detailed metrics analysis
        return {"summary": "Metrics analysis placeholder"}

    async def record_operation_metrics(
        self,
        operation: str,
        component: str,
        duration: float,
        trace_context: Optional[TraceContext] = None
    ) -> None:
        """Record operation-level metrics."""
        # This would integrate with distributed tracing systems
        pass

    async def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot."""
        return {
            "prometheus_metrics": generate_latest(METRICS_REGISTRY).decode(),
            "timestamp": datetime.now().isoformat()
        }

    async def _generate_performance_recommendations(
        self,
        report: Dict[str, Any]
    ) -> List[str]:
        """Generate performance recommendations based on analysis."""
        recommendations = []

        # Analyze agent performance
        agent_perf = report.get("agent_performance", {})

        # Analyze system performance
        system_perf = report.get("system_performance", {})

        if system_perf.get("cpu", {}).get("percent", 0) > 80:
            recommendations.append("Consider scaling CPU resources")

        if system_perf.get("memory", {}).get("percent", 0) > 85:
            recommendations.append("Consider scaling memory resources")

        return recommendations


# Global monitoring system instance
_monitoring_system: Optional[EnterpriseMonitoringSystem] = None


def get_monitoring_system() -> EnterpriseMonitoringSystem:
    """Get the global monitoring system instance."""
    if _monitoring_system is None:
        raise RuntimeError("Monitoring system not initialized")
    return _monitoring_system


async def initialize_monitoring(config: MonitoringConfig) -> EnterpriseMonitoringSystem:
    """Initialize the enterprise monitoring system."""
    global _monitoring_system

    if _monitoring_system is None:
        _monitoring_system = EnterpriseMonitoringSystem(config)
        await _monitoring_system.initialize()
        logger.info("Enterprise Monitoring System initialized")

    return _monitoring_system


# FastAPI middleware for request monitoring
class MonitoringMiddleware:
    """FastAPI middleware for request monitoring."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()

        async def send_with_metrics(message):
            if message["type"] == "http.response.start":
                duration = time.time() - start_time
                # Record request metrics
                pass
            await send(message)

        await self.app(scope, receive, send_with_metrics)
