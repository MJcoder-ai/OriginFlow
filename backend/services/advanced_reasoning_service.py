# backend/services/advanced_reasoning_service.py
"""Advanced reasoning service for enterprise-grade AI capabilities.

This service provides sophisticated reasoning capabilities including:
- Multi-step reasoning chains
- Context-aware decision making
- Advanced prompt engineering
- Reasoning validation and confidence scoring
- Chain-of-thought processing
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio

from openai import AsyncOpenAI
import numpy as np

from backend.services.ai_clients import get_openai_client
from backend.utils.logging import get_logger
from backend.utils.observability import trace_span, record_metric


logger = get_logger(__name__)


class ReasoningStrategy(Enum):
    """Different reasoning strategies available."""

    BASIC = "basic"  # Simple prompt-response
    CHAIN_OF_THOUGHT = "cot"  # Step-by-step reasoning
    TREE_OF_THOUGHT = "tot"  # Multiple reasoning paths
    REACTIVE = "reactive"  # Context-aware reasoning
    MULTI_PERSPECTIVE = "multi_perspective"  # Consider multiple viewpoints


class ReasoningDepth(Enum):
    """Depth levels for reasoning."""

    BASIC = "basic"  # Quick decisions
    STANDARD = "standard"  # Normal reasoning
    ADVANCED = "advanced"  # Detailed analysis
    EXPERT = "expert"  # Deep expertise


@dataclass
class ReasoningContext:
    """Context information for reasoning."""

    domain: str
    task_type: str
    user_intent: str
    design_context: Optional[Dict[str, Any]] = None
    historical_actions: Optional[List[Dict[str, Any]]] = None
    constraints: Optional[Dict[str, Any]] = None
    reasoning_depth: ReasoningDepth = ReasoningDepth.STANDARD
    strategy: ReasoningStrategy = ReasoningStrategy.CHAIN_OF_THOUGHT


@dataclass
class ReasoningStep:
    """Single step in a reasoning chain."""

    step_id: str
    step_type: str  # analysis, decision, validation, etc.
    thought: str
    confidence: float
    evidence: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ReasoningChain:
    """Complete reasoning process."""

    chain_id: str
    context: ReasoningContext
    steps: List[ReasoningStep] = field(default_factory=list)
    final_decision: Optional[str] = None
    confidence_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ReasoningResult:
    """Result of a reasoning process."""

    success: bool
    reasoning_chain: ReasoningChain
    actions: List[Dict[str, Any]] = field(default_factory=list)
    confidence_score: float = 0.0
    explanation: str = ""
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class AdvancedReasoningService:
    """Enterprise-grade reasoning service with multiple strategies and capabilities."""

    def __init__(self, client: Optional[AsyncOpenAI] = None):
        self.client = client or get_openai_client()
        self.logger = logging.getLogger(f"{__name__}.AdvancedReasoningService")

        # Strategy configurations
        self.strategy_configs = {
            ReasoningStrategy.BASIC: {
                "max_tokens": 512,
                "temperature": 0.3,
                "system_prompt": "Provide a direct, clear response."
            },
            ReasoningStrategy.CHAIN_OF_THOUGHT: {
                "max_tokens": 1024,
                "temperature": 0.5,
                "system_prompt": "Think step by step. Break down the problem and explain your reasoning."
            },
            ReasoningStrategy.TREE_OF_THOUGHT: {
                "max_tokens": 2048,
                "temperature": 0.7,
                "system_prompt": "Consider multiple approaches and evaluate them systematically."
            },
            ReasoningStrategy.REACTIVE: {
                "max_tokens": 1024,
                "temperature": 0.4,
                "system_prompt": "Consider the context and historical actions when making decisions."
            },
            ReasoningStrategy.MULTI_PERSPECTIVE: {
                "max_tokens": 1536,
                "temperature": 0.6,
                "system_prompt": "Consider this problem from multiple stakeholder perspectives."
            }
        }

    @trace_span("advanced_reasoning.execute")
    async def execute_reasoning(
        self,
        context: ReasoningContext,
        user_query: str
    ) -> ReasoningResult:
        """Execute advanced reasoning based on context and strategy."""

        chain_id = f"reasoning_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{context.domain}"
        chain = ReasoningChain(chain_id=chain_id, context=context)

        try:
            # Execute reasoning based on strategy
            if context.strategy == ReasoningStrategy.CHAIN_OF_THOUGHT:
                result = await self._chain_of_thought_reasoning(chain, user_query)
            elif context.strategy == ReasoningStrategy.TREE_OF_THOUGHT:
                result = await self._tree_of_thought_reasoning(chain, user_query)
            elif context.strategy == ReasoningStrategy.REACTIVE:
                result = await self._reactive_reasoning(chain, user_query)
            elif context.strategy == ReasoningStrategy.MULTI_PERSPECTIVE:
                result = await self._multi_perspective_reasoning(chain, user_query)
            else:
                result = await self._basic_reasoning(chain, user_query)

            # Calculate final confidence
            final_confidence = self._calculate_final_confidence(chain)
            result.confidence_score = final_confidence
            chain.confidence_score = final_confidence

            return result

        except Exception as e:
            self.logger.error(f"Reasoning execution failed: {e}", exc_info=True)
            return ReasoningResult(
                success=False,
                reasoning_chain=chain,
                errors=[str(e)],
                explanation=f"Reasoning failed: {str(e)}"
            )

    async def _chain_of_thought_reasoning(
        self,
        chain: ReasoningChain,
        user_query: str
    ) -> ReasoningResult:
        """Implement chain-of-thought reasoning."""

        config = self.strategy_configs[ReasoningStrategy.CHAIN_OF_THOUGHT]

        # Step 1: Analyze the problem
        analysis_step = await self._execute_reasoning_step(
            chain_id=chain.chain_id,
            step_type="analysis",
            prompt=f"Analyze this engineering design request: {user_query}\n\nContext: {chain.context.domain} domain",
            config=config
        )
        chain.steps.append(analysis_step)

        # Step 2: Consider constraints and requirements
        constraints_step = await self._execute_reasoning_step(
            chain_id=chain.chain_id,
            step_type="constraints",
            prompt=f"Given the analysis above, what constraints and requirements should be considered?\n\nUser request: {user_query}",
            config=config
        )
        chain.steps.append(constraints_step)

        # Step 3: Generate solution approach
        solution_step = await self._execute_reasoning_step(
            chain_id=chain.chain_id,
            step_type="solution",
            prompt=f"Based on the analysis and constraints, what is the best approach to solve this?\n\nUser request: {user_query}",
            config=config
        )
        chain.steps.append(solution_step)

        # Step 4: Validate the approach
        validation_step = await self._execute_reasoning_step(
            chain_id=chain.chain_id,
            step_type="validation",
            prompt=f"Validate the proposed solution approach:\n\nApproach: {solution_step.thought}\n\nIs this technically sound and appropriate for the requirements?",
            config=config
        )
        chain.steps.append(validation_step)

        # Generate final actions based on reasoning
        actions = await self._convert_reasoning_to_actions(chain, user_query)

        return ReasoningResult(
            success=True,
            reasoning_chain=chain,
            actions=actions,
            explanation=self._generate_explanation(chain)
        )

    async def _tree_of_thought_reasoning(
        self,
        chain: ReasoningChain,
        user_query: str
    ) -> ReasoningResult:
        """Implement tree-of-thought reasoning with multiple paths."""

        config = self.strategy_configs[ReasoningStrategy.TREE_OF_THOUGHT]

        # Generate multiple solution approaches
        approaches = []
        for i in range(3):  # Consider 3 different approaches
            approach_step = await self._execute_reasoning_step(
                chain_id=chain.chain_id,
                step_type=f"approach_{i+1}",
                prompt=f"Generate approach {i+1} for solving: {user_query}\n\nConsider different technical strategies and methodologies.",
                config=config
            )
            approaches.append(approach_step)
            chain.steps.append(approach_step)

        # Evaluate each approach
        evaluations = []
        for i, approach in enumerate(approaches):
            eval_step = await self._execute_reasoning_step(
                chain_id=chain.chain_id,
                step_type=f"evaluation_{i+1}",
                prompt=f"Evaluate approach {i+1}: {approach.thought}\n\nPros, cons, feasibility, and alignment with requirements.",
                config=config
            )
            evaluations.append(eval_step)
            chain.steps.append(eval_step)

        # Select best approach
        selection_step = await self._execute_reasoning_step(
            chain_id=chain.chain_id,
            step_type="selection",
            prompt=f"Select the best approach from the following:\n\n" +
                   "\n".join([f"Approach {i+1}: {a.thought}" for i, a in enumerate(approaches)]) +
                   f"\n\nEvaluations:\n" +
                   "\n".join([f"Evaluation {i+1}: {e.thought}" for i, e in enumerate(evaluations)]) +
                   f"\n\nWhich approach is best for: {user_query}",
            config=config
        )
        chain.steps.append(selection_step)

        # Generate actions based on selected approach
        actions = await self._convert_reasoning_to_actions(chain, user_query)

        return ReasoningResult(
            success=True,
            reasoning_chain=chain,
            actions=actions,
            explanation=self._generate_explanation(chain)
        )

    async def _reactive_reasoning(
        self,
        chain: ReasoningChain,
        user_query: str
    ) -> ReasoningResult:
        """Implement context-aware reactive reasoning."""

        config = self.strategy_configs[ReasoningStrategy.REACTIVE]

        # Analyze historical context
        if chain.context.historical_actions:
            context_step = await self._execute_reasoning_step(
                chain_id=chain.chain_id,
                step_type="context_analysis",
                prompt=f"Analyze historical actions and their relevance to current request:\n\n"
                       f"Historical actions: {json.dumps(chain.context.historical_actions[-5:], indent=2)}\n\n"
                       f"Current request: {user_query}",
                config=config
            )
            chain.steps.append(context_step)

        # Consider current design state
        if chain.context.design_context:
            design_step = await self._execute_reasoning_step(
                chain_id=chain.chain_id,
                step_type="design_analysis",
                prompt=f"Analyze current design state and its impact on the request:\n\n"
                       f"Design context: {json.dumps(chain.context.design_context, indent=2)}\n\n"
                       f"Current request: {user_query}",
                config=config
            )
            chain.steps.append(design_step)

        # Generate context-aware solution
        solution_step = await self._execute_reasoning_step(
            chain_id=chain.chain_id,
            step_type="context_solution",
            prompt=f"Based on the context analysis, provide a solution that considers:\n"
                   f"- Historical patterns\n"
                   f"- Current design state\n"
                   f"- User requirements\n\n"
                   f"Request: {user_query}",
            config=config
        )
        chain.steps.append(solution_step)

        actions = await self._convert_reasoning_to_actions(chain, user_query)

        return ReasoningResult(
            success=True,
            reasoning_chain=chain,
            actions=actions,
            explanation=self._generate_explanation(chain)
        )

    async def _multi_perspective_reasoning(
        self,
        chain: ReasoningChain,
        user_query: str
    ) -> ReasoningResult:
        """Implement multi-perspective reasoning."""

        config = self.strategy_configs[ReasoningStrategy.MULTI_PERSPECTIVE]

        perspectives = ["technical", "business", "user_experience", "operational"]

        perspective_analyses = []

        for perspective in perspectives:
            perspective_step = await self._execute_reasoning_step(
                chain_id=chain.chain_id,
                step_type=f"{perspective}_analysis",
                prompt=f"Analyze the request from a {perspective} perspective:\n\n"
                       f"Request: {user_query}\n\n"
                       f"Consider {perspective} implications, requirements, and constraints.",
                config=config
            )
            perspective_analyses.append(perspective_step)
            chain.steps.append(perspective_step)

        # Synthesize perspectives
        synthesis_step = await self._execute_reasoning_step(
            chain_id=chain.chain_id,
            step_type="synthesis",
            prompt=f"Synthesize the following perspective analyses into a comprehensive solution:\n\n" +
                   "\n".join([f"{p.step_type}: {p.thought}" for p in perspective_analyses]) +
                   f"\n\nOriginal request: {user_query}",
            config=config
        )
        chain.steps.append(synthesis_step)

        actions = await self._convert_reasoning_to_actions(chain, user_query)

        return ReasoningResult(
            success=True,
            reasoning_chain=chain,
            actions=actions,
            explanation=self._generate_explanation(chain)
        )

    async def _basic_reasoning(
        self,
        chain: ReasoningChain,
        user_query: str
    ) -> ReasoningResult:
        """Implement basic direct reasoning."""

        config = self.strategy_configs[ReasoningStrategy.BASIC]

        basic_step = await self._execute_reasoning_step(
            chain_id=chain.chain_id,
            step_type="basic_solution",
            prompt=f"Provide a direct solution for: {user_query}",
            config=config
        )
        chain.steps.append(basic_step)

        actions = await self._convert_reasoning_to_actions(chain, user_query)

        return ReasoningResult(
            success=True,
            reasoning_chain=chain,
            actions=actions,
            explanation=basic_step.thought
        )

    async def _execute_reasoning_step(
        self,
        chain_id: str,
        step_type: str,
        prompt: str,
        config: Dict[str, Any]
    ) -> ReasoningStep:
        """Execute a single reasoning step with LLM."""

        try:
            messages = [
                {"role": "system", "content": config["system_prompt"]},
                {"role": "user", "content": prompt}
            ]

            response = await self.client.chat.completions.create(
                model="gpt-4o",  # Use most capable model for reasoning
                messages=messages,
                max_tokens=config["max_tokens"],
                temperature=config["temperature"]
            )

            thought = response.choices[0].message.content or ""
            confidence = self._estimate_confidence(thought)

            return ReasoningStep(
                step_id=f"{chain_id}_{step_type}",
                step_type=step_type,
                thought=thought,
                confidence=confidence
            )

        except Exception as e:
            self.logger.error(f"Reasoning step failed: {e}")
            return ReasoningStep(
                step_id=f"{chain_id}_{step_type}_error",
                step_type=step_type,
                thought=f"Error during reasoning: {str(e)}",
                confidence=0.1
            )

    def _estimate_confidence(self, thought: str) -> float:
        """Estimate confidence score based on reasoning quality."""

        if not thought or len(thought) < 10:
            return 0.1

        confidence_indicators = [
            "definitely", "certainly", "absolutely", "clearly",
            "obviously", "undoubtedly", "without doubt"
        ]

        hesitation_indicators = [
            "maybe", "perhaps", "possibly", "might", "could",
            "uncertain", "unclear", "not sure"
        ]

        confidence_score = 0.5  # Base confidence

        # Check for confidence indicators
        thought_lower = thought.lower()
        for indicator in confidence_indicators:
            if indicator in thought_lower:
                confidence_score += 0.1

        # Check for hesitation indicators
        for indicator in hesitation_indicators:
            if indicator in thought_lower:
                confidence_score -= 0.1

        # Length and detail bonus
        if len(thought) > 200:
            confidence_score += 0.1

        # Reasoning structure bonus
        if "because" in thought_lower or "therefore" in thought_lower:
            confidence_score += 0.1

        return max(0.0, min(1.0, confidence_score))

    def _calculate_final_confidence(self, chain: ReasoningChain) -> float:
        """Calculate overall confidence from reasoning chain."""

        if not chain.steps:
            return 0.5

        # Weight recent steps more heavily
        weights = np.linspace(0.5, 1.0, len(chain.steps))
        confidences = [step.confidence for step in chain.steps]

        # Weighted average
        weighted_confidence = np.average(confidences, weights=weights)

        # Adjust based on number of steps (more steps = more thorough)
        step_bonus = min(0.1, len(chain.steps) * 0.02)

        return min(1.0, weighted_confidence + step_bonus)

    async def _convert_reasoning_to_actions(
        self,
        chain: ReasoningChain,
        user_query: str
    ) -> List[Dict[str, Any]]:
        """Convert reasoning chain into actionable items."""

        # This is a simplified implementation
        # In practice, this would use more sophisticated action generation

        final_thought = chain.steps[-1].thought if chain.steps else ""

        # Basic action extraction based on reasoning
        actions = []

        if "design" in user_query.lower() or "create" in user_query.lower():
            actions.append({
                "action": "add_component",
                "payload": {
                    "name": f"Generated from reasoning: {final_thought[:50]}...",
                    "type": "design_element"
                },
                "confidence": chain.confidence_score,
                "reasoning": chain.chain_id
            })

        if "analyze" in user_query.lower() or "validate" in user_query.lower():
            actions.append({
                "action": "report",
                "payload": {
                    "message": f"Analysis: {final_thought[:200]}..."
                },
                "confidence": chain.confidence_score,
                "reasoning": chain.chain_id
            })

        return actions

    def _generate_explanation(self, chain: ReasoningChain) -> str:
        """Generate human-readable explanation of reasoning process."""

        if not chain.steps:
            return "No reasoning steps available."

        explanation_parts = [
            f"Reasoning Process ({len(chain.steps)} steps):",
            ""
        ]

        for i, step in enumerate(chain.steps, 1):
            explanation_parts.extend([
                f"Step {i}: {step.step_type.title()}",
                f"Thought: {step.thought[:100]}..." if len(step.thought) > 100 else f"Thought: {step.thought}",
                f"Confidence: {step.confidence:.2f}",
                ""
            ])

        explanation_parts.extend([
            f"Final Decision: {chain.final_decision or 'No explicit decision'}",
            f"Overall Confidence: {chain.confidence_score:.2f}"
        ])

        return "\n".join(explanation_parts)

    # Public interface methods
    async def reason_about_design(
        self,
        user_query: str,
        domain: str = "general",
        reasoning_depth: ReasoningDepth = ReasoningDepth.STANDARD,
        strategy: ReasoningStrategy = ReasoningStrategy.CHAIN_OF_THOUGHT
    ) -> ReasoningResult:
        """High-level method for design-related reasoning."""

        context = ReasoningContext(
            domain=domain,
            task_type="design",
            user_intent=user_query,
            reasoning_depth=reasoning_depth,
            strategy=strategy
        )

        return await self.execute_reasoning(context, user_query)

    async def validate_reasoning_chain(
        self,
        chain: ReasoningChain
    ) -> Tuple[bool, List[str]]:
        """Validate a reasoning chain for consistency and logic."""

        errors = []

        if not chain.steps:
            errors.append("Empty reasoning chain")
            return False, errors

        # Check for logical consistency
        confidences = [step.confidence for step in chain.steps]
        if max(confidences) - min(confidences) > 0.8:
            errors.append("High confidence variance indicates inconsistent reasoning")

        # Check for minimum reasoning depth
        if len(chain.steps) < 2:
            errors.append("Insufficient reasoning depth")

        return len(errors) == 0, errors


# Global instance for easy access
_advanced_reasoning_service: Optional[AdvancedReasoningService] = None


def get_advanced_reasoning_service() -> AdvancedReasoningService:
    """Get or create the global advanced reasoning service instance."""
    global _advanced_reasoning_service
    if _advanced_reasoning_service is None:
        _advanced_reasoning_service = AdvancedReasoningService()
    return _advanced_reasoning_service
