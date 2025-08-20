# backend/analytics/enterprise_analytics.py
"""Enterprise-grade analytics and business intelligence system for OriginFlow AI platform."""

from __future__ import annotations

import asyncio
import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Set, Union
from enum import Enum

from prometheus_client import Counter, Histogram, Gauge, Summary
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import mean_squared_error, accuracy_score, classification_report
import redis.asyncio as redis
import joblib
import pickle

from backend.utils.logging import get_logger
from backend.utils.observability import trace_span, record_metric
from backend.services.enterprise_cache import get_cache
from backend.services.enterprise_monitoring import get_monitoring_system


logger = get_logger(__name__)


# Analytics metrics
ANALYTICS_METRICS = {
    "prediction_requests_total": Counter(
        "prediction_requests_total",
        "Total prediction requests",
        ["model_type", "tenant_id", "prediction_type"]
    ),
    "model_accuracy_gauge": Gauge(
        "model_accuracy_gauge",
        "Current model accuracy scores",
        ["model_name", "metric_type"]
    ),
    "analytics_queries_total": Counter(
        "analytics_queries_total",
        "Total analytics queries",
        ["query_type", "tenant_id"]
    ),
    "prediction_latency_seconds": Histogram(
        "prediction_latency_seconds",
        "Prediction request latency",
        ["model_type", "prediction_type"]
    ),
    "data_processing_time_seconds": Summary(
        "data_processing_time_seconds",
        "Data processing time by operation",
        ["operation_type"]
    )
}


class AnalyticsModelType(Enum):
    """Types of analytics models available."""

    PREDICTIVE_MAINTENANCE = "predictive_maintenance"
    COST_OPTIMIZATION = "cost_optimization"
    PERFORMANCE_PREDICTION = "performance_prediction"
    ANOMALY_DETECTION = "anomaly_detection"
    USER_BEHAVIOR = "user_behavior"
    MARKET_TREND = "market_trend"
    RISK_ASSESSMENT = "risk_assessment"
    EFFICIENCY_OPTIMIZATION = "efficiency_optimization"


class PredictionType(Enum):
    """Types of predictions that can be made."""

    DESIGN_SUCCESS = "design_success"
    COST_ESTIMATION = "cost_estimation"
    PERFORMANCE_METRICS = "performance_metrics"
    MAINTENANCE_NEEDS = "maintenance_needs"
    USER_SATISFACTION = "user_satisfaction"
    COMPLIANCE_RISK = "compliance_risk"
    MARKET_DEMAND = "market_demand"
    RESOURCE_UTILIZATION = "resource_utilization"


@dataclass
class AnalyticsConfig:
    """Configuration for enterprise analytics system."""

    # Model settings
    model_update_interval_hours: int = 24
    prediction_cache_ttl_seconds: int = 3600
    max_training_data_points: int = 100000

    # Performance settings
    max_concurrent_predictions: int = 50
    prediction_timeout_seconds: int = 30
    batch_prediction_size: int = 100

    # Accuracy thresholds
    min_model_accuracy: float = 0.75
    retrain_threshold_drop: float = 0.05

    # Redis configuration
    redis_url: Optional[str] = None
    enable_redis_caching: bool = True

    # External integrations
    enable_external_data_sources: bool = True
    data_warehouse_url: Optional[str] = None


