# backend/scalability/enterprise_scalability.py
"""Enterprise-grade scalability and performance optimization for OriginFlow AI platform."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Set
from datetime import datetime, timedelta
import time
import json
import hashlib

import redis.asyncio as redis
from concurrent.futures import ThreadPoolExecutor
import aiocache
from aiocache import Cache
from prometheus_client import Histogram, Counter


logger = logging.getLogger(__name__)


# Scalability metrics
SCALABILITY_METRICS = {
    "cache_hits_total": Counter(
        "cache_hits_total",
        "Total cache hits",
        ["cache_name", "tenant_id"]
    ),
    "cache_misses_total": Counter(
        "cache_misses_total",
        "Total cache misses",
        ["cache_name", "tenant_id"]
    ),
    "queue_depth": Histogram(
        "queue_depth",
        "Current queue depth",
        ["queue_name"]
    ),
    "circuit_breaker_state": Counter(
        "circuit_breaker_state",
        "Circuit breaker state changes",
        ["service_name", "state"]
    )
}


@dataclass
class ScalabilityConfig:
    """Configuration for enterprise scalability features."""

    # Caching configuration
    enable_caching: bool = True
    cache_ttl_seconds: int = 300  # 5 minutes default
    max_cache_size_mb: int = 512

    # Connection pooling
    max_database_connections: int = 100
    connection_pool_timeout: float = 30.0

    # Queue configuration
    enable_queuing: bool = True
    max_queue_size: int = 10000
    worker_threads: int = 4

    # Circuit breaker settings
    circuit_breaker_enabled: bool = True
    failure_threshold: int = 5
    recovery_timeout_seconds: int = 60

    # Load balancing
    enable_load_balancing: bool = True
    max_concurrent_requests: int = 1000

    # Resource limits
    max_memory_percent: float = 85.0
    max_cpu_percent: float = 80.0

    # Redis configuration for distributed state
    redis_url: Optional[str] = None

    # Rate limiting per tenant
    tenant_rate_limit_per_minute: int = 1000


@dataclass
class CircuitBreakerState:
    """State of a circuit breaker."""

    service_name: str
    is_open: bool = False
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    recovery_time: Optional[datetime] = None


@dataclass
class CacheEntry:
    """Cached data entry with metadata."""

    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    ttl_seconds: int = 300
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)


class EnterpriseCache:
    """Enterprise-grade caching system with Redis backing."""

    def __init__(self, config: ScalabilityConfig):
        self.config = config
        self.redis: Optional[redis.Redis] = None
        self.local_cache: Dict[str, CacheEntry] = {}
        self.cache_size_bytes = 0

        # Initialize aiocache for local caching
        self.cache = Cache(
            Cache.MEMORY,
            ttl=config.cache_ttl_seconds,
            max_size=10000
        )

        if config.redis_url:
            self.redis = redis.from_url(config.redis_url)

    async def initialize(self) -> None:
        """Initialize the cache system."""
        if self.redis:
            await self.redis.ping()
            logger.info("Redis cache backend connected")

        logger.info("Enterprise Cache System initialized")

    async def get(self, key: str, tenant_id: str = "default") -> Optional[Any]:
        """Get value from cache with tenant isolation."""

        cache_key = self._make_cache_key(key, tenant_id)

        # Try local cache first
        if cache_key in self.local_cache:
            entry = self.local_cache[cache_key]
            if not self._is_expired(entry):
                entry.access_count += 1
                entry.last_accessed = datetime.now()
                SCALABILITY_METRICS["cache_hits_total"].labels(
                    cache_name="local", tenant_id=tenant_id
                ).inc()
                return entry.value

        # Try Redis cache
        if self.redis:
            try:
                value = await self.redis.get(cache_key)
                if value is not None:
                    # Deserialize and store locally
                    data = json.loads(value)
                    entry = CacheEntry(
                        key=cache_key,
                        value=data["value"],
                        ttl_seconds=data["ttl_seconds"]
                    )
                    self.local_cache[cache_key] = entry
                    SCALABILITY_METRICS["cache_hits_total"].labels(
                        cache_name="redis", tenant_id=tenant_id
                    ).inc()
                    return entry.value
            except Exception as e:
                logger.warning(f"Redis cache get failed: {e}")

        SCALABILITY_METRICS["cache_misses_total"].labels(
            cache_name="total", tenant_id=tenant_id
        ).inc()
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        tenant_id: str = "default"
    ) -> bool:
        """Set value in cache with tenant isolation."""

        cache_key = self._make_cache_key(key, tenant_id)
        ttl = ttl_seconds or self.config.cache_ttl_seconds

        entry = CacheEntry(
            key=cache_key,
            value=value,
            ttl_seconds=ttl
        )

        # Store locally
        self.local_cache[cache_key] = entry

        # Clean expired entries periodically
        await self._cleanup_expired_entries()

        # Store in Redis if available
        if self.redis:
            try:
                data = {
                    "value": value,
                    "ttl_seconds": ttl,
                    "created_at": datetime.now().isoformat()
                }
                await self.redis.setex(cache_key, ttl, json.dumps(data))
                return True
            except Exception as e:
                logger.warning(f"Redis cache set failed: {e}")

        return True

    async def invalidate(self, key_pattern: str, tenant_id: str = "default") -> int:
        """Invalidate cache entries matching pattern."""

        cache_key_pattern = self._make_cache_key(key_pattern, tenant_id)
        invalidated_count = 0

        # Invalidate local cache
        keys_to_remove = [
            k for k in self.local_cache.keys()
            if k.startswith(cache_key_pattern.rstrip("*"))
        ]

        for key in keys_to_remove:
            del self.local_cache[key]
            invalidated_count += 1

        # Invalidate Redis cache
        if self.redis:
            try:
                # Redis pattern matching for invalidation
                keys = await self.redis.keys(f"{cache_key_pattern}*")
                if keys:
                    await self.redis.delete(*keys)
                    invalidated_count += len(keys)
            except Exception as e:
                logger.warning(f"Redis cache invalidation failed: {e}")

        return invalidated_count

    def _make_cache_key(self, key: str, tenant_id: str) -> str:
        """Create tenant-isolated cache key."""
        return f"cache:{tenant_id}:{key}"

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired."""
        return datetime.now() - entry.created_at > timedelta(seconds=entry.ttl_seconds)

    async def _cleanup_expired_entries(self) -> None:
        """Clean up expired cache entries."""
        expired_keys = [
            key for key, entry in self.local_cache.items()
            if self._is_expired(entry)
        ]

        for key in expired_keys:
            del self.local_cache[key]


