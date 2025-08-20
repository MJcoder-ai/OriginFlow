# backend/integration/enterprise_integration_hub.py
"""Enterprise integration hub for connecting with external systems and APIs."""

from __future__ import annotations

import asyncio
import logging
import json
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Set, Union
from datetime import datetime, timedelta
from enum import Enum

import aiohttp
import redis.asyncio as redis
from fastapi import HTTPException, status
from prometheus_client import Counter, Histogram, Gauge, Summary
import xml.etree.ElementTree as ET

from backend.utils.logging import get_logger
from backend.utils.observability import trace_span, record_metric
from backend.services.enterprise_cache import get_cache
from backend.services.enterprise_security import get_security_manager


logger = get_logger(__name__)


# Integration metrics
INTEGRATION_METRICS = {
    "api_requests_total": Counter(
        "api_requests_total",
        "Total API requests by endpoint and status",
        ["endpoint", "method", "status", "integration_type"]
    ),
    "integration_latency_seconds": Histogram(
        "integration_latency_seconds",
        "Integration request latency",
        ["integration_type", "endpoint"]
    ),
    "active_integrations": Gauge(
        "active_integrations",
        "Number of active integrations",
        ["integration_type"]
    ),
    "data_sync_success_rate": Gauge(
        "data_sync_success_rate",
        "Data synchronization success rate",
        ["integration_type"]
    ),
    "external_api_errors_total": Counter(
        "external_api_errors_total",
        "Total external API errors",
        ["integration_type", "error_type"]
    )
}


class IntegrationType(Enum):
    """Types of integrations supported."""

    REST_API = "rest_api"
    SOAP_API = "soap_api"
    GRAPHQL_API = "graphql_api"
    DATABASE = "database"
    MESSAGE_QUEUE = "message_queue"
    FILE_SYSTEM = "file_system"
    CLOUD_STORAGE = "cloud_storage"
    ENTERPRISE_SERVICE_BUS = "esb"


class SyncDirection(Enum):
    """Data synchronization directions."""

    INBOUND = "inbound"   # External -> OriginFlow
    OUTBOUND = "outbound" # OriginFlow -> External
    BIDIRECTIONAL = "bidirectional"


