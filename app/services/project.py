from typing import Optional, List
from app.schemas.project import ProjectORM
from app.models.project import ProjectResponse
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
            self.db.commit()
        
        return project_orm
    
    def get_project(self, project_name: str) -> Optional[ProjectORM]:
        """프로젝트 이름으로 프로젝트를 조회합니다.
        
        Args:
            project_name: 프로젝트 이름.
            
        Returns:
            프로젝트 ORM 엔티티 또는 None.
        """
        return self.db.query(ProjectORM).filter(ProjectORM.project == project_name).first()
    
    def get_project_by_id(self, project_id: int) -> Optional[ProjectResponse]:
        """프로젝트 ID로 프로젝트를 조회합니다.
        
        Args:
            project_id: 프로젝트 ID.
            
        Returns:
            프로젝트 응답 DTO 또는 None.
        """
        project_orm = self.db.query(ProjectORM).filter(ProjectORM.project_id == project_id).first()
        if not project_orm:
            return None
        return self._orm_to_dto(project_orm)
    
    def get_all_projects(self) -> List[ProjectORM]:
        """저장된 모든 프로젝트 정보를 반환합니다.
        
        Returns:
            프로젝트 ORM 엔티티 리스트.
        """
        return self.db.query(ProjectORM).all()
    
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
    
    def _orm_to_dto(self, project_orm: ProjectORM) -> ProjectResponse:
        """ProjectORM을 ProjectResponse DTO로 변환합니다."""
        return ProjectResponse(
            project_id=project_orm.project_id,
            project=project_orm.project,
            description=project_orm.description,
        )
