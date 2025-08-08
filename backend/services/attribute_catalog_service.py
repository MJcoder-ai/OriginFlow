from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class CatalogAttr:
    attribute_id: str
    key: str
    display_label: str
    data_type: str
    unit_default: Optional[str]
    cardinality: str
    category: str
    synonyms: list[str]
    applicable_types: list[str]

class AttributeCatalogService:
    def __init__(self, repo):  # repo abstracts DB access
        self.repo = repo

    async def find_by_key_or_synonym(self, key: str, component_type_id: str) -> Optional[CatalogAttr]:
        # TODO: replace with real repo lookup
        if self.repo is None:
            return None
        return await self.repo.lookup_attribute(key, component_type_id)

    async def normalize_value(self, catalog_attr: CatalogAttr, raw_value: Any, raw_unit: Optional[str]) -> tuple[Any, Optional[str]]:
        unit = raw_unit or catalog_attr.unit_default
        if catalog_attr.data_type in ("number","integer"):
            try:
                v = float(raw_value) if catalog_attr.data_type == "number" else int(float(raw_value))
            except Exception:
                v = raw_value
            return v, unit
        return raw_value, unit
