# Service Server

FastAPI 기반 코드 실행 관리 API Gateway입니다. 사용자가 업로드한 코드를 S3에 저장하고, Execution Engine으로 실행하며, 결과를 RDS에 저장합니다.

## 기술 스택

| 항목 | 기술 |
|------|------|
| Framework | FastAPI 0.123+ |
| ORM | SQLAlchemy 2.0+ |
| Database | MySQL 8.0+ (AWS RDS) |
| Storage | AWS S3 |
| Monit oring | AWS CloudWatch |
| Language | Python 3.11+ |

## 프로젝트 구조

```
app/
├── api/routes.py              # 13개 API 엔드포인트
├── clients/
│   ├── cloudwatch.py          # CloudWatch 메트릭 조회
│   └── s3.py                  # S3 업로드
├── models/                    # Pydantic DTO (요청/응답)
├── schemas/                   # SQLAlchemy ORM (DB 모델)
└── services/                  # 비즈니스 로직
    ├── job.py                 # Job CRUD & 상태 관리
    ├── project.py             # 프로젝트 관리
    ├── execution.py           # Execution Engine 연동
    ├── s3.py                  # S3 통합
    └── cloudwatch.py          # CloudWatch 조회

config/
├── settings.py                # 환경 변수 설정
└── db.py                      # 데이터베이스 초기화

main.py                        # FastAPI 앱
```

## 핵심 기술 아키텍처

### 1. 비동기 작업 처리

Execution Engine의 느린 실행 대기를 없애기 위해 **백그라운드 작업**으로 처리합니다:

```python
@router.post("/execute/{jobId}")
async def execute_code(
    jobId: str,
    background_tasks: BackgroundTasks,
    job_service: JobService = Depends(get_job_service),
    execution_service: ExecutionService = Depends(get_execution_service),
):
    # 1. Job 상태를 PENDING → RUNNING으로 변경
    job_service.update_job_status(jobId, JobStatus.RUNNING)
    
    # 2. 백그라운드에서 Execution Engine 호출
    background_tasks.add_task(
        run_execution_and_update_job,
        jobId,
        execution_request,
        job_service,
        execution_service,
    )
    
    # 3. 즉시 클라이언트에 응답 (RUNNING 상태)
    return job_service.to_response(job, "Execution started")
```

**기술적 장점:**
- 클라이언트는 즉시 응답 받음 (Execution Engine 대기 시간 제거)
- 동시에 여러 작업 처리 가능 (높은 동시성)
- 서버 리소스 효율적 사용

### 2. Job 상태 관리

**Job 라이프사이클:**
```
PENDING → RUNNING → SUCCESS/FAILED/TIMEOUT/CANCELLED
```

**SQLAlchemy 기반 상태 추적:**
```python
class JobService:
    def update_job_status(self, job_id: str, status: JobStatus) -> bool:
        job_orm = self.db.query(JobORM).filter(JobORM.job_id == job_id).first()
        job_orm.status = status
        job_orm.updated_at = datetime.utcnow()
        
        # 상태별 타임스탬프 자동 기록
        if status == JobStatus.RUNNING:
            job_orm.started_at = datetime.utcnow()
        elif status in [JobStatus.SUCCESS, JobStatus.FAILED, ...]:
            job_orm.completed_at = datetime.utcnow()
        
        self.db.commit()  # 트랜잭션 커밋
```

**기술적 장점:**
- 데이터베이스에 지속성 보장 (서버 재시작 후에도 상태 추적)
- 실행 시간(started_at, completed_at) 자동 기록
- `(project, status)` 복합 인덱스로 쿼리 최적화

### 3. CloudWatch 실시간 모니터링

**ECS 클러스터의 CPU/Memory 메트릭 조회:**

