"""Component selector agent for replacing placeholders with real components."""
from __future__ import annotations

import asyncio
from typing import Dict, List, Any, Optional
from collections import Counter

from backend.services.component_db_service import ComponentDBService
from backend.services import odl_graph_service
from backend.services.learning_agent_service import LearningAgentService
from backend.services.placeholder_components import get_placeholder_service
from backend.utils.adpf import wrap_response
from backend.schemas.odl import ComponentCandidate, ODLNode, ODLEdge
from datetime import datetime


class ComponentSelectorAgent:
    """Agent for selecting real components to replace placeholders."""
    
    def __init__(self):
        self.component_db_service = ComponentDBService()
        self.odl_graph_service = odl_graph_service
        self.learning_agent = LearningAgentService()
        self.placeholder_service = get_placeholder_service()
    
    async def execute(self, session_id: str, tid: str, **kwargs) -> Dict:
        """Execute component selection task and return an ADPF envelope."""
        try:
        if tid != "populate_real_components":
            return wrap_response(
                thought=f"Received unknown component-selection task '{tid}'.",
                card={"title": "Component Selection", "body": f"Unknown task '{tid}'"},
                patch=None,
                status="pending",
            )
            
            graph = await self.odl_graph_service.get_graph(session_id)
            if graph is None:
                return wrap_response(
                    thought="Cannot replace placeholders because the session does not exist.",
                    card={"title": "Component Selection", "body": "Session not found"},
                    patch=None,
                    status="blocked",
                )
            
            placeholder_nodes = {
                n: d for n, d in graph.nodes(data=True) 
                if d.get("placeholder", False)
            }
            
            if not placeholder_nodes:
                return wrap_response(
                    thought="No placeholders found; component selection is unnecessary.",
                    card={
                        "title": "Component Selection",
                        "body": "No placeholder components found to replace"
                    },
                    patch=None,
                    status="complete",
                )
            
            # Group placeholders by type
            placeholders_by_type = {}
            for node_id, node_data in placeholder_nodes.items():
                component_type = node_data.get("type", "unknown")
                if component_type not in placeholders_by_type:
                    placeholders_by_type[component_type] = []
                placeholders_by_type[component_type].append((node_id, node_data))
            
            # Find candidate components for each type
            all_candidates = {}
            requirements = graph.graph.get("requirements", {})
            
            for placeholder_type, nodes in placeholders_by_type.items():
                candidates = await self._find_candidates(placeholder_type, requirements, nodes)
                all_candidates[placeholder_type] = candidates
            
            # Create selection card
            selection_result = await self._create_selection_card(session_id, placeholders_by_type, all_candidates)
            card = selection_result.get("card")
            patch = selection_result.get("patch")
            status = selection_result.get("status", "pending")
            warnings = card.get("warnings", []) if card else []
            return wrap_response(
                thought="Generated candidate replacements for placeholder components.",
                card=card,
                patch=patch,
                status=status,
                warnings=warnings or None,
            )
        
        except Exception as e:
            return wrap_response(
                thought="Encountered an exception during component selection.",
                card={
                    "title": "Component Selection",
                    "body": f"Error in component selection: {str(e)}"
                },
                patch=None,
                status="blocked",
            )
    
    async def _find_candidates(self, placeholder_type: str, requirements: Dict, placeholder_nodes: List) -> List[ComponentCandidate]:
        """Find real components that could replace the placeholder type."""
        try:
            placeholder_def = self.placeholder_service.get_placeholder_type(placeholder_type)
            if not placeholder_def:
                return []
            
            replacement_categories = placeholder_def.replacement_categories
            
            # Search component database for matching categories
            all_candidates = []
            for category in replacement_categories:
                try:
                    components = await self.component_db_service.search(category=category)
                    for comp in components:
                        candidate = ComponentCandidate(
                            part_number=comp.get("part_number", ""),
                            name=comp.get("name", "Unknown"),
                            category=category,
                            power=comp.get("power"),
                            price=comp.get("price"),
                            manufacturer=comp.get("manufacturer"),
                            efficiency=comp.get("efficiency"),
                            availability=True,  # Assume available if in database
                            metadata=comp
                        )
                        all_candidates.append(candidate)
                except Exception as e:
                    print(f"Error searching for {category}: {e}")
                    continue
            
            if not all_candidates:
                return []
            
            # Filter and rank candidates based on requirements
            filtered_candidates = self._filter_candidates(
                all_candidates, placeholder_type, requirements, placeholder_nodes
            )
            
            # Sort by suitability score
            ranked_candidates = self._rank_candidates(filtered_candidates, requirements)
            
            return ranked_candidates[:5]  # Return top 5 candidates
        
        except Exception as e:
            print(f"Error finding candidates for {placeholder_type}: {e}")
            return []
    
    def _filter_candidates(self, candidates: List[ComponentCandidate], placeholder_type: str, 
                         requirements: Dict, placeholder_nodes: List) -> List[ComponentCandidate]:
        """Filter candidates based on technical requirements."""
        try:
            filtered = []
            
            if placeholder_type == "generic_panel":
                target_power = requirements.get("target_power")
                budget = requirements.get("budget") 
                preferred_brands = requirements.get("preferred_brands", [])
                
                for comp in candidates:
                    # Power range filter (within reasonable bounds of requirement)
                    if target_power:
                        num_panels_needed = len(placeholder_nodes)
                        if num_panels_needed > 0:
                            avg_power_needed = target_power / num_panels_needed
                            comp_power = comp.power or 0
                            if not (avg_power_needed * 0.5 <= comp_power <= avg_power_needed * 2.0):
                                continue
                    
                    # Budget filter (rough component-level budget check)
                    if budget and comp.price:
                        estimated_total_cost = comp.price * len(placeholder_nodes)
                        if estimated_total_cost > budget * 0.7:  # Leave room for other components
                            continue
                    
                    # Brand preference
                    if preferred_brands and comp.manufacturer:
                        comp_brand = comp.manufacturer.lower()
                        if not any(brand.lower() in comp_brand for brand in preferred_brands):
                            comp.suitability_score -= 0.2  # Penalty for non-preferred brand
                    
                    filtered.append(comp)
            
            elif placeholder_type == "generic_inverter":
                target_power = requirements.get("target_power")
                preferred_brands = requirements.get("preferred_brands", [])
                
                for comp in candidates:
                    # Capacity should be reasonable for target power
                    comp_capacity = comp.metadata.get("capacity", comp.power or 0)
                    if target_power and comp_capacity > 0:
                        if comp_capacity < target_power * 0.8 or comp_capacity > target_power * 1.5:
                            continue
                    
                    # Brand preference
                    if preferred_brands and comp.manufacturer:
                        comp_brand = comp.manufacturer.lower()
                        if not any(brand.lower() in comp_brand for brand in preferred_brands):
                            comp.suitability_score -= 0.2
                    
                    filtered.append(comp)
            
            else:
                # For other component types, apply basic filtering
                filtered = candidates
            
            return filtered
        
        except Exception as e:
            print(f"Error filtering candidates: {e}")
            return candidates
    
    def _rank_candidates(self, candidates: List[ComponentCandidate], requirements: Dict) -> List[ComponentCandidate]:
        """Rank candidates by suitability score."""
        try:
            for comp in candidates:
                score = 0.0
                
                # Price-performance ratio
                power = comp.power or comp.metadata.get("capacity", 1)
                price = comp.price or 1000
                if power > 0 and price > 0:
                    score += (power / price) * 100  # Watts per dollar * 100
                
                # Brand preference bonus (applied in filtering)
                if comp.suitability_score >= 0:  # No brand penalty
                    score += 20
                else:
                    score += comp.suitability_score * 100  # Apply penalty
                
                # Efficiency bonus
                efficiency = comp.efficiency or comp.metadata.get("efficiency", 0.2)
                if efficiency:
                    score += efficiency * 50
                
                # Availability bonus
                if comp.availability:
                    score += 10
                
                # Manufacturer reputation (simple heuristic)
                if comp.manufacturer:
                    reputable_brands = ["sunpower", "tesla", "lg", "panasonic", "sma", "fronius", "solaredge"]
                    if any(brand in comp.manufacturer.lower() for brand in reputable_brands):
                        score += 15
                
                comp.suitability_score = max(score, 0)  # Ensure non-negative
            
            return sorted(candidates, key=lambda x: x.suitability_score, reverse=True)
        
        except Exception as e:
            print(f"Error ranking candidates: {e}")
            return candidates
    
    async def _create_selection_card(self, session_id: str, placeholders_by_type: Dict, 
                                   all_candidates: Dict) -> Dict:
        """Create interactive selection card for component choices."""
        try:
            # Create specs showing what needs to be selected
            specs = []
            total_selections_needed = 0
            for placeholder_type, nodes in placeholders_by_type.items():
                candidate_count = len(all_candidates.get(placeholder_type, []))
                display_type = placeholder_type.replace('generic_', '').replace('_', ' ').title()
                
                specs.append({
                    "label": f"{display_type}s",
                    "value": f"{len(nodes)} to replace",
                    "confidence": 1.0 if candidate_count > 0 else 0.0
                })
                specs.append({
                    "label": f"Available {display_type}s", 
                    "value": str(candidate_count),
                    "confidence": 1.0 if candidate_count > 0 else 0.0
                })
                total_selections_needed += len(nodes)
            
            # Create actions for each component type with candidates
            actions = []
            for placeholder_type, candidates in all_candidates.items():
                if candidates:
                    # Add action for top candidate
                    top_candidate = candidates[0]
                    display_type = placeholder_type.replace('generic_', '').replace('_', ' ')
                    actions.append({
                        "label": f"Use {top_candidate.name} ({display_type})",
                        "command": f"select_component_{placeholder_type}_{top_candidate.part_number}",
                        "variant": "primary",
                        "icon": "check"
                    })
                    
                    # Add action to see all options
                    actions.append({
                        "label": f"See All {display_type.title()} Options",
                        "command": f"show_alternatives_{placeholder_type}",
                        "variant": "secondary", 
                        "icon": "list"
                    })
            
            # Add general actions
            actions.extend([
                {"label": "Skip for Now", "command": "skip_component_selection", "variant": "secondary", "icon": "forward"},
                {"label": "Upload More Components", "command": "upload_components", "variant": "secondary", "icon": "upload"}
            ])
            
            # Determine overall confidence and warnings
            total_placeholder_types = len(placeholders_by_type)
            types_with_candidates = len([t for t, c in all_candidates.items() if c])
            confidence = types_with_candidates / total_placeholder_types if total_placeholder_types > 0 else 0
            
            warnings = []
            if types_with_candidates < total_placeholder_types:
                missing_types = [t.replace('generic_', '') for t, c in all_candidates.items() if not c]
                warnings.append(f"No candidates found for: {', '.join(missing_types)}")
            
            recommendations = []
            if confidence < 1.0:
                recommendations.append("Upload more component datasheets for better selection options")
            if confidence > 0:
                recommendations.append("Review suggested components and select the best fit for your requirements")
            
            # Create alternatives list
            alternatives = self._create_alternatives_list(all_candidates)
            
            enhanced_card = {
                "title": "Select Real Components",
                "body": f"Found candidates for {types_with_candidates}/{total_placeholder_types} component types. Select components to replace {total_selections_needed} placeholders.",
                "confidence": confidence,
                "specs": specs,
                "actions": actions,
                "warnings": warnings,
                "recommendations": recommendations,
                "alternatives": alternatives
            }
            
            return {
                "card": enhanced_card,
                "patch": None,  # No patch until user makes selection
                "status": "pending"
            }
        
        except Exception as e:
            return {
                "card": {
                    "title": "Component Selection",
                    "body": f"Error creating selection card: {str(e)}"
                },
                "patch": None,
                "status": "blocked"
            }
    
    def _create_alternatives_list(self, all_candidates: Dict) -> List[Dict]:
        """Create alternatives list for the design card."""
        alternatives = []
        try:
            for placeholder_type, candidates in all_candidates.items():
                display_type = placeholder_type.replace('generic_', '').replace('_', ' ')
                for i, candidate in enumerate(candidates[:3]):  # Top 3 for each type
                    power_info = ""
                    if candidate.power:
                        power_info = f"{candidate.power} W"
                    elif candidate.metadata.get("capacity"):
                        power_info = f"{candidate.metadata['capacity']} W"
                    
                    price_info = f"${candidate.price}" if candidate.price else "Price unknown"
                    
                    alternatives.append({
                        "title": f"{candidate.name} ({display_type})",
                        "description": f"{power_info}, {price_info}",
                        "confidence": min(candidate.suitability_score / 100, 1.0),
                        "command": f"select_component_{placeholder_type}_{candidate.part_number}"
                    })
            
            return alternatives
        except Exception as e:
            print(f"Error creating alternatives list: {e}")
            return []

    async def replace_placeholder(self, session_id: str, placeholder_id: str, 
                                real_component: ComponentCandidate) -> Dict:
        """Replace a specific placeholder with a real component."""
        try:
            graph = await self.odl_graph_service.get_graph(session_id)
            
            if placeholder_id not in graph.nodes:
                return {
                    "card": {
                        "title": "Component Replacement",
                        "body": f"Placeholder {placeholder_id} not found in graph"
                    },
                    "patch": None,
                    "status": "blocked"
                }
            
            placeholder_data = dict(graph.nodes[placeholder_id])
            if not placeholder_data.get("placeholder", False):
                return {
                    "card": {
                        "title": "Component Replacement",
                        "body": f"Node {placeholder_id} is not a placeholder"
                    },
                    "patch": None,
                    "status": "blocked"
                }
            
            # Create replacement node data
            old_type = placeholder_data.get("type", "unknown")
            new_type = old_type.replace("generic_", "") if old_type.startswith("generic_") else real_component.category
            
            replacement_data = {
                **placeholder_data,
                "type": new_type,
                "part_number": real_component.part_number,
                "placeholder": False,
                "replaced_from": old_type,
                "replacement_timestamp": datetime.utcnow().isoformat()
            }
            
            # Add component-specific attributes
            if real_component.power:
                replacement_data["power"] = real_component.power
            if real_component.price:
                replacement_data["price"] = real_component.price
            if real_component.manufacturer:
                replacement_data["manufacturer"] = real_component.manufacturer
            if real_component.efficiency:
                replacement_data["efficiency"] = real_component.efficiency
            
            # Add any additional metadata
            for key, value in real_component.metadata.items():
                if key not in replacement_data and not key.startswith("_"):
                    replacement_data[key] = value
            
            # Update replacement history
            history_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "from_type": old_type,
                "to_component": real_component.part_number,
                "reason": "user_selection"
            }
            replacement_history = placeholder_data.get("replacement_history", [])
            replacement_history.append(history_entry)
            replacement_data["replacement_history"] = replacement_history
            
            # Create patch to update the node
            patch = {
                "remove_nodes": [placeholder_id],
                "add_nodes": [{"id": placeholder_id, "data": replacement_data}]
            }
            
            return {
                "card": {
                    "title": "Component Replaced",
                    "body": f"Replaced {old_type} with {real_component.name}"
                },
                "patch": patch,
                "status": "complete"
            }
            
        except Exception as e:
            return {
                "card": {
                    "title": "Component Replacement",
                    "body": f"Error replacing component: {str(e)}"
                },
                "patch": None,
                "status": "blocked"
            }

    async def bulk_replace_placeholders(self, session_id: str, 
                                      replacements: Dict[str, ComponentCandidate]) -> Dict:
        """Replace multiple placeholders at once."""
        try:
            graph = await self.odl_graph_service.get_graph(session_id)

            if graph is None:
                return {
                    "card": {"title": "Bulk Replacement", "body": "Session not found"},
                    "patch": None,
                    "status": "blocked"
                }
            
            remove_nodes = []
            add_nodes = []
            replacement_count = 0
            errors = []
            
            for placeholder_id, real_component in replacements.items():
                try:
                    if placeholder_id not in graph.nodes:
                        errors.append(f"Placeholder {placeholder_id} not found")
                        continue
                    
                    placeholder_data = dict(graph.nodes[placeholder_id])
                    if not placeholder_data.get("placeholder", False):
                        errors.append(f"Node {placeholder_id} is not a placeholder")
                        continue
                    
                    # Create replacement data (similar to single replacement)
                    old_type = placeholder_data.get("type", "unknown")
                    new_type = old_type.replace("generic_", "") if old_type.startswith("generic_") else real_component.category
                    
                    replacement_data = {
                        **placeholder_data,
                        "type": new_type,
                        "part_number": real_component.part_number,
                        "placeholder": False,
                        "replaced_from": old_type,
                        "replacement_timestamp": datetime.utcnow().isoformat()
                    }
                    
                    # Add component attributes
                    if real_component.power:
                        replacement_data["power"] = real_component.power
                    if real_component.price:
                        replacement_data["price"] = real_component.price
                    if real_component.manufacturer:
                        replacement_data["manufacturer"] = real_component.manufacturer
                    
                    remove_nodes.append(placeholder_id)
                    add_nodes.append({"id": placeholder_id, "data": replacement_data})
                    replacement_count += 1
                    
                except Exception as e:
                    errors.append(f"Error replacing {placeholder_id}: {str(e)}")
            
            if replacement_count == 0:
                return {
                    "card": {
                        "title": "Bulk Replacement",
                        "body": f"No components replaced. Errors: {'; '.join(errors)}"
                    },
                    "patch": None,
                    "status": "blocked"
                }
            
            patch = {
                "remove_nodes": remove_nodes,
                "add_nodes": add_nodes
            }
            
            body = f"Successfully replaced {replacement_count} placeholder components"
            if errors:
                body += f". Errors: {'; '.join(errors)}"
            
            return {
                "card": {
                    "title": "Bulk Replacement",
                    "body": body
                },
                "patch": patch,
                "status": "complete"
            }
            
        except Exception as e:
            return {
                "card": {
                    "title": "Bulk Replacement",
                    "body": f"Error in bulk replacement: {str(e)}"
                },
                "patch": None,
                "status": "blocked"
            }
