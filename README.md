# 🏥 병원 대기현황판 시스템

환자 개인정보 보호 기반의 실시간 진료 대기현황 표시 시스템

---

## 📁 파일 구성

```
hospital_queue/
├── shared_store.py          ← 핵심 데이터 레이어 (두 앱이 공유)
├── staff_app.py             ← 직원용 원무과 관리 툴 (포트 8501)
├── patient_display.py       ← 환자용 대기현황판 (포트 8502)
├── api_server.py            ← HIS 연동 REST API (포트 5000)
├── his_integration_example.py ← HIS 연동 예제 코드
├── requirements.txt
├── start_all.sh             ← 전체 실행 스크립트
└── data/
    └── queue.json           ← 실시간 공유 데이터
```

---

## 🚀 실행 방법

### 설치
```bash
pip install -r requirements.txt
```

### 한번에 실행 (Linux/Mac)
```bash
chmod +x start_all.sh
./start_all.sh
```

### 개별 실행 (Windows 포함)
```bash
# 터미널 1: 직원용
streamlit run staff_app.py --server.port 8501

# 터미널 2: 환자용
streamlit run patient_display.py --server.port 8502

# 터미널 3: API 서버 (HIS 연동 시만 필요)
python api_server.py
```

---

## 🖥️ 접속 주소

| 화면 | URL | 대상 |
|------|-----|------|
| 직원용 (원무과) | http://서버IP:8501 | 원무과 직원 PC |
| 환자용 (대기현황판) | http://서버IP:8502 | 원내 TV/모니터 |
| HIS 연동 API | http://서버IP:5000 | HIS 소프트웨어 |

---

## 🔐 개인정보 보호 기능

| 기능 | 설명 |
|------|------|
| 이름 마스킹 | 박민지 → 박X지 (중간 글자 X 처리) |
| 차트번호 미표시 | 내부 메모로만 저장, 화면에 절대 노출 안 됨 |
| API 키 인증 | HIS 연동 API에 키 인증 필수 |
| 감사 로그 | 모든 접수/상태변경 기록 (마스킹 이름으로) |

### 마스킹 규칙
- 2글자: `김철` → `김X`
- 3글자: `박민지` → `박X지`
- 4글자: `남궁민수` → `남XX수`

---

## 🔌 HIS 연동 방법

### 방법 1: API 직접 연동 (추천)
```http
POST http://서버IP:5000/api/register
X-API-Key: HOSPITAL_SECRET_KEY_2024
Content-Type: application/json

{
  "patient_name": "홍길동",
  "department": "내과",
  "chart_number": "P2024-001234",
  "memo": "정기 방문"
}
```

### 방법 2: 비트컴퓨터 HIS 연동
비트컴퓨터는 접수 완료 시 외부 프로그램 실행 기능 지원.
설정 → 외부 프로그램 연동에서 `python his_call.py` 등록.

### 방법 3: 이지케어텍(EMR) 연동
이지케어텍은 Webhook/HTTP Call 기능 내장.
접수 이벤트에 `http://localhost:5000/api/register` 등록.

### 방법 4: DB 트리거
HIS DB에 직접 접근 가능한 경우:
```sql
-- MSSQL 예시
CREATE TRIGGER trg_patient_register
ON 접수테이블
AFTER INSERT
AS
BEGIN
  EXEC xp_cmdshell 'python C:\hospital\his_call.py'
END
```

---

## ⚙️ 설정 변경

`shared_store.py` 상단에서 진료과 목록 수정:
```python
DEPARTMENTS = [
    "내과", "외과", "정형외과", ...
]
```

API 키 변경 (환경변수 권장):
```bash
export HOSPITAL_API_KEY="새로운비밀키"
python api_server.py
```

---

## 📋 지원 진료과 (기본값)
내과, 외과, 정형외과, 소아과, 산부인과, 안과, 이비인후과,
피부과, 신경과, 정신건강의학과, 비뇨기과, 재활의학과