```python
class ResourceService:
    def get_recent_cpu_memory_utilization(
        self,
        cluster_name: str,
        minutes: int = 10,
        period: int = 60,  # 1분 단위
    ) -> list[CloudWatchMetricPoint]:
        # CloudWatch API 호출
        raw = self.cw_client.get_cpu_memory_timeseries(
            cluster_name=cluster_name,
            minutes=minutes,
            period=period,
        )
        
        # CPU/Memory 데이터를 타임스탬프별로 병합
        result_map: dict[datetime, dict] = {}
        for metric_result in raw.get("MetricDataResults", []):
            metric_id = metric_result["Id"]  # "cpu" or "memory"
            for ts, value in zip(metric_result["Timestamps"], metric_result["Values"]):
                if ts not in result_map:
                    result_map[ts] = {
                        "timestamp": ts,
                        "cpu_utilization": None,
                        "memory_utilization": None
                    }
                if metric_id == "cpu":
                    result_map[ts]["cpu_utilization"] = value
                else:
                    result_map[ts]["memory_utilization"] = value
        
        # 시간순 정렬해서 반환
        return [CloudWatchMetricPoint(**data) for ts, data in sorted(result_map.items())]
```

**기술적 장점:**
- 실시간 ECS 리소스 사용률 모니터링
- 1분 단위 세분화된 메트릭 (period=60)
- 최대 60분 범위 조회

**API 사용 예시:**
```bash
GET /api/cloudwatch/softbank-execution-engine?minutes=10&period=60
# → CPU/Memory 10분간의 시계열 데이터 반환
```

## API 요약

### 코드 및 Job 관리
- `POST /api/upload` - 코드 업로드 & Job 생성
- `POST /api/execute/{jobId}` - 코드 실행 (비동기 백그라운드)
- `GET /api/jobs` - Job 목록 조회
- `GET /api/projects/{project}/jobs` - 프로젝트별 Job 목록

### 모니터링
- `GET /api/cloudwatch/{clusterName}` - CPU/Memory 메트릭 조회
- `GET /api/cloudwatch/{clusterName}/metrics` - 사용 가능한 메트릭 목록

### 기타
- `GET /api/projects` - 프로젝트 목록
- `POST /api/project` - 프로젝트 생성
- `GET /api/log?log_key={key}` - S3 로그 파일 조회
- `GET /api/health` - 헬스 체크

## 의존성 주입 패턴

FastAPI의 **의존성 주입(Dependency Injection)** 패턴을 사용하여 매 요청마다 독립적인 DB 세션 제공:

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_job_service(db: Session = Depends(get_db)) -> JobService:
    return JobService(db)

@router.post("/execute/{jobId}")
async def execute_code(
    jobId: str,
    background_tasks: BackgroundTasks,
    job_service: JobService = Depends(get_job_service),
    execution_service: ExecutionService = Depends(get_execution_service),
):
    # FastAPI가 자동으로 DB 세션 생성 & 서비스 인스턴스화
```

**이점:**
- 매 요청마다 독립적인 DB 세션
- 테스트 시 Mock 서비스 쉽게 주입
- 느슨한 결합

## 시작하기

```bash
# 1. 가상환경 및 의존성 설치
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. 환경 설정 (.env)
# AWS_RDS_HOST, AWS_RDS_PORT, AWS_RDS_DBNAME, AWS_RDS_USERNAME, AWS_RDS_PASSWORD
# AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
# AWS_CODE_BUCKET, AWS_LOG_BUCKET 등

# 3. 데이터베이스 테이블 수동 생성 (DB에 직접 실행)
# SQLAlchemy ORM에 의해 자동으로 생성되지 않으므로 SQL 스크립트 실행 필요

# 4. 서버 실행
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 요청/응답 예시

### 코드 업로드
```bash
curl -X POST http://localhost:8000/api/upload \
  -H "Content-Type: application/json" \
  -d '{
    "project": "my-project",
    "code": "print(\"hello\")",
    "language": "python"
  }'
```

응답:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "project": "my-project",
  "code_key": "my-project/550e8400.py",
  "status": "PENDING",
  "message": "Code uploaded successfully"
}
```

### 코드 실행
```bash
curl -X POST http://localhost:8000/api/execute/550e8400-e29b-41d4-a716-446655440000
```

응답:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "RUNNING",
  "message": "Execution started"
}
```

## 주요 패키지

- **fastapi**: 웹 프레임워크
- **sqlalchemy**: ORM
- **pydantic**: 데이터 검증 및 직렬화
- **boto3**: AWS SDK (S3, CloudWatch)
- **httpx**: 비동기 HTTP 클라이언트
- **uvicorn**: ASGI 서버