class IntegrationStatus(Enum):
    """Integration status states."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    DEGRADED = "degraded"


@dataclass
class IntegrationConfig:
    """Configuration for an integration endpoint."""

    name: str
    integration_type: IntegrationType
    base_url: str
    auth_type: str = "bearer"  # bearer, basic, api_key, oauth2
    auth_config: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    timeout_seconds: int = 30
    retry_count: int = 3
    retry_delay_seconds: float = 1.0
    rate_limit_per_minute: int = 60
    circuit_breaker_enabled: bool = True
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300

    # Database-specific config
    connection_string: Optional[str] = None
    query_timeout_seconds: int = 60

    # Message queue config
    queue_name: Optional[str] = None
    message_format: str = "json"

    # File system config
    root_path: Optional[str] = None
    file_pattern: Optional[str] = None


@dataclass
class DataMapping:
    """Data mapping configuration for field transformations."""

    source_field: str
    target_field: str
    field_type: str = "string"
    transformation: Optional[str] = None  # json_path, regex_extract, date_format, etc.
    transformation_config: Dict[str, Any] = field(default_factory=dict)
    required: bool = False
    default_value: Optional[Any] = None


@dataclass
class SyncJob:
    """Data synchronization job configuration."""

    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    source_integration: str
    target_integration: str
    sync_direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    sync_frequency_minutes: int = 60
    data_mappings: List[DataMapping] = field(default_factory=list)
    filter_conditions: Dict[str, Any] = field(default_factory=dict)
    batch_size: int = 100
    error_handling: str = "skip"  # skip, stop, retry
    enabled: bool = True

    # Runtime state
    last_sync_time: Optional[datetime] = None
    next_sync_time: Optional[datetime] = None
    sync_status: str = "pending"
    records_processed: int = 0
    errors_count: int = 0


@dataclass
class IntegrationResult:
    """Result of an integration operation."""

    success: bool
    data: Any = None
    error_message: str = ""
    status_code: Optional[int] = None
    execution_time: float = 0.0
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class EnterpriseIntegrationHub:
    """Central hub for managing all enterprise integrations."""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.EnterpriseIntegrationHub")

        # Integration storage
        self.integrations: Dict[str, IntegrationConfig] = {}
        self.sync_jobs: Dict[str, SyncJob] = {}
        self.session_pools: Dict[str, aiohttp.ClientSession] = {}

        # Services
        self.cache = get_cache()
        self.security = get_security_manager()
        self.redis: Optional[redis.Redis] = None

        # Runtime state
        self._running_jobs: Set[str] = set()
        self._job_tasks: Dict[str, asyncio.Task] = {}

        # Initialize integrations
        self._initialize_default_integrations()

    async def initialize(self) -> None:
        """Initialize the integration hub."""

        self.logger.info("Enterprise Integration Hub initialized")

        # Start background sync jobs
        await self._start_sync_scheduler()

    async def cleanup(self) -> None:
        """Cleanup integration resources."""

        # Cancel all running jobs
        for task in self._job_tasks.values():
            task.cancel()

        # Close all sessions
        for session in self.session_pools.values():
            await session.close()

        if self.redis:
            await self.redis.aclose()

        self.logger.info("Integration Hub cleaned up")

    def register_integration(self, config: IntegrationConfig) -> None:
        """Register a new integration."""

        self.integrations[config.name] = config

        # Create HTTP session for REST/GraphQL APIs
        if config.integration_type in [IntegrationType.REST_API, IntegrationType.GRAPHQL_API]:
            connector = aiohttp.TCPConnector(limit=100, ttl_dns_cache=300)
            timeout = aiohttp.ClientTimeout(total=config.timeout_seconds)
            self.session_pools[config.name] = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=config.headers
            )

        self.logger.info(f"Registered integration: {config.name}")

    def register_sync_job(self, job: SyncJob) -> None:
        """Register a data synchronization job."""

        self.sync_jobs[job.job_id] = job
        self.logger.info(f"Registered sync job: {job.name}")

    async def execute_integration(
        self,
        integration_name: str,
        operation: str,
        **kwargs: Any
    ) -> IntegrationResult:
        """Execute an integration operation."""

        start_time = asyncio.get_event_loop().time()

        try:
            if integration_name not in self.integrations:
                raise ValueError(f"Integration {integration_name} not found")

            config = self.integrations[integration_name]

            # Check cache first
            cache_key = f"integration:{integration_name}:{operation}:{hash(json.dumps(kwargs, sort_keys=True))}"
            if config.cache_enabled:
                cached_result = await self.cache.get(cache_key)
                if cached_result:
                    return cached_result

            # Execute based on integration type
            if config.integration_type == IntegrationType.REST_API:
                result = await self._execute_rest_api(config, operation, **kwargs)
            elif config.integration_type == IntegrationType.SOAP_API:
                result = await self._execute_soap_api(config, operation, **kwargs)
            elif config.integration_type == IntegrationType.GRAPHQL_API:
                result = await self._execute_graphql_api(config, operation, **kwargs)
            else:
                raise ValueError(f"Unsupported integration type: {config.integration_type}")

            execution_time = asyncio.get_event_loop().time() - start_time
            result.execution_time = execution_time

            # Cache successful results
            if result.success and config.cache_enabled:
                await self.cache.set(cache_key, result, ttl_seconds=config.cache_ttl_seconds)

            # Record metrics
            INTEGRATION_METRICS["api_requests_total"].labels(
                endpoint=operation,
                method="POST",  # Simplified
                status="success" if result.success else "error",
                integration_type=config.integration_type.value
            ).inc()

            INTEGRATION_METRICS["integration_latency_seconds"].labels(
                integration_type=config.integration_type.value,
                endpoint=operation
            ).observe(execution_time)

            return result

        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            self.logger.error(f"Integration execution failed: {e}", exc_info=True)

            return IntegrationResult(
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )

    async def execute_sync_job(self, job_id: str) -> Dict[str, Any]:
        """Execute a data synchronization job."""

        if job_id not in self.sync_jobs:
            raise ValueError(f"Sync job {job_id} not found")

        job = self.sync_jobs[job_id]

        if not job.enabled:
            return {"status": "disabled", "job_id": job_id}

        if job_id in self._running_jobs:
            return {"status": "already_running", "job_id": job_id}

        self._running_jobs.add(job_id)
        start_time = datetime.now()

        try:
            self.logger.info(f"Starting sync job: {job.name}")

            # Execute synchronization based on direction
            if job.sync_direction == SyncDirection.INBOUND:
                result = await self._execute_inbound_sync(job)
            elif job.sync_direction == SyncDirection.OUTBOUND:
                result = await self._execute_outbound_sync(job)
            else:  # BIDIRECTIONAL
                inbound_result = await self._execute_inbound_sync(job)
                outbound_result = await self._execute_outbound_sync(job)
                result = {
                    "inbound": inbound_result,
                    "outbound": outbound_result
                }

            # Update job state
            job.last_sync_time = start_time
            job.next_sync_time = start_time + timedelta(minutes=job.sync_frequency_minutes)
            job.sync_status = "success"
            job.records_processed = result.get("records_processed", 0)
            job.errors_count = result.get("errors_count", 0)

            return {
                "status": "success",
                "job_id": job_id,
                "execution_time": (datetime.now() - start_time).total_seconds(),
                "result": result
            }

        except Exception as e:
            job.sync_status = "error"
            job.errors_count += 1

            self.logger.error(f"Sync job failed: {e}", exc_info=True)
            return {
                "status": "error",
                "job_id": job_id,
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds()
            }

        finally:
            self._running_jobs.discard(job_id)

    async def get_integration_status(self) -> Dict[str, Any]:
        """Get comprehensive integration status."""

        status = {
            "timestamp": datetime.now().isoformat(),
            "integrations": {},
            "sync_jobs": {},
            "metrics": {}
        }

        # Integration status
        for name, config in self.integrations.items():
            status["integrations"][name] = {
                "type": config.integration_type.value,
                "status": IntegrationStatus.ACTIVE.value,  # Simplified
                "last_used": None,  # Would track in real implementation
                "error_count": 0
            }

        # Sync job status
        for job_id, job in self.sync_jobs.items():
            status["sync_jobs"][job_id] = {
                "name": job.name,
                "enabled": job.enabled,
                "status": job.sync_status,
                "last_sync": job.last_sync_time.isoformat() if job.last_sync_time else None,
                "next_sync": job.next_sync_time.isoformat() if job.next_sync_time else None,
                "records_processed": job.records_processed,
                "errors_count": job.errors_count
            }

        # Integration metrics
        status["metrics"] = {
            "active_integrations": len(self.integrations),
            "running_sync_jobs": len(self._running_jobs),
            "total_sync_jobs": len(self.sync_jobs)
        }

        return status

    async def test_integration(self, integration_name: str) -> Dict[str, Any]:
        """Test an integration connection."""

        try:
            if integration_name not in self.integrations:
                return {"success": False, "error": "Integration not found"}

            config = self.integrations[integration_name]

            # Execute a test operation
            test_result = await self.execute_integration(
                integration_name,
                "test_connection"
            )

            return {
                "success": test_result.success,
                "response_time": test_result.execution_time,
                "error": test_result.error_message if not test_result.success else None
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _initialize_default_integrations(self) -> None:
        """Initialize default enterprise integrations."""

        # Example: ERP System Integration
        erp_config = IntegrationConfig(
            name="erp_system",
            integration_type=IntegrationType.REST_API,
            base_url="https://erp.example.com/api/v1",
            auth_type="oauth2",
            auth_config={
                "client_id": "originflow_client",
                "client_secret": "encrypted_secret",
                "token_url": "https://erp.example.com/oauth/token"
            },
            headers={"Accept": "application/json"}
        )
        self.register_integration(erp_config)

        # Example: CRM Integration
        crm_config = IntegrationConfig(
            name="crm_system",
            integration_type=IntegrationType.REST_API,
            base_url="https://crm.example.com/api/v2",
            auth_type="api_key",
            auth_config={"api_key": "encrypted_key"},
            headers={"Authorization": "Bearer encrypted_token"}
        )
        self.register_integration(crm_config)

        # Example: External Data Provider
        data_provider_config = IntegrationConfig(
            name="market_data",
            integration_type=IntegrationType.GRAPHQL_API,
            base_url="https://data.example.com/graphql",
            auth_type="bearer",
            auth_config={"token": "encrypted_token"}
        )
        self.register_integration(data_provider_config)

        # Example: Document Management System
        dms_config = IntegrationConfig(
            name="document_management",
            integration_type=IntegrationType.REST_API,
            base_url="https://dms.example.com/api/v1",
            auth_type="basic",
            auth_config={
                "username": "originflow_user",
                "password": "encrypted_password"
            }
        )
        self.register_integration(dms_config)

    async def _execute_rest_api(
        self,
        config: IntegrationConfig,
        operation: str,
        **kwargs: Any
    ) -> IntegrationResult:
        """Execute REST API integration."""

        session = self.session_pools.get(config.name)
        if not session:
            raise ValueError(f"No session available for {config.name}")

        # Build URL and determine method
        url = f"{config.base_url}/{operation}"
        method = kwargs.get("method", "GET").upper()

        # Build request data
        request_data = {
            "method": method,
            "url": url,
            "headers": config.headers.copy()
        }

        if method in ["POST", "PUT", "PATCH"]:
            request_data["json"] = kwargs.get("data", {})
        elif method == "GET":
            request_data["params"] = kwargs.get("params", {})

        # Add authentication
        await self._add_authentication(config, request_data)

        # Execute with retry logic
        result = await self._execute_with_retry(
            session, request_data, config.retry_count, config.retry_delay_seconds
        )

        return result

    async def _execute_soap_api(
        self,
        config: IntegrationConfig,
        operation: str,
        **kwargs: Any
    ) -> IntegrationResult:
        """Execute SOAP API integration."""

        session = self.session_pools.get(config.name)
        if not session:
            raise ValueError(f"No session available for {config.name}")

        # Build SOAP envelope
        soap_envelope = self._build_soap_envelope(operation, kwargs)

        headers = config.headers.copy()
        headers["Content-Type"] = "text/xml; charset=utf-8"

        request_data = {
            "method": "POST",
            "url": config.base_url,
            "data": soap_envelope,
            "headers": headers
        }

        # Add authentication
        await self._add_authentication(config, request_data)

        result = await self._execute_with_retry(
            session, request_data, config.retry_count, config.retry_delay_seconds
        )

        # Parse SOAP response
        if result.success and result.data:
            result.data = self._parse_soap_response(result.data)

        return result

    async def _execute_graphql_api(
        self,
        config: IntegrationConfig,
        operation: str,
        **kwargs: Any
    ) -> IntegrationResult:
        """Execute GraphQL API integration."""

        session = self.session_pools.get(config.name)
        if not session:
            raise ValueError(f"No session available for {config.name}")

        # Build GraphQL query
        query = kwargs.get("query", "")
        variables = kwargs.get("variables", {})

        request_data = {
            "method": "POST",
            "url": config.base_url,
            "json": {
                "query": query,
                "variables": variables
            },
            "headers": {**config.headers, "Content-Type": "application/json"}
        }

        # Add authentication
        await self._add_authentication(config, request_data)

        result = await self._execute_with_retry(
            session, request_data, config.retry_count, config.retry_delay_seconds
        )

        # Parse GraphQL response
        if result.success and result.data:
            result.data = result.data.get("data", {}) if isinstance(result.data, dict) else result.data

        return result

    async def _execute_with_retry(
        self,
        session: aiohttp.ClientSession,
        request_data: Dict[str, Any],
        max_retries: int,
        retry_delay: float
    ) -> IntegrationResult:
        """Execute HTTP request with retry logic."""

        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                start_time = asyncio.get_event_loop().time()

                async with session.request(**request_data) as response:
                    execution_time = asyncio.get_event_loop().time() - start_time

                    if response.status < 400:
                        # Success
                        try:
                            data = await response.json()
                        except:
                            data = await response.text()

                        return IntegrationResult(
                            success=True,
                            data=data,
                            status_code=response.status,
                            execution_time=execution_time
                        )
                    else:
                        # Error
                        error_text = await response.text()
                        if attempt == max_retries:
                            return IntegrationResult(
                                success=False,
                                error_message=f"HTTP {response.status}: {error_text}",
                                status_code=response.status,
                                execution_time=execution_time
                            )

            except Exception as e:
                last_exception = e
                if attempt == max_retries:
                    break

            # Wait before retry
            if attempt < max_retries:
                await asyncio.sleep(retry_delay * (2 ** attempt))  # Exponential backoff

        return IntegrationResult(
            success=False,
            error_message=str(last_exception),
            execution_time=0.0
        )

    async def _add_authentication(
        self,
        config: IntegrationConfig,
        request_data: Dict[str, Any]
    ) -> None:
        """Add authentication to request."""

        headers = request_data.get("headers", {})

        if config.auth_type == "bearer":
            token = await self.security.generate_secure_token(config.auth_config)
            headers["Authorization"] = f"Bearer {token}"
        elif config.auth_type == "basic":
            import base64
            credentials = base64.b64encode(
                f"{config.auth_config['username']}:{config.auth_config['password']}".encode()
            ).decode()
            headers["Authorization"] = f"Basic {credentials}"
        elif config.auth_type == "api_key":
            headers["X-API-Key"] = config.auth_config["api_key"]
        elif config.auth_type == "oauth2":
            # In practice, this would handle OAuth2 token refresh
            headers["Authorization"] = f"Bearer {config.auth_config.get('access_token', '')}"

        request_data["headers"] = headers

    def _build_soap_envelope(self, operation: str, data: Dict[str, Any]) -> str:
        """Build SOAP envelope for SOAP API calls."""

        # Simplified SOAP envelope builder
        envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <{operation} xmlns="http://example.com/service">
"""

        for key, value in data.items():
            envelope += f"      <{key}>{value}</{key}>\n"

        envelope += f"""    </{operation}>
  </soap:Body>
</soap:Envelope>"""

        return envelope

    def _parse_soap_response(self, response: str) -> Dict[str, Any]:
        """Parse SOAP response."""

        try:
            root = ET.fromstring(response)
            # Simplified parsing - in practice would be more sophisticated
            return {"parsed": True, "raw_response": response}
        except Exception:
            return {"parsed": False, "raw_response": response}

    async def _execute_inbound_sync(self, job: SyncJob) -> Dict[str, Any]:
        """Execute inbound data synchronization."""

        # Simplified implementation
        return {
            "direction": "inbound",
            "records_processed": 100,
            "errors_count": 2,
            "status": "success"
        }

    async def _execute_outbound_sync(self, job: SyncJob) -> Dict[str, Any]:
        """Execute outbound data synchronization."""

        # Simplified implementation
        return {
            "direction": "outbound",
            "records_processed": 95,
            "errors_count": 1,
            "status": "success"
        }

    async def _start_sync_scheduler(self) -> None:
        """Start the sync job scheduler."""

        async def scheduler():
            while True:
                try:
                    await asyncio.sleep(60)  # Check every minute

                    current_time = datetime.now()

                    for job in self.sync_jobs.values():
                        if (job.enabled and
                            job.next_sync_time and
                            current_time >= job.next_sync_time and
                            job.job_id not in self._running_jobs):

                            # Start sync job
                            task = asyncio.create_task(self.execute_sync_job(job.job_id))
                            self._job_tasks[job.job_id] = task

                except Exception as e:
                    self.logger.error(f"Sync scheduler error: {e}")
                    await asyncio.sleep(60)

        # Start scheduler
        asyncio.create_task(scheduler())


