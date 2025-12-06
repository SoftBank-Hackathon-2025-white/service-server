from datetime import datetime
from typing import List

from app.clients.cloudwatch import CloudWatchClient 
from app.models.cloudwatch import CloudWatchMetricPoint


class ResourceService:
    """ECS 리소스/메트릭 조회를 담당하는 도메인 서비스입니다."""

    def __init__(self, cw_client: CloudWatchClient) -> None:
        self.cw_client = cw_client

    def list_cluster_metric_names(self, cluster_name: str) -> List[str]:
        """클러스터에서 사용 가능한 메트릭 이름 리스트를 반환합니다."""
        return self.cw_client.list_cluster_metric_names(cluster_name)

    def get_recent_cpu_memory_utilization(
        self,
        cluster_name: str,
        minutes: int = 10,
        period: int = 60,
    ) -> list[CloudWatchMetricPoint]:
        """최근 N분 동안의 CPU/Memory 사용률을 도메인 모델로 반환합니다."""
        raw = self.cw_client.get_cpu_memory_timeseries(
            cluster_name=cluster_name,
            minutes=minutes,
            period=period,
        )

        # timestamp 기준으로 cpu / memory merge
        result_map: dict[datetime, dict] = {}

        for metric_result in raw.get("MetricDataResults", []):
            metric_id = metric_result["Id"]  # "cpu" or "memory"
            timestamps = metric_result.get("Timestamps", [])
            values = metric_result.get("Values", [])
            
            for ts, value in zip(timestamps, values):
                if ts not in result_map:
                    result_map[ts] = {
                        "timestamp": ts,
                        "cpu_utilization": None,
                        "memory_utilization": None,
                    }
                if metric_id == "cpu":
                    result_map[ts]["cpu_utilization"] = value
                else:
                    result_map[ts]["memory_utilization"] = value

        points = [
            CloudWatchMetricPoint(
                timestamp=ts,
                cpu_utilization=data["cpu_utilization"],
                memory_utilization=data["memory_utilization"],
            )
            for ts, data in sorted(result_map.items(), key=lambda x: x[0])
        ]

        return points

    def get_latest_cpu_memory_snapshot(
        self,
        cluster_name: str,
        minutes: int = 5,
        period: int = 60,
    ) -> dict:
        """가장 최신 CPU/Memory 값 요약본을 반환합니다."""
        return self.cw_client.get_latest_cpu_memory_snapshot(
            cluster_name=cluster_name,
            minutes=minutes,
            period=period,
        )
