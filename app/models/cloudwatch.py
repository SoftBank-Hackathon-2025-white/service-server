from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class CloudWatchMetricPoint(BaseModel):
    timestamp: datetime
    cpu_utilization: Optional[float] = None
    memory_utilization: Optional[float] = None


class ClusterMetricsResponse(BaseModel):
    cluster_name: str
    metrics: List[CloudWatchMetricPoint]


class AvailableMetricsResponse(BaseModel):
    cluster_name: str
    metric_names: List[str]