# Global integration hub instance
_integration_hub: Optional[EnterpriseIntegrationHub] = None


def get_integration_hub() -> EnterpriseIntegrationHub:
    """Get the global integration hub instance."""
    if _integration_hub is None:
        raise RuntimeError("Integration hub not initialized")
    return _integration_hub


async def initialize_integration_hub() -> EnterpriseIntegrationHub:
    """Initialize the enterprise integration hub."""
    global _integration_hub

    if _integration_hub is None:
        _integration_hub = EnterpriseIntegrationHub()
        await _integration_hub.initialize()
        logger.info("Enterprise Integration Hub initialized")

    return _integration_hub


# Example usage functions
async def execute_enterprise_integration(
    integration_name: str,
    operation: str,
    **kwargs: Any
) -> IntegrationResult:
    """Execute an enterprise integration."""

    hub = get_integration_hub()
    return await hub.execute_integration(integration_name, operation, **kwargs)


async def sync_enterprise_data(job_id: str) -> Dict[str, Any]:
    """Execute enterprise data synchronization."""

    hub = get_integration_hub()
    return await hub.execute_sync_job(job_id)


async def get_integration_status() -> Dict[str, Any]:
    """Get enterprise integration status."""

    hub = get_integration_hub()
    return await hub.get_integration_status()
