from typing import Optional, List
from app.schemas.project import ProjectORM
from sqlalchemy.orm import Session


class ProjectService:
    """프로젝트 관리를 담당하는 서비스입니다.

    프로젝트 생성, 조회, 목록 조회 등의 작업을 처리합니다.
    """
    
    def __init__(self, db: Session) -> None:
        """데이터베이스 세션을 초기화합니다."""
        self.db = db
    
    def get_or_create_project(self, project_name: str, description: Optional[str] = None) -> ProjectORM:
        """프로젝트를 조회하거나 없으면 생성합니다.
        
        Args:
            project_name: 프로젝트 이름.
            description: 프로젝트 설명 (선택사항).
            
        Returns:
            프로젝트 ORM 엔티티.
        """
        project_orm = self.db.query(ProjectORM).filter(ProjectORM.project == project_name).first()
        
        if not project_orm:
            project_orm = ProjectORM(
                project=project_name,
                description=description
            )
            self.db.add(project_orm)
            self.db.flush()
        
        return project_orm
    
    def get_project(self, project_name: str) -> Optional[ProjectORM]:
        """프로젝트 이름으로 프로젝트를 조회합니다.
        
        Args:
            project_name: 프로젝트 이름.
            
        Returns:
            프로젝트 ORM 엔티티 또는 None.
        """
        return self.db.query(ProjectORM).filter(ProjectORM.project == project_name).first()
    
    def get_all_projects(self) -> List[str]:
        """저장된 모든 프로젝트 이름을 반환합니다.
        
        Returns:
            프로젝트 이름 리스트.
        """
        projects = self.db.query(ProjectORM.project).all()
        return [p[0] for p in projects]
    
    def update_project_description(self, project_name: str, description: str) -> bool:
        """프로젝트 설명을 업데이트합니다.
        
        Args:
            project_name: 프로젝트 이름.
            description: 새로운 설명.
            
        Returns:
            업데이트 성공 여부.
        """
        project_orm = self.db.query(ProjectORM).filter(ProjectORM.project == project_name).first()
        
        if not project_orm:
            return False
        
        project_orm.description = description
        self.db.commit()
        return True
