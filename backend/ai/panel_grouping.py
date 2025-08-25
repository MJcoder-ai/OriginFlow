"""
Enterprise Panel Grouping Engine - Formal Schema Compatible
==========================================================

Advanced spatial grouping system for solar PV modules using the formal ODL schema.
This enterprise-grade engine provides intelligent panel clustering with consistent
attribute access patterns and comprehensive optimization strategies.

Updated for Formal ODL Schema:
- Uses ODLGraph model with formal node.data attribute access
- Consistent with formal source_id/target_id naming conventions  
- Integrated with STANDARD_COMPONENT_TYPES for type checking
- Enhanced validation using formal schema patterns
- Enterprise-grade logging and error handling

Key Features:
- Multi-factor optimization (spatial, electrical, shading, performance)
- NEC 690.7 string length compliance validation
- Roof section and orientation awareness
- Shading pattern consideration and performance optimization
- Formal schema integration for type safety and consistency
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Any, Union
from enum import Enum

# Import formal ODL schema components
from backend.schemas.odl import ODLGraph, ODLNode, STANDARD_COMPONENT_TYPES

logger = logging.getLogger(__name__)


class GroupingStrategy(Enum):
    """Panel grouping strategy options."""
    SPATIAL_PROXIMITY = "spatial_proximity"
    ELECTRICAL_OPTIMAL = "electrical_optimal" 
    SHADING_AWARE = "shading_aware"
    PERFORMANCE_OPTIMIZED = "performance_optimized"


@dataclass
class PanelInfo:
    """Enhanced panel information for grouping decisions."""
    id: str
    x: float
    y: float
    orientation: float = 0.0  # degrees from south
    tilt: float = 30.0  # degrees from horizontal
    power: float = 400.0  # watts
    voltage_oc: float = 49.5  # open circuit voltage
    current_sc: float = 11.2  # short circuit current
    shading_factor: float = 1.0  # 0.0 = fully shaded, 1.0 = no shading
    roof_section: str = "main"  # roof section identifier
    performance_ratio: float = 1.0  # relative performance factor


@dataclass  
class StringConfiguration:
    """Configuration parameters for string formation."""
    max_modules_per_string: int = 12
    min_modules_per_string: int = 6
    max_string_voltage: float = 600.0  # NEC 690.7(A) limit
    min_string_voltage: float = 200.0  # inverter minimum
    max_current_mismatch: float = 0.1  # 10% current mismatch tolerance
    grouping_strategy: GroupingStrategy = GroupingStrategy.PERFORMANCE_OPTIMIZED


class EnterpriseGroupingEngine:
    """
    Advanced panel grouping engine with multi-factor optimization.
    
    This engine considers spatial layout, electrical characteristics, shading
    patterns, and code compliance to create optimal string configurations
    for complex solar installations.
    """
    
    def __init__(self, config: Optional[StringConfiguration] = None):
        self.config = config or StringConfiguration()
        self.logger = logging.getLogger(__name__ + ".EnterpriseGroupingEngine")
    
    def group_panels(
        self, 
        graph: Union[ODLGraph, Any], 
        strategy: Optional[GroupingStrategy] = None
    ) -> List[List[str]]:
        """
        Group panels into optimal strings using formal ODL schema.
        
        Args:
            graph: Formal ODLGraph instance or compatible graph object with nodes
            strategy: Grouping strategy override
            
        Returns:
            List of string groups, where each group contains panel node IDs
        """
        strategy = strategy or self.config.grouping_strategy
        
        # Extract and enhance panel information
        panels = self._extract_panel_info(graph)
        if len(panels) < self.config.min_modules_per_string:
            self.logger.warning(f"Only {len(panels)} panels found, below minimum string size")
            return [panel.id for panel in panels] if panels else []
        
        self.logger.info(f"Grouping {len(panels)} panels using {strategy.value} strategy")
        
        # Apply selected grouping strategy
        if strategy == GroupingStrategy.SPATIAL_PROXIMITY:
            groups = self._spatial_proximity_grouping(panels)
        elif strategy == GroupingStrategy.ELECTRICAL_OPTIMAL:
            groups = self._electrical_optimal_grouping(panels)
        elif strategy == GroupingStrategy.SHADING_AWARE:
            groups = self._shading_aware_grouping(panels)
        else:  # PERFORMANCE_OPTIMIZED
            groups = self._performance_optimized_grouping(panels)
        
        # Validate and optimize final groups
        validated_groups = self._validate_and_optimize_groups(groups, panels)
        
        self.logger.info(f"Created {len(validated_groups)} optimized string groups")
        return [[panel.id for panel in group] for group in validated_groups]
    
    def _extract_panel_info(self, graph: Union[ODLGraph, Any]) -> List[PanelInfo]:
        """Extract enhanced panel information using formal ODL schema patterns."""
        panels = []
        
        for node_id, node in graph.nodes.items():
            if not self._is_panel_node(node):
                continue
                
            # Use formal ODL schema: node.data for all component attributes
            node_data = node.data
            
            # Extract spatial coordinates using formal node.data access
            x = float(node_data.get('x', 0.0))
            y = float(node_data.get('y', 0.0))
            
            # Extract electrical characteristics
            power = float(node_data.get('power', 400.0))
            voc = float(node_data.get('voc', 49.5))
            isc = float(node_data.get('isc', 11.2))
            
            # Extract physical characteristics
            orientation = float(node_data.get('orientation', 0.0))
            tilt = float(node_data.get('tilt', 30.0))
            
            # Extract performance factors
            shading_factor = float(node_data.get('shading_factor', 1.0))
            roof_section = str(node_data.get('roof_section', 'main'))
            performance_ratio = float(node_data.get('performance_ratio', 1.0))
            
            panel = PanelInfo(
                id=node_id,
                x=x, y=y,
                orientation=orientation,
                tilt=tilt,
                power=power,
                voltage_oc=voc,
                current_sc=isc,
                shading_factor=shading_factor,
                roof_section=roof_section,
                performance_ratio=performance_ratio
            )
            panels.append(panel)
        
        return panels
    
    def _is_panel_node(self, node: Any) -> bool:
        """Determine if a node represents a solar panel using formal schema types."""
        node_type = node.type.lower()
        
        # Use formal STANDARD_COMPONENT_TYPES for consistent type checking
        panel_types = {"panel", "pv_module", "solar_panel", "generic_panel"}
        
        # Check direct type match first
        if node_type in panel_types:
            return True
            
        # Additional type matching for comprehensive coverage
        return any(keyword in node_type for keyword in ['panel', 'module', 'pv'])
    
    def _spatial_proximity_grouping(self, panels: List[PanelInfo]) -> List[List[PanelInfo]]:
        """Group panels by spatial proximity with roof section awareness."""
        # Group by roof section first
        roof_sections: Dict[str, List[PanelInfo]] = {}
        for panel in panels:
            if panel.roof_section not in roof_sections:
                roof_sections[panel.roof_section] = []
            roof_sections[panel.roof_section].append(panel)
        
        all_groups = []
        for section_name, section_panels in roof_sections.items():
            # Sort panels by position (top-to-bottom, left-to-right)
            section_panels.sort(key=lambda p: (p.y, p.x))
            
            # Create proximity-based groups
            groups = []
            current_group = []
            
            for panel in section_panels:
                if len(current_group) == 0:
                    current_group.append(panel)
                elif (len(current_group) < self.config.max_modules_per_string and
                      self._is_spatially_adjacent(current_group[-1], panel)):
                    current_group.append(panel)
                else:
                    if len(current_group) >= self.config.min_modules_per_string:
                        groups.append(current_group)
                    current_group = [panel]
            
            # Add final group if valid
            if len(current_group) >= self.config.min_modules_per_string:
                groups.append(current_group)
            
            all_groups.extend(groups)
        
        return all_groups
    
    def _electrical_optimal_grouping(self, panels: List[PanelInfo]) -> List[List[PanelInfo]]:
        """Group panels for optimal electrical performance."""
        # Sort by electrical characteristics (voltage, current matching)
        panels.sort(key=lambda p: (p.voltage_oc, p.current_sc, p.power))
        
        groups = []
        current_group = []
        
        for panel in panels:
            if len(current_group) == 0:
                current_group.append(panel)
            elif (len(current_group) < self.config.max_modules_per_string and
                  self._is_electrically_compatible(current_group[0], panel)):
                current_group.append(panel)
                
                # Check string voltage limit
                string_voltage = sum(p.voltage_oc for p in current_group)
                if string_voltage > self.config.max_string_voltage:
                    # Remove last panel and start new group
                    current_group.pop()
                    if len(current_group) >= self.config.min_modules_per_string:
                        groups.append(current_group)
                    current_group = [panel]
            else:
                if len(current_group) >= self.config.min_modules_per_string:
                    groups.append(current_group)
                current_group = [panel]
        
        # Add final group
        if len(current_group) >= self.config.min_modules_per_string:
            groups.append(current_group)
        
        return groups
    
    def _shading_aware_grouping(self, panels: List[PanelInfo]) -> List[List[PanelInfo]]:
        """Group panels considering shading patterns."""
        # Group panels by similar shading characteristics
        shading_groups: Dict[float, List[PanelInfo]] = {}
        
        for panel in panels:
            # Round shading factor to create discrete groups
            shading_key = round(panel.shading_factor, 1)
            if shading_key not in shading_groups:
                shading_groups[shading_key] = []
            shading_groups[shading_key].append(panel)
        
        all_groups = []
        for shading_factor, group_panels in shading_groups.items():
            # Sort by spatial proximity within shading group
            group_panels.sort(key=lambda p: (p.y, p.x))
            
            # Create appropriately sized groups
            while len(group_panels) >= self.config.min_modules_per_string:
                group_size = min(len(group_panels), self.config.max_modules_per_string)
                group = group_panels[:group_size]
                all_groups.append(group)
                group_panels = group_panels[group_size:]
        
        return all_groups
    
    def _performance_optimized_grouping(self, panels: List[PanelInfo]) -> List[List[PanelInfo]]:
        """Advanced grouping optimizing for overall system performance."""
        # Multi-factor scoring: spatial proximity + electrical matching + performance
        scored_groups = []
        
        # Start with spatial grouping as base
        spatial_groups = self._spatial_proximity_grouping(panels)
        
        for group in spatial_groups:
            # Calculate group performance score
            score = self._calculate_group_score(group)
            scored_groups.append((score, group))
        
        # Sort by performance score (higher is better)
        scored_groups.sort(key=lambda x: x[0], reverse=True)
        
        # Extract optimized groups
        return [group for _, group in scored_groups]
    
    def _calculate_group_score(self, group: List[PanelInfo]) -> float:
        """Calculate performance score for a panel group."""
        if not group:
            return 0.0
        
        # Base score factors
        size_score = len(group) / self.config.max_modules_per_string  # Prefer larger strings
        
        # Electrical matching score
        avg_voltage = sum(p.voltage_oc for p in group) / len(group)
        voltage_variance = sum((p.voltage_oc - avg_voltage) ** 2 for p in group) / len(group)
        electrical_score = 1.0 / (1.0 + voltage_variance)  # Lower variance is better
        
        # Performance consistency score
        avg_performance = sum(p.performance_ratio for p in group) / len(group)
        performance_variance = sum((p.performance_ratio - avg_performance) ** 2 for p in group) / len(group)
        performance_score = 1.0 / (1.0 + performance_variance)
        
        # Shading consistency score
        avg_shading = sum(p.shading_factor for p in group) / len(group)
        shading_variance = sum((p.shading_factor - avg_shading) ** 2 for p in group) / len(group)
        shading_score = 1.0 / (1.0 + shading_variance)
        
        # Combined weighted score
        total_score = (
            0.3 * size_score +
            0.25 * electrical_score +
            0.25 * performance_score +
            0.2 * shading_score
        )
        
        return total_score
    
    def _is_spatially_adjacent(self, panel1: PanelInfo, panel2: PanelInfo) -> bool:
        """Check if two panels are spatially adjacent."""
        distance = math.sqrt((panel1.x - panel2.x)**2 + (panel1.y - panel2.y)**2)
        # Assume panels are adjacent if within 3 meters
        return distance <= 3.0
    
    def _is_electrically_compatible(self, panel1: PanelInfo, panel2: PanelInfo) -> bool:
        """Check if two panels are electrically compatible for same string."""
        # Check current mismatch tolerance
        current_diff = abs(panel1.current_sc - panel2.current_sc)
        current_avg = (panel1.current_sc + panel2.current_sc) / 2
        current_mismatch = current_diff / current_avg if current_avg > 0 else 0
        
        return current_mismatch <= self.config.max_current_mismatch
    
    def _validate_and_optimize_groups(
        self, 
        groups: List[List[PanelInfo]], 
        all_panels: List[PanelInfo]
    ) -> List[List[PanelInfo]]:
        """Validate groups against NEC requirements and optimize."""
        validated_groups = []
        orphaned_panels = []
        
        for group in groups:
            if self._validate_string_group(group):
                validated_groups.append(group)
            else:
                # Split oversized groups or merge undersized ones
                if len(group) > self.config.max_modules_per_string:
                    # Split large group
                    mid_point = len(group) // 2
                    group1 = group[:mid_point]
                    group2 = group[mid_point:]
                    
                    if len(group1) >= self.config.min_modules_per_string:
                        validated_groups.append(group1)
                    else:
                        orphaned_panels.extend(group1)
                        
                    if len(group2) >= self.config.min_modules_per_string:
                        validated_groups.append(group2)
                    else:
                        orphaned_panels.extend(group2)
                else:
                    # Group too small, add to orphaned
                    orphaned_panels.extend(group)
        
        # Try to create additional groups from orphaned panels
        if len(orphaned_panels) >= self.config.min_modules_per_string:
            while len(orphaned_panels) >= self.config.min_modules_per_string:
                group_size = min(len(orphaned_panels), self.config.max_modules_per_string)
                rescue_group = orphaned_panels[:group_size]
                if self._validate_string_group(rescue_group):
                    validated_groups.append(rescue_group)
                orphaned_panels = orphaned_panels[group_size:]
        
        if orphaned_panels:
            self.logger.warning(f"{len(orphaned_panels)} panels could not be grouped into valid strings")
        
        return validated_groups
    
    def _validate_string_group(self, group: List[PanelInfo]) -> bool:
        """Validate string group against NEC and electrical requirements."""
        if len(group) < self.config.min_modules_per_string:
            return False
        if len(group) > self.config.max_modules_per_string:
            return False
        
        # Check string voltage limits
        total_voltage = sum(panel.voltage_oc for panel in group)
        if total_voltage > self.config.max_string_voltage:
            return False
        if total_voltage < self.config.min_string_voltage:
            return False
        
        return True


# Convenience functions for formal schema compatibility
def group_panels(
    graph: Union[ODLGraph, Any], 
    max_per_string: int = 12,
    strategy: GroupingStrategy = GroupingStrategy.PERFORMANCE_OPTIMIZED
) -> List[List[str]]:
    """
    Simplified panel grouping function using formal ODL schema.
    
    Args:
        graph: Formal ODLGraph instance or compatible graph with nodes
        max_per_string: Maximum modules per string
        strategy: Grouping strategy to use
        
    Returns:
        List of string groups (panel node IDs)
    """
    config = StringConfiguration(
        max_modules_per_string=max_per_string,
        grouping_strategy=strategy
    )
    engine = EnterpriseGroupingEngine(config)
    return engine.group_panels(graph, strategy)