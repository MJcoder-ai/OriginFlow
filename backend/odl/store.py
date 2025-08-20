"""
Persistence and optimistic concurrency for ODL graphs.

Default implementation stores the entire graph JSON plus a separate table for
op idempotency tracking (patch/operation ids).  Swap this for a more granular
storage if/when needed.
"""
from __future__ import annotations

from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from sqlalchemy import Table, Column, String, Integer, JSON, MetaData, select, insert, update, UniqueConstraint
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy.exc import IntegrityError

from backend.odl.schemas import ODLGraph, ODLPatch
from backend.odl.patches import apply_patch


metadata = MetaData()

graphs = Table(
    "odl_graphs", metadata,
    Column("session_id", String, primary_key=True),
    Column("version", Integer, nullable=False),
    Column("graph_json", JSON, nullable=False),
)

idempotency = Table(
    "odl_idempotency", metadata,
    Column("session_id", String, nullable=False),
    Column("op_id", String, nullable=False),
    UniqueConstraint("session_id", "op_id", name="uq_odl_idempotency"),
)


@dataclass
class ODLStore:
    """ODL persistence with optimistic concurrency and idempotency."""
    engine: Optional[AsyncEngine] = None

    async def init_schema(self, db: AsyncSession) -> None:
        engine = db.bind
        async with engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

    # --- core operations ---
    async def create_graph(self, db: AsyncSession, session_id: str) -> ODLGraph:
        g = ODLGraph(session_id=session_id, version=1, nodes={}, edges=[], meta={})
        await db.execute(
            insert(graphs).values(
                session_id=session_id,
                version=g.version,
                graph_json=g.model_dump(),
            )
        )
        await db.commit()
        return g

    async def get_graph(self, db: AsyncSession, session_id: str) -> Optional[ODLGraph]:
        result = await db.execute(select(graphs).where(graphs.c.session_id == session_id))
        row = result.fetchone()
        if not row:
            return None
        data = row._mapping["graph_json"]
        return ODLGraph.model_validate(data)

    async def apply_patch_cas(
        self,
        db: AsyncSession,
        session_id: str,
        expected_version: int,
        patch: ODLPatch,
    ) -> Tuple[ODLGraph, int]:
        current = await self.get_graph(db, session_id)
        if current is None:
            raise KeyError("Session not found")
        if current.version != expected_version:
            raise ValueError(f"Version mismatch: expected {expected_version}, got {current.version}")

        applied_op_ids: Dict[str, bool] = {}
        new_graph, applied_op_ids = apply_patch(current, patch, applied_op_ids)
        new_version = current.version + 1

        for op in patch.operations:
            try:
                await db.execute(insert(idempotency).values(session_id=session_id, op_id=op.op_id))
            except IntegrityError:
                pass

        await db.execute(
            update(graphs)
            .where(graphs.c.session_id == session_id)
            .values(version=new_version, graph_json=new_graph.model_dump())
        )
        await db.commit()
        new_graph.version = new_version
        return new_graph, new_version