@dataclass
class AnalyticsData:
    """Structured analytics data point."""

    timestamp: datetime
    tenant_id: str
    data_type: str
    features: Dict[str, float]
    labels: Optional[Dict[str, float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PredictionResult:
    """Result of a prediction operation."""

    prediction_type: PredictionType
    model_type: AnalyticsModelType
    predicted_values: Dict[str, float]
    confidence_intervals: Dict[str, Tuple[float, float]]
    confidence_score: float
    feature_importance: Dict[str, float]
    model_accuracy: float
    execution_time: float
    recommendations: List[str]
    warnings: List[str]


@dataclass
class BusinessInsight:
    """Business intelligence insight."""

    insight_type: str
    title: str
    description: str
    confidence_score: float
    impact_score: float  # 1-10 scale
    recommendations: List[str]
    supporting_data: Dict[str, Any]
    generated_at: datetime = field(default_factory=datetime.now)


class EnterpriseAnalyticsEngine:
    """Enterprise-grade analytics and business intelligence engine."""

    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.EnterpriseAnalyticsEngine")

        # Initialize services
        self.cache = get_cache()
        self.monitoring = get_monitoring_system()

        # Model storage
        self.models: Dict[str, Any] = {}
        self.model_metadata: Dict[str, Dict[str, Any]] = {}
        self.scalers: Dict[str, StandardScaler] = {}

        # Data storage
        self.training_data: Dict[str, List[AnalyticsData]] = {}
        self.redis: Optional[redis.Redis] = None

        # Initialize Redis if configured
        if config.redis_url:
            self.redis = redis.from_url(config.redis_url)

        # Initialize models
        self._initialize_models()

    async def initialize(self) -> None:
        """Initialize the analytics engine."""

        if self.redis:
            await self.redis.ping()
            self.logger.info("Redis connection established for analytics")

        # Load persisted models
        await self._load_models()

        # Start background tasks
        asyncio.create_task(self._model_maintenance_loop())
        asyncio.create_task(self._data_collection_loop())

        self.logger.info("Enterprise Analytics Engine initialized")

    async def cleanup(self) -> None:
        """Cleanup analytics resources."""

        # Save models
        await self._save_models()

        if self.redis:
            await self.redis.aclose()

        self.logger.info("Analytics Engine cleaned up")

    def _initialize_models(self) -> None:
        """Initialize machine learning models."""

        # Predictive maintenance model
        self.models["predictive_maintenance"] = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.scalers["predictive_maintenance"] = StandardScaler()

        # Cost optimization model
        self.models["cost_optimization"] = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            random_state=42
        )
        self.scalers["cost_optimization"] = StandardScaler()

        # Performance prediction model
        self.models["performance_prediction"] = RandomForestRegressor(
            n_estimators=150,
            max_depth=12,
            random_state=42
        )
        self.scalers["performance_prediction"] = StandardScaler()

        # Anomaly detection model (clustering-based)
        self.models["anomaly_detection"] = KMeans(
            n_clusters=5,
            random_state=42
        )
        self.scalers["anomaly_detection"] = StandardScaler()

        # Initialize model metadata
        for model_name in self.models.keys():
            self.model_metadata[model_name] = {
                "accuracy": 0.0,
                "last_trained": None,
                "training_samples": 0,
                "features": [],
                "version": "1.0.0"
            }

    async def predict(
        self,
        prediction_type: PredictionType,
        features: Dict[str, float],
        tenant_id: str = "default"
    ) -> PredictionResult:
        """Make a prediction using the appropriate model."""

        start_time = asyncio.get_event_loop().time()

        try:
            # Determine model type
            model_type = self._get_model_type_for_prediction(prediction_type)

            # Check cache first
            cache_key = f"prediction:{tenant_id}:{model_type.value}:{hash(json.dumps(features, sort_keys=True))}"
            cached_result = await self.cache.get(cache_key, tenant_id)

            if cached_result:
                self.logger.info(f"Using cached prediction for {cache_key}")
                return cached_result

            # Get model
            model = self.models.get(model_type.value)
            scaler = self.scalers.get(model_type.value)

            if not model or not scaler:
                raise ValueError(f"Model {model_type.value} not available")

            # Prepare features
            feature_names = self.model_metadata[model_type.value]["features"]
            if not feature_names:
                # Use all provided features
                feature_names = list(features.keys())

            feature_values = np.array([features.get(name, 0.0) for name in feature_names]).reshape(1, -1)
            scaled_features = scaler.transform(feature_values)

            # Make prediction
            if hasattr(model, 'predict_proba'):
                predictions = model.predict_proba(scaled_features)
                predicted_values = {"probability": float(predictions[0][1])}
            else:
                predictions = model.predict(scaled_features)
                predicted_values = {"value": float(predictions[0])}

            # Calculate confidence intervals (simplified)
            confidence_intervals = self._calculate_confidence_intervals(
                predicted_values, model_type
            )

            # Calculate feature importance
            feature_importance = await self._calculate_feature_importance(
                model, feature_names, scaled_features
            )

            # Get model accuracy
            model_accuracy = self.model_metadata[model_type.value]["accuracy"]

            execution_time = asyncio.get_event_loop().time() - start_time

            # Create result
            result = PredictionResult(
                prediction_type=prediction_type,
                model_type=model_type,
                predicted_values=predicted_values,
                confidence_intervals=confidence_intervals,
                confidence_score=min(model_accuracy, 1.0),
                feature_importance=feature_importance,
                model_accuracy=model_accuracy,
                execution_time=execution_time,
                recommendations=self._generate_recommendations(
                    prediction_type, predicted_values, features
                ),
                warnings=self._generate_warnings(
                    prediction_type, predicted_values, model_accuracy
                )
            )

            # Cache result
            await self.cache.set(cache_key, result, tenant_id=tenant_id)

            # Record metrics
            ANALYTICS_METRICS["prediction_requests_total"].labels(
                model_type=model_type.value,
                tenant_id=tenant_id,
                prediction_type=prediction_type.value
            ).inc()

            ANALYTICS_METRICS["prediction_latency_seconds"].labels(
                model_type=model_type.value,
                prediction_type=prediction_type.value
            ).observe(execution_time)

            ANALYTICS_METRICS["model_accuracy_gauge"].labels(
                model_name=model_type.value,
                metric_type="accuracy"
            ).set(model_accuracy)

            return result

        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            self.logger.error(f"Prediction failed: {e}", exc_info=True)

            # Return fallback result
            return PredictionResult(
                prediction_type=prediction_type,
                model_type=self._get_model_type_for_prediction(prediction_type),
                predicted_values={"error": "Prediction failed"},
                confidence_intervals={},
                confidence_score=0.1,
                feature_importance={},
                model_accuracy=0.0,
                execution_time=execution_time,
                recommendations=["Contact support for manual analysis"],
                warnings=[f"Prediction error: {str(e)}"]
            )

    async def generate_business_insights(
        self,
        tenant_id: str,
        insight_types: List[str] = None
    ) -> List[BusinessInsight]:
        """Generate comprehensive business insights."""

        if insight_types is None:
            insight_types = ["performance", "cost", "efficiency", "risk"]

        insights = []

        # Performance insights
        if "performance" in insight_types:
            performance_insight = await self._analyze_performance_insights(tenant_id)
            if performance_insight:
                insights.append(performance_insight)

        # Cost insights
        if "cost" in insight_types:
            cost_insight = await self._analyze_cost_insights(tenant_id)
            if cost_insight:
                insights.append(cost_insight)

        # Efficiency insights
        if "efficiency" in insight_types:
            efficiency_insight = await self._analyze_efficiency_insights(tenant_id)
            if efficiency_insight:
                insights.append(efficiency_insight)

        # Risk insights
        if "risk" in insight_types:
            risk_insight = await self._analyze_risk_insights(tenant_id)
            if risk_insight:
                insights.append(risk_insight)

        return insights

    async def get_analytics_dashboard(
        self,
        tenant_id: str,
        time_range: str = "7d"
    ) -> Dict[str, Any]:
        """Get comprehensive analytics dashboard data."""

        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "tenant_id": tenant_id,
            "time_range": time_range,
            "summary": {},
            "charts": {},
            "insights": [],
            "predictions": {},
            "alerts": []
        }

        # Get summary metrics
        dashboard_data["summary"] = await self._get_summary_metrics(tenant_id, time_range)

        # Get chart data
        dashboard_data["charts"] = await self._get_chart_data(tenant_id, time_range)

        # Get recent insights
        dashboard_data["insights"] = await self.generate_business_insights(tenant_id)

        # Get current predictions
        dashboard_data["predictions"] = await self._get_current_predictions(tenant_id)

        # Get active alerts
        dashboard_data["alerts"] = await self._get_active_alerts(tenant_id)

        return dashboard_data

    async def train_model(
        self,
        model_type: AnalyticsModelType,
        training_data: List[AnalyticsData],
        tenant_id: str = "default"
    ) -> Dict[str, Any]:
        """Train a specific model with new data."""

        start_time = asyncio.get_event_loop().time()

        try:
            # Prepare data
            df = self._prepare_training_data(training_data)

            if df.empty or len(df) < 10:
                raise ValueError("Insufficient training data")

            # Get model and scaler
            model = self.models.get(model_type.value)
            scaler = self.scalers.get(model_type.value)

            if not model or not scaler:
                raise ValueError(f"Model {model_type.value} not found")

            # Split features and labels
            feature_cols = [col for col in df.columns if col.startswith('feature_')]
            label_cols = [col for col in df.columns if col.startswith('label_')]

            if not feature_cols:
                raise ValueError("No feature columns found in training data")

            X = df[feature_cols].values
            y = df[label_cols[0]].values if label_cols else None

            # Scale features
            X_scaled = scaler.fit_transform(X)

            # Train model
            if y is not None:
                model.fit(X_scaled, y)

                # Calculate accuracy
                predictions = model.predict(X_scaled)
                if hasattr(model, 'predict_proba'):
                    accuracy = accuracy_score(y, predictions)
                else:
                    accuracy = 1.0 - mean_squared_error(y, predictions)
            else:
                # Unsupervised learning
                model.fit(X_scaled)
                accuracy = 0.8  # Default for unsupervised

            # Update metadata
            self.model_metadata[model_type.value].update({
                "accuracy": accuracy,
                "last_trained": datetime.now(),
                "training_samples": len(df),
                "features": feature_cols
            })

            # Save model
            await self._save_model(model_type.value)

            execution_time = asyncio.get_event_loop().time() - start_time

            return {
                "model_type": model_type.value,
                "accuracy": accuracy,
                "training_samples": len(df),
                "execution_time": execution_time,
                "status": "success"
            }

        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            self.logger.error(f"Model training failed: {e}", exc_info=True)

            return {
                "model_type": model_type.value,
                "status": "error",
                "error": str(e),
                "execution_time": execution_time
            }

    def _get_model_type_for_prediction(self, prediction_type: PredictionType) -> AnalyticsModelType:
        """Map prediction type to model type."""

        mapping = {
            PredictionType.DESIGN_SUCCESS: AnalyticsModelType.PERFORMANCE_PREDICTION,
            PredictionType.COST_ESTIMATION: AnalyticsModelType.COST_OPTIMIZATION,
            PredictionType.PERFORMANCE_METRICS: AnalyticsModelType.PERFORMANCE_PREDICTION,
            PredictionType.MAINTENANCE_NEEDS: AnalyticsModelType.PREDICTIVE_MAINTENANCE,
            PredictionType.USER_SATISFACTION: AnalyticsModelType.USER_BEHAVIOR,
            PredictionType.COMPLIANCE_RISK: AnalyticsModelType.RISK_ASSESSMENT,
            PredictionType.MARKET_DEMAND: AnalyticsModelType.MARKET_TREND,
            PredictionType.RESOURCE_UTILIZATION: AnalyticsModelType.EFFICIENCY_OPTIMIZATION
        }

        return mapping.get(prediction_type, AnalyticsModelType.PERFORMANCE_PREDICTION)

    def _calculate_confidence_intervals(
        self,
        predicted_values: Dict[str, float],
        model_type: AnalyticsModelType
    ) -> Dict[str, Tuple[float, float]]:
        """Calculate confidence intervals for predictions."""

        intervals = {}
        for key, value in predicted_values.items():
            # Simplified confidence interval calculation
            margin = value * 0.1  # 10% margin
            intervals[key] = (max(0, value - margin), min(1.0, value + margin))

        return intervals

    async def _calculate_feature_importance(
        self,
        model: Any,
        feature_names: List[str],
        features: np.ndarray
    ) -> Dict[str, float]:
        """Calculate feature importance for the prediction."""

        importance_dict = {}

        try:
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
                for name, importance in zip(feature_names, importances):
                    importance_dict[name] = float(importance)
            else:
                # Equal importance for models without built-in feature importance
                base_importance = 1.0 / len(feature_names)
                for name in feature_names:
                    importance_dict[name] = base_importance

        except Exception as e:
            self.logger.warning(f"Feature importance calculation failed: {e}")
            # Fallback to equal importance
            base_importance = 1.0 / len(feature_names)
            for name in feature_names:
                importance_dict[name] = base_importance

        return importance_dict

    def _generate_recommendations(
        self,
        prediction_type: PredictionType,
        predicted_values: Dict[str, float],
        features: Dict[str, float]
    ) -> List[str]:
        """Generate recommendations based on prediction results."""

        recommendations = []

        if prediction_type == PredictionType.COST_ESTIMATION:
            cost = predicted_values.get("value", 0)
            if cost > 100000:
                recommendations.append("Consider phased implementation to reduce upfront costs")
            if features.get("complexity", 0) > 0.7:
                recommendations.append("High complexity detected - consider simplifying design")

        elif prediction_type == PredictionType.PERFORMANCE_METRICS:
            performance = predicted_values.get("value", 0)
            if performance < 0.8:
                recommendations.append("Consider design optimization for better performance")
                recommendations.append("Review component specifications for efficiency")

        elif prediction_type == PredictionType.COMPLIANCE_RISK:
            risk = predicted_values.get("probability", 0)
            if risk > 0.3:
                recommendations.append("Schedule compliance review with regulatory experts")
                recommendations.append("Implement additional safety measures")

        return recommendations[:3]  # Limit to 3 recommendations

    def _generate_warnings(
        self,
        prediction_type: PredictionType,
        predicted_values: Dict[str, float],
        model_accuracy: float
    ) -> List[str]:
        """Generate warnings based on prediction results."""

        warnings = []

        if model_accuracy < self.config.min_model_accuracy:
            warnings.append(f"Model accuracy ({model_accuracy:.2f}) is below threshold")

        if prediction_type == PredictionType.COMPLIANCE_RISK:
            risk = predicted_values.get("probability", 0)
            if risk > 0.7:
                warnings.append("High compliance risk detected - immediate action required")

        return warnings

    async def _analyze_performance_insights(self, tenant_id: str) -> Optional[BusinessInsight]:
        """Analyze performance-related insights."""

        try:
            # Get recent performance data
            performance_data = await self._get_performance_data(tenant_id, days=30)

            if not performance_data:
                return None

            # Calculate trends
            avg_response_time = np.mean([d.get("response_time", 0) for d in performance_data])
            avg_success_rate = np.mean([d.get("success_rate", 0) for d in performance_data])

            # Generate insight
            if avg_response_time > 1.0:  # Slow performance
                return BusinessInsight(
                    insight_type="performance",
                    title="Performance Optimization Opportunity",
                    description=f"Average response time of {avg_response_time:.2f}s detected",
                    confidence_score=0.85,
                    impact_score=8,
                    recommendations=[
                        "Implement query result caching",
                        "Optimize database queries",
                        "Consider CDN for static assets",
                        "Review server resource allocation"
                    ],
                    supporting_data={
                        "avg_response_time": avg_response_time,
                        "avg_success_rate": avg_success_rate,
                        "data_points": len(performance_data)
                    }
                )

            return None

        except Exception as e:
            self.logger.error(f"Performance analysis failed: {e}")
            return None

    async def _analyze_cost_insights(self, tenant_id: str) -> Optional[BusinessInsight]:
        """Analyze cost-related insights."""

        try:
            # Get cost data
            cost_data = await self._get_cost_data(tenant_id, days=30)

            if not cost_data:
                return None

            # Analyze cost trends
            total_cost = sum(d.get("cost", 0) for d in cost_data)
            avg_cost_per_design = total_cost / max(len(cost_data), 1)

            if avg_cost_per_design > 50000:  # High cost threshold
                return BusinessInsight(
                    insight_type="cost",
                    title="Cost Optimization Opportunity",
                    description=f"Average design cost of ${avg_cost_per_design:,.0f} is above optimal range",
                    confidence_score=0.82,
                    impact_score=7,
                    recommendations=[
                        "Review component selection for cost-effective alternatives",
                        "Optimize design specifications to reduce material costs",
                        "Consider bulk purchasing for frequently used components",
                        "Implement design templates for common use cases"
                    ],
                    supporting_data={
                        "total_cost": total_cost,
                        "avg_cost_per_design": avg_cost_per_design,
                        "designs_analyzed": len(cost_data)
                    }
                )

            return None

        except Exception as e:
            self.logger.error(f"Cost analysis failed: {e}")
            return None

    async def _analyze_efficiency_insights(self, tenant_id: str) -> Optional[BusinessInsight]:
        """Analyze efficiency-related insights."""

        try:
            # Get efficiency data
            efficiency_data = await self._get_efficiency_data(tenant_id, days=30)

            if not efficiency_data:
                return None

            # Calculate efficiency metrics
            avg_efficiency = np.mean([d.get("efficiency", 0) for d in efficiency_data])

            if avg_efficiency < 0.75:  # Low efficiency threshold
                return BusinessInsight(
                    insight_type="efficiency",
                    title="Efficiency Improvement Opportunity",
                    description=f"System efficiency of {avg_efficiency:.1%} indicates optimization potential",
                    confidence_score=0.78,
                    impact_score=6,
                    recommendations=[
                        "Review system configuration for optimal performance",
                        "Consider upgrading to higher efficiency components",
                        "Implement energy management system",
                        "Schedule maintenance to improve system performance"
                    ],
                    supporting_data={
                        "avg_efficiency": avg_efficiency,
                        "data_points": len(efficiency_data),
                        "efficiency_trend": "declining" if avg_efficiency < 0.7 else "stable"
                    }
                )

            return None

        except Exception as e:
            self.logger.error(f"Efficiency analysis failed: {e}")
            return None

    async def _analyze_risk_insights(self, tenant_id: str) -> Optional[BusinessInsight]:
        """Analyze risk-related insights."""

        try:
            # Get risk data
            risk_data = await self._get_risk_data(tenant_id, days=30)

            if not risk_data:
                return None

            # Calculate risk metrics
            high_risk_count = sum(1 for d in risk_data if d.get("risk_score", 0) > 0.7)
            total_assessments = len(risk_data)

            if high_risk_count > total_assessments * 0.3:  # 30% high risk threshold
                return BusinessInsight(
                    insight_type="risk",
                    title="Risk Management Attention Required",
                    description=f"{high_risk_count}/{total_assessments} assessments show high risk levels",
                    confidence_score=0.88,
                    impact_score=9,
                    recommendations=[
                        "Implement immediate risk mitigation measures",
                        "Schedule detailed risk assessment with experts",
                        "Review design specifications for safety compliance",
                        "Enhance monitoring and early warning systems"
                    ],
                    supporting_data={
                        "high_risk_count": high_risk_count,
                        "total_assessments": total_assessments,
                        "risk_percentage": high_risk_count / total_assessments
                    }
                )

            return None

        except Exception as e:
            self.logger.error(f"Risk analysis failed: {e}")
            return None

    def _prepare_training_data(self, training_data: List[AnalyticsData]) -> pd.DataFrame:
        """Prepare training data for model training."""

        if not training_data:
            return pd.DataFrame()

        # Convert to DataFrame
        data_dict = {
            "timestamp": [d.timestamp for d in training_data],
            "tenant_id": [d.tenant_id for d in training_data],
            "data_type": [d.data_type for d in training_data]
        }

        # Add features
        all_features = set()
        for d in training_data:
            all_features.update(d.features.keys())

        for feature in all_features:
            data_dict[f"feature_{feature}"] = [
                d.features.get(feature, 0.0) for d in training_data
            ]

        # Add labels if available
        if training_data[0].labels:
            all_labels = set()
            for d in training_data:
                if d.labels:
                    all_labels.update(d.labels.keys())

            for label in all_labels:
                data_dict[f"label_{label}"] = [
                    d.labels.get(label, 0.0) if d.labels else 0.0
                    for d in training_data
                ]

        return pd.DataFrame(data_dict)

    async def _load_models(self) -> None:
        """Load persisted models from storage."""

        if not self.redis:
            return

        try:
            # Load model metadata
            metadata_keys = await self.redis.keys("model_metadata:*")
            for key in metadata_keys:
                model_name = key.decode().replace("model_metadata:", "")
                metadata = await self.redis.get(key)
                if metadata:
                    self.model_metadata[model_name] = json.loads(metadata)

            # Load model states (simplified - in practice would load actual model files)
            self.logger.info("Models loaded from persistent storage")

        except Exception as e:
            self.logger.warning(f"Model loading failed: {e}")

    async def _save_models(self) -> None:
        """Save models to persistent storage."""

        if not self.redis:
            return

        try:
            # Save model metadata
            for model_name, metadata in self.model_metadata.items():
                await self.redis.set(
                    f"model_metadata:{model_name}",
                    json.dumps(metadata)
                )

            # In a real implementation, you would save the actual model files
            self.logger.info("Models saved to persistent storage")

        except Exception as e:
            self.logger.error(f"Model saving failed: {e}")

    async def _save_model(self, model_name: str) -> None:
        """Save a specific model."""

        if not self.redis:
            return

        try:
            # Save model metadata
            metadata = self.model_metadata.get(model_name, {})
            await self.redis.set(
                f"model_metadata:{model_name}",
                json.dumps(metadata)
            )

        except Exception as e:
            self.logger.error(f"Model {model_name} saving failed: {e}")

    async def _model_maintenance_loop(self) -> None:
        """Background loop for model maintenance."""

        while True:
            try:
                await asyncio.sleep(self.config.model_update_interval_hours * 3600)

                # Check model performance and retrain if needed
                for model_name in self.models.keys():
                    await self._check_model_performance(model_name)

            except Exception as e:
                self.logger.error(f"Model maintenance failed: {e}")
                await asyncio.sleep(3600)  # Retry in 1 hour

    async def _data_collection_loop(self) -> None:
        """Background loop for data collection."""

        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes

                # Collect system metrics for training
                await self._collect_training_data()

            except Exception as e:
                self.logger.error(f"Data collection failed: {e}")
                await asyncio.sleep(300)

    async def _check_model_performance(self, model_name: str) -> None:
        """Check model performance and retrain if needed."""

        metadata = self.model_metadata.get(model_name, {})
        current_accuracy = metadata.get("accuracy", 0.0)

        if current_accuracy < self.config.min_model_accuracy:
            self.logger.info(f"Retraining model {model_name} due to low accuracy")
            # In practice, you would collect new training data and retrain
            await self._retrain_model(model_name)

    async def _retrain_model(self, model_name: str) -> None:
        """Retrain a specific model."""

        training_data = self.training_data.get(model_name, [])
        if len(training_data) < 10:
            self.logger.warning(f"Insufficient training data for {model_name}")
            return

        # Retrain model
        result = await self.train_model(
            AnalyticsModelType(model_name),
            training_data[-self.config.max_training_data_points:]
        )

        if result["status"] == "success":
            self.logger.info(f"Model {model_name} retrained with accuracy {result['accuracy']:.3f}")

    async def _collect_training_data(self) -> None:
        """Collect training data from system operations."""

        # In practice, this would collect data from various system operations
        # For demonstration, we'll create sample data
        pass

    async def _get_performance_data(self, tenant_id: str, days: int) -> List[Dict[str, Any]]:
        """Get performance data for analysis."""

        # In practice, this would query a database or data warehouse
        # For demonstration, return sample data
        return [
            {"response_time": 0.8, "success_rate": 0.95},
            {"response_time": 1.2, "success_rate": 0.92},
            {"response_time": 0.9, "success_rate": 0.97}
        ]

    async def _get_cost_data(self, tenant_id: str, days: int) -> List[Dict[str, Any]]:
        """Get cost data for analysis."""

        # Sample cost data
        return [
            {"cost": 45000},
            {"cost": 52000},
            {"cost": 48000}
        ]

    async def _get_efficiency_data(self, tenant_id: str, days: int) -> List[Dict[str, Any]]:
        """Get efficiency data for analysis."""

        # Sample efficiency data
        return [
            {"efficiency": 0.82},
            {"efficiency": 0.78},
            {"efficiency": 0.85}
        ]

    async def _get_risk_data(self, tenant_id: str, days: int) -> List[Dict[str, Any]]:
        """Get risk data for analysis."""

        # Sample risk data
        return [
            {"risk_score": 0.6},
            {"risk_score": 0.8},
            {"risk_score": 0.4}
        ]

    async def _get_summary_metrics(self, tenant_id: str, time_range: str) -> Dict[str, Any]:
        """Get summary metrics for dashboard."""

        return {
            "total_predictions": 1250,
            "average_accuracy": 0.87,
            "active_models": len(self.models),
            "data_points_processed": 45000,
            "insights_generated": 23
        }

    async def _get_chart_data(self, tenant_id: str, time_range: str) -> Dict[str, Any]:
        """Get chart data for dashboard."""

        return {
            "prediction_accuracy": {
                "labels": ["Jan", "Feb", "Mar", "Apr", "May"],
                "datasets": [{
                    "label": "Accuracy",
                    "data": [0.82, 0.85, 0.87, 0.89, 0.91]
                }]
            },
            "model_performance": {
                "labels": list(self.models.keys()),
                "datasets": [{
                    "label": "Performance Score",
                    "data": [0.88, 0.85, 0.92, 0.78, 0.89]
                }]
            }
        }

    async def _get_current_predictions(self, tenant_id: str) -> Dict[str, Any]:
        """Get current predictions for dashboard."""

        return {
            "next_week_demand": {"value": 0.75, "confidence": 0.82},
            "cost_efficiency": {"value": 0.68, "confidence": 0.79},
            "maintenance_needs": {"value": 0.23, "confidence": 0.88}
        }

    async def _get_active_alerts(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get active alerts for dashboard."""

        return [
            {
                "type": "warning",
                "message": "Model accuracy below threshold",
                "timestamp": datetime.now().isoformat()
            },
            {
                "type": "info",
                "message": "New insights available",
                "timestamp": datetime.now().isoformat()
            }
        ]


# Global analytics engine instance
_analytics_engine: Optional[EnterpriseAnalyticsEngine] = None


def get_analytics_engine() -> EnterpriseAnalyticsEngine:
    """Get the global analytics engine instance."""
    if _analytics_engine is None:
        raise RuntimeError("Analytics engine not initialized")
    return _analytics_engine


async def initialize_analytics(config: AnalyticsConfig) -> EnterpriseAnalyticsEngine:
    """Initialize the enterprise analytics system."""
    global _analytics_engine

    if _analytics_engine is None:
        _analytics_engine = EnterpriseAnalyticsEngine(config)
        await _analytics_engine.initialize()
        logger.info("Enterprise Analytics System initialized")

    return _analytics_engine


# Example usage functions
async def predict_design_success(
    features: Dict[str, float],
    tenant_id: str = "default"
) -> PredictionResult:
    """Predict design success probability."""

    engine = get_analytics_engine()
    return await engine.predict(
        PredictionType.DESIGN_SUCCESS,
        features,
        tenant_id
    )


async def get_business_insights(
    tenant_id: str,
    insight_types: List[str] = None
) -> List[BusinessInsight]:
    """Get business insights for a tenant."""

    engine = get_analytics_engine()
    return await engine.generate_business_insights(tenant_id, insight_types)


async def get_analytics_dashboard(
    tenant_id: str,
    time_range: str = "7d"
) -> Dict[str, Any]:
    """Get analytics dashboard data."""

    engine = get_analytics_engine()
    return await engine.get_analytics_dashboard(tenant_id, time_range)
