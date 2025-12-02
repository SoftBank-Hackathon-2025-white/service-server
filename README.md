# Service Server (FastAPI 백엔드)

코드 업로드/실행 요청을 받아 Execution Engine에 전달하고 결과와 리소스 지표를 반환하는 API Gateway 백엔드입니다.

## 주요 기능
- 코드 업로드 → **S3에 저장** → Job 생성(PENDING) 및 `job_id` 발급
- Job 실행 요청 → **S3에서 코드 다운로드** → Execution Engine 연동, stdout/stderr/리소스 메트릭 반환
- 상태 조회/실행 취소/Job 목록/헬스 체크 제공
- 환경 변수 기반 설정 (파일 로깅은 현재 미사용)

## 실행 방법
1) Python 3.11+ 가상환경 생성 후 패키지 설치
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
2) `.env` 확인/수정 (`EXECUTION_ENGINE_URL`, `EXECUTION_ENGINE_TIMEOUT` 등)
3) 서버 실행
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 환경 변수 (.env)
- `SERVER_HOST`, `SERVER_PORT`, `DEBUG`, `ENVIRONMENT`
- `EXECUTION_ENGINE_URL`, `EXECUTION_ENGINE_TIMEOUT`
- `AWS_REGION`, `AWS_S3_BUCKET`, `AWS_DYNAMODB_TABLE`
- `LOG_LEVEL`, `LOG_FILE` (현재 파일 로깅 미사용)

## API 엔드포인트
- `POST /api/upload` : 코드/언어 입력 → **S3 업로드** → Job 생성 (S3 object key 포함)
- `POST /api/execute/{job_id}` : 실행 요청 → **S3에서 코드 다운로드** → Execution Engine 실행 → stdout/stderr/resource/logs_url 반환
- `GET /api/status/{job_id}` : 상태 조회
- `POST /api/cancel/{job_id}` : 실행 취소 → CANCELLED
- `GET /api/jobs?limit=100` : Job 목록
- `GET /api/health` : 헬스 체크
- `/` : 서비스 메타 정보

### 요청 예시
```bash
# 1. 코드 업로드 (S3에 저장)
curl -X POST http://localhost:8000/api/upload \
  -H "Content-Type: application/json" \
  -d '{"code":"print(\"hello\")","language":"python"}'

# 응답: {"job_id":"abc-123-def","s3_key":"uploads/abc-123-def.py","status":"PENDING"}

# 2. 코드 실행 (S3에서 다운로드 후 Engine 실행)
curl -X POST http://localhost:8000/api/execute/abc-123-def \
  -H "Content-Type: application/json" \
  -d '{"input":"","timeout":5000}'
```

## 프로젝트 구조(미정)
```
app/
  api/routes.py              # 실행 API 라우터
  clients/
    engine_client.py         # Execution Engine HTTP 클라이언트
    s3_client.py             # AWS S3 클라이언트 (코드 업로드/다운로드)
  services/
    job_service.py           # Job 관리 서비스
    execution_service.py     # 코드 실행 서비스
    s3_service.py            # S3 업로드/다운로드 서비스
  models/                    # Pydantic 스키마
  utils/                     # 유틸리티 모듈
config/settings.py           # 환경 설정 로더
main.py                      # FastAPI 앱 엔트리포인트
```

## S3 워크플로우
1. **코드 업로드** (`/api/upload`)
   - 사용자 코드 → S3 업로드 (`s3://{BUCKET}/uploads/{job_id}.{extension}`)
   - DB/메모리에 Job 생성 (status: PENDING, s3_key 저장)
   - 클라이언트에게 job_id + s3_key 반환

2. **코드 실행** (`/api/execute/{job_id}`)
   - Job 조회 → S3에서 코드 다운로드
   - 코드 + job_id → Execution Engine 제출
   - 실행 결과 → 클라이언트 반환

## 기술 스택 / 주요 패키지
- FastAPI 0.123.4
- Pydantic 2.12.5
- httpx 0.28.1, anyio 4.12.0
- Uvicorn 0.38.0
- boto3 1.42.0 (S3/DynamoDB 연동)
