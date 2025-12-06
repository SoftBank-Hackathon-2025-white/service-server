import boto3
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from config.settings import settings


class CloudWatchClient:
    """ECS 관련 CloudWatch 메트릭을 조회하기 위한 저수준 클라이언트입니다."""

    def __init__(self, region_name: str | None = None) -> None:
        if region_name is None:
            region_name = getattr(settings, "AWS_REGION", "ap-northeast-2")

        client_kwargs: Dict[str, Any] = {
            "region_name": region_name,
        }

        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            client_kwargs.update(
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )
        if settings.AWS_SESSION_TOKEN:
            client_kwargs["aws_session_token"] = settings.AWS_SESSION_TOKEN

        self.client = boto3.client("cloudwatch", **client_kwargs)

    def list_cluster_metric_names(self, cluster_name: str) -> List[str]:
        """특정 ECS 클러스터에서 사용 가능한 CloudWatch 메트릭 이름 목록을 조회합니다."""
        paginator = self.client.get_paginator("list_metrics")

        metrics: List[Dict[str, Any]] = []
        for page in paginator.paginate(
            Namespace="AWS/ECS",
            Dimensions=[{"Name": "ClusterName", "Value": cluster_name}],
        ):
            metrics.extend(page.get("Metrics", []))

        return sorted({m["MetricName"] for m in metrics})

    def get_cpu_memory_timeseries(
        self,
        cluster_name: str,
        minutes: int = 10,
        period: int = 60,
    ) -> Dict[str, Any]:
        """CPU/Memory Utilization 시계열 RAW 데이터를 그대로 반환합니다."""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(minutes=minutes)

        resp = self.client.get_metric_data(
            MetricDataQueries=[
                {
                    "Id": "cpu",
                    "MetricStat": {
                        "Metric": {
                            "Namespace": "AWS/ECS",
                            "MetricName": "CPUUtilization",
                            "Dimensions": [
                                {"Name": "ClusterName", "Value": cluster_name},
                            ],
                        },
                        "Period": period,
                        "Stat": "Average",
                    },
                    "ReturnData": True,
                },
                {
                    "Id": "memory",
                    "MetricStat": {
                        "Metric": {
                            "Namespace": "AWS/ECS",
                            "MetricName": "MemoryUtilization",
                            "Dimensions": [
                                {"Name": "ClusterName", "Value": cluster_name},
                            ],
                        },
                        "Period": period,
                        "Stat": "Average",
                    },
                    "ReturnData": True,
                },
            ],
            StartTime=start_time,
            EndTime=end_time,
            ScanBy="TimestampAscending",
        )

        return resp

    def get_latest_cpu_memory_snapshot(
        self,
        cluster_name: str,
        minutes: int = 5,
        period: int = 60,
    ) -> Dict[str, float | None]:
        """최근 N분 동안의 메트릭에서 가장 최신 CPU/Memory 값만 요약해서 반환합니다."""
        resp = self.get_cpu_memory_timeseries(
            cluster_name=cluster_name,
            minutes=minutes,
            period=period,
        )

        result: Dict[str, float | None] = {
            "cpu_utilization": None,
            "memory_utilization": None,
        }

        for metric_result in resp["MetricDataResults"]:
            metric_id = metric_result["Id"]  # "cpu" 또는 "memory"
            values = metric_result.get("Values", [])
            if not values:
                continue

            latest_value = values[-1]
            if metric_id == "cpu":
                result["cpu_utilization"] = latest_value
            else:
                result["memory_utilization"] = latest_value

        return result
