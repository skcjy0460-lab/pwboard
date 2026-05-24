"""
his_integration_example.py
━━━━━━━━━━━━━━━━━━━━━━━━━━
HIS 소프트웨어에서 대기현황판 API 호출 예제 코드

이 파일을 참고하여 기존 HIS 시스템에서 API를 연동하세요.
비트컴퓨터, 이지케어텍, 유비케어 등 어떤 HIS든
HTTP 요청이 가능하다면 연동 가능합니다.
"""

import requests
import json

# ─── 설정 ──────────────────────────────────────────────
API_BASE = "http://localhost:5000"        # API 서버 주소 (같은 PC면 localhost)
API_KEY  = "HOSPITAL_SECRET_KEY_2024"    # api_server.py의 API_KEY와 동일하게

HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY,
}


def test_health():
    """서버 연결 확인"""
    r = requests.get(f"{API_BASE}/health")
    print(f"[헬스체크] {r.json()}")


def register_patient_example():
    """
    ─── 환자 접수 예제 ─────────────────────────────────────
    HIS에서 접수 완료 이벤트 발생 시 이 함수를 호출하세요.
    
    차트번호(chart_number)는 내부 메모로만 저장되며
    환자용 화면에는 절대 표시되지 않습니다.
    """
    payload = {
        "patient_name": "박민지",
        "department": "내과",
        "chart_number": "P2024-001234",   # 내부 메모 (화면 미표시)
        "memo": "고혈압 정기 방문",
    }

    r = requests.post(
        f"{API_BASE}/api/register",
        headers=HEADERS,
        json=payload,
    )
    result = r.json()
    print(f"[접수 결과] {json.dumps(result, ensure_ascii=False, indent=2)}")

    if result["success"]:
        patient_id = result["data"]["patient_id"]
        print(f"  → 환자 ID: {patient_id}")
        print(f"  → 화면 표시 이름: {result['data']['masked_name']}")
        print(f"  → 대기 번호: {result['data']['wait_number']}번")
        return patient_id
    return None


def call_patient_example(patient_id: str):
    """
    ─── 진료실 호출 예제 ────────────────────────────────────
    의사가 진료실에서 다음 환자를 호출할 때 사용.
    EMR에서 '다음 환자' 버튼 클릭 시 이 API를 호출하세요.
    """
    r = requests.put(
        f"{API_BASE}/api/status/{patient_id}",
        headers=HEADERS,
        json={"status": "진료중"},
    )
    print(f"[진료 호출] {r.json()}")


def complete_patient_example(patient_id: str):
    """
    ─── 진료 완료 예제 ──────────────────────────────────────
    처방전 발행 또는 진료 완료 시 호출.
    """
    r = requests.put(
        f"{API_BASE}/api/status/{patient_id}",
        headers=HEADERS,
        json={"status": "진료완료"},
    )
    print(f"[진료 완료] {r.json()}")


def get_queue_example():
    """
    ─── 대기열 조회 예제 ────────────────────────────────────
    특정 진료과의 현재 대기 현황을 가져옵니다.
    """
    r = requests.get(
        f"{API_BASE}/api/queue",
        headers=HEADERS,
        params={"department": "내과"},
    )
    result = r.json()
    print(f"[내과 대기열] {json.dumps(result, ensure_ascii=False, indent=2)}")


# ─── HIS 소프트웨어별 연동 방식 안내 ──────────────────────────
HIS_INTEGRATION_GUIDE = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  HIS 소프트웨어별 연동 방법
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 방법 1: API 직접 연동 (추천)
  - HIS에서 HTTP POST 요청 지원 시 사용
  - POST http://[서버IP]:5000/api/register 호출
  - 헤더: X-API-Key: [설정한 API 키]
  
📌 방법 2: 데이터베이스 트리거 연동
  - HIS DB (MSSQL/Oracle/MySQL)에 트리거 추가
  - 접수 INSERT 시 Python 스크립트 실행
  - db_trigger_example.py 참고

📌 방법 3: 파일 감시 (폴링) 연동
  - HIS가 접수 시 CSV/TXT 파일 생성하는 경우
  - file_watcher.py로 파일 변경 감지 → API 호출

📌 방법 4: 화면 스크래핑 (최후 수단)
  - HIS API/DB 접근 불가 시
  - pyautogui + OCR로 HIS 화면에서 데이터 추출

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


if __name__ == "__main__":
    print(HIS_INTEGRATION_GUIDE)
    print("━━━ 연결 테스트 실행 ━━━")
    
    try:
        test_health()
        print()
        
        print("1. 환자 접수 테스트 (박민지 → 내과)")
        pid = register_patient_example()
        print()
        
        if pid:
            print("2. 진료 호출 테스트")
            call_patient_example(pid)
            print()

            print("3. 진료 완료 테스트")
            complete_patient_example(pid)
            print()

        print("4. 대기열 조회 테스트")
        get_queue_example()

    except requests.exceptions.ConnectionError:
        print("❌ API 서버에 연결할 수 없습니다.")
        print("   api_server.py를 먼저 실행해주세요: python api_server.py")