class CircuitBreakerManager:
    """Enterprise circuit breaker implementation."""

    def __init__(self, config: ScalabilityConfig):
        self.config = config
        self.breakers: Dict[str, CircuitBreakerState] = {}
        self.redis: Optional[redis.Redis] = None

        if config.redis_url:
            self.redis = redis.from_url(config.redis_url)

    async def initialize(self) -> None:
        """Initialize circuit breaker manager."""
        if self.redis:
            await self.redis.ping()
            logger.info("Circuit breaker Redis backend connected")

    @asynccontextmanager
    async def protect_service(self, service_name: str):
        """Context manager to protect service calls with circuit breaker."""

        if not self.config.circuit_breaker_enabled:
            yield
            return

        state = self.breakers.get(service_name, CircuitBreakerState(service_name))

        # Check if circuit is open
        if state.is_open:
            if (datetime.now() - (state.recovery_time or datetime.now()) >
                timedelta(seconds=self.config.recovery_timeout_seconds)):
                # Try to close the circuit
                state.is_open = False
                state.failure_count = 0
                logger.info(f"Circuit breaker for {service_name} attempting recovery")
            else:
                raise Exception(f"Service {service_name} is currently unavailable (circuit breaker open)")

        try:
            yield
            # Success - reset failure count
            state.failure_count = 0
            state.recovery_time = None

        except Exception as e:
            # Failure - increment failure count
            state.failure_count += 1
            state.last_failure_time = datetime.now()

            if state.failure_count >= self.config.failure_threshold:
                state.is_open = True
                state.recovery_time = datetime.now()
                SCALABILITY_METRICS["circuit_breaker_state"].labels(
                    service_name=service_name, state="open"
                ).inc()
                logger.warning(f"Circuit breaker for {service_name} opened due to failures")

            raise e

        # Store updated state
        self.breakers[service_name] = state


