# from sqlalchemy import Column, String, DateTime, Float, Index
# from datetime import datetime
# import uuid

# from config.db import Base


# class CloudWatchMetricORM(Base):
#     """ECS 클러스터의 CloudWatch 메트릭을 저장하는 ORM 엔티티입니다.

#     CPU 및 메모리 사용률을 시계열 데이터로 기록합니다.
#     """

#     __tablename__ = "cloudwatch_metrics"

#     id: str = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
#     cluster_name: str = Column(String(255), nullable=False, index=True)
#     cpu_utilization: float = Column(Float, nullable=True)
#     memory_utilization: float = Column(Float, nullable=True)
#     timestamp: datetime = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)

#     __table_args__ = (
#         Index("ix_cloudwatch_cluster_timestamp", "cluster_name", "timestamp"),
#     )

#     def __repr__(self) -> str:
#         return (
#             f"<CloudWatchMetricORM(cluster_name={self.cluster_name}, "
#             f"cpu={self.cpu_utilization}, memory={self.memory_utilization})>"
#         )
