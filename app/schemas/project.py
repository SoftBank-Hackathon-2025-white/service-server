from sqlalchemy import Integer, Column, String, Text
from config.db import Base


class ProjectORM(Base):
    """프로젝트 정보를 저장하는 ORM 엔티티입니다.

    여러 Job이 같은 프로젝트에 속할 수 있습니다.
    """

    __tablename__ = "projects"

    project_id: int = Column(Integer, primary_key=True, autoincrement=True)
    project: str = Column(String(255), nullable=False, unique=True, index=True)
    description: str = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<ProjectORM(project_id={self.project_id}, project={self.project})>"