class EnterpriseQueueManager:
    """Enterprise-grade queue management for background tasks."""

    def __init__(self, config: ScalabilityConfig):
        self.config = config
        self.redis: Optional[redis.Redis] = None
        self.executor = ThreadPoolExecutor(max_workers=config.worker_threads)
        self.queues: Dict[str, asyncio.Queue] = {}

        if config.redis_url:
            self.redis = redis.from_url(config.redis_url)

    async def initialize(self) -> None:
        """Initialize queue manager."""
        if self.redis:
            await self.redis.ping()
            logger.info("Queue manager Redis backend connected")

        # Create default queues
        self.queues["default"] = asyncio.Queue(maxsize=self.config.max_queue_size)
        self.queues["agent_tasks"] = asyncio.Queue(maxsize=self.config.max_queue_size)
        self.queues["background_jobs"] = asyncio.Queue(maxsize=self.config.max_queue_size)

    async def enqueue_task(
        self,
        queue_name: str,
        task_data: Dict[str, Any],
        priority: int = 5
    ) -> str:
        """Enqueue a task for background processing."""

        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(json.dumps(task_data).encode()).hexdigest()[:8]}"

        task = {
            "task_id": task_id,
            "data": task_data,
            "priority": priority,
            "created_at": datetime.now().isoformat(),
            "status": "queued"
        }

        # Add to local queue
        if queue_name in self.queues:
            await self.queues[queue_name].put(task)

            # Update queue depth metric
            SCALABILITY_METRICS["queue_depth"].labels(queue_name=queue_name).observe(
                self.queues[queue_name].qsize()
            )

        # Store in Redis for persistence
        if self.redis:
            await self.redis.lpush(f"queue:{queue_name}", json.dumps(task))
            await self.redis.ltrim(f"queue:{queue_name}", 0, self.config.max_queue_size)

        logger.info(f"Enqueued task {task_id} to queue {queue_name}")
        return task_id

    async def dequeue_task(self, queue_name: str) -> Optional[Dict[str, Any]]:
        """Dequeue a task for processing."""

        if queue_name not in self.queues:
            return None

        try:
            # Try local queue first
            task = await asyncio.wait_for(
                self.queues[queue_name].get(),
                timeout=1.0
            )
            return task
        except asyncio.TimeoutError:
            # Try Redis queue
            if self.redis:
                result = await self.redis.rpop(f"queue:{queue_name}")
                if result:
                    return json.loads(result)

        return None

    async def process_queue(self, queue_name: str, handler: Callable) -> None:
        """Process tasks from a queue with the given handler."""

        while True:
            try:
                task = await self.dequeue_task(queue_name)
                if task:
                    # Process task in thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(
                        self.executor,
                        self._process_task_sync,
                        handler,
                        task
                    )
                else:
                    await asyncio.sleep(1)  # Wait before checking again

            except Exception as e:
                logger.error(f"Queue processing error: {e}")
                await asyncio.sleep(5)  # Back off on error

    def _process_task_sync(self, handler: Callable, task: Dict[str, Any]) -> None:
        """Process task synchronously in thread pool."""
        try:
            # Convert async handler to sync if needed
            import inspect
            if inspect.iscoroutinefunction(handler):
                # This is a simplified approach - in practice you'd need proper async handling
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(handler(task))
                loop.close()
            else:
                result = handler(task)

            logger.info(f"Task {task['task_id']} processed successfully")

        except Exception as e:
            logger.error(f"Task {task['task_id']} processing failed: {e}")


class LoadBalancer:
    """Simple load balancing for enterprise deployments."""

    def __init__(self, config: ScalabilityConfig):
        self.config = config
        self.redis: Optional[redis.Redis] = None
        self.instance_id = f"instance_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.active_requests = 0

        if config.redis_url:
            self.redis = redis.from_url(config.redis_url)

    async def initialize(self) -> None:
        """Initialize load balancer."""
        if self.redis:
            await self.redis.ping()
            await self.redis.sadd("active_instances", self.instance_id)
            logger.info(f"Load balancer initialized with instance ID: {self.instance_id}")

    @asynccontextmanager
    async def handle_request(self):
        """Context manager to handle request with load balancing."""

        if not self.config.enable_load_balancing:
            yield
            return

        # Check if we can handle more requests
        if self.active_requests >= self.config.max_concurrent_requests:
            raise Exception("Instance at capacity")

        self.active_requests += 1

        try:
            # Update instance load in Redis
            if self.redis:
                await self.redis.hset("instance_load", self.instance_id, str(self.active_requests))

            yield

        finally:
            self.active_requests -= 1
            if self.redis:
                await self.redis.hset("instance_load", self.instance_id, str(self.active_requests))

    async def get_healthiest_instance(self) -> str:
        """Get the healthiest instance for load balancing."""
        if not self.redis:
            return self.instance_id

        try:
            # Get all active instances and their loads
            instances = await self.redis.smembers("active_instances")
            loads = await self.redis.hgetall("instance_load")

            # Find instance with lowest load
            lowest_load = float('inf')
            selected_instance = self.instance_id

            for instance in instances:
                load = int(loads.get(instance.decode(), 0))
                if load < lowest_load:
                    lowest_load = load
                    selected_instance = instance.decode()

            return selected_instance

        except Exception as e:
            logger.warning(f"Load balancing health check failed: {e}")
            return self.instance_id


# Global instances
_cache: Optional[EnterpriseCache] = None
_circuit_breaker: Optional[CircuitBreakerManager] = None
_queue_manager: Optional[EnterpriseQueueManager] = None
_load_balancer: Optional[LoadBalancer] = None


async def initialize_scalability(config: ScalabilityConfig) -> Dict[str, Any]:
    """Initialize all enterprise scalability components."""

    global _cache, _circuit_breaker, _queue_manager, _load_balancer

    components = {}

    # Initialize cache
    if config.enable_caching:
        _cache = EnterpriseCache(config)
        await _cache.initialize()
        components["cache"] = _cache

    # Initialize circuit breaker
    if config.circuit_breaker_enabled:
        _circuit_breaker = CircuitBreakerManager(config)
        await _circuit_breaker.initialize()
        components["circuit_breaker"] = _circuit_breaker

    # Initialize queue manager
    if config.enable_queuing:
        _queue_manager = EnterpriseQueueManager(config)
        await _queue_manager.initialize()
        components["queue_manager"] = _queue_manager

    # Initialize load balancer
    if config.enable_load_balancing:
        _load_balancer = LoadBalancer(config)
        await _load_balancer.initialize()
        components["load_balancer"] = _load_balancer

    logger.info("Enterprise Scalability System initialized")
    return components


def get_cache() -> EnterpriseCache:
    """Get the global cache instance."""
    if _cache is None:
        raise RuntimeError("Cache not initialized")
    return _cache


def get_circuit_breaker() -> CircuitBreakerManager:
    """Get the global circuit breaker instance."""
    if _circuit_breaker is None:
        raise RuntimeError("Circuit breaker not initialized")
    return _circuit_breaker


def get_queue_manager() -> EnterpriseQueueManager:
    """Get the global queue manager instance."""
    if _queue_manager is None:
        raise RuntimeError("Queue manager not initialized")
    return _queue_manager


def get_load_balancer() -> LoadBalancer:
    """Get the global load balancer instance."""
    if _load_balancer is None:
        raise RuntimeError("Load balancer not initialized")
    return _load_balancer
