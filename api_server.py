"""
api_server.py - 병원 HIS(Hospital Information System) 연동 REST API
실행: python api_server.py  (기본 포트: 5000)

외부 HIS 소프트웨어에서 이 API를 호출하여 환자 접수/상태 변경을 자동화합니다.

지원 HIS 예시:
- 비트컴퓨터 (BIT HIS)
- 이지케어텍 (ezCaretech)
- 유비케어 (U-BCAER)
- 포티즈 (Fortiz)
- 커스텀 EMR

연동 방식: HTTP REST API (JSON)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import hashlib
import hmac
import os
import sys

# shared_store 모듈 경로 추가
sys.path.insert(0, os.path.dirname(__file__))
import shared_store as store

app = Flask(__name__)
CORS(app)

# ── API 키 설정 (실제 운영 시 환경변수로 관리) ─────────────────
API_KEY = os.environ.get("HOSPITAL_API_KEY", "HOSPITAL_SECRET_KEY_2024")


def verify_api_key(req):
    """API 키 검증"""
    key = req.headers.get("X-API-Key") or req.args.get("api_key")
    return key == API_KEY


def error_response(message: str, code: int = 400):
    return jsonify({"success": False, "error": message}), code


def success_response(data: dict = None, message: str = "성공"):
    resp = {"success": True, "message": message}
    if data:
        resp["data"] = data
    return jsonify(resp), 200


# ── 헬스체크 ─────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health_check():
    """서버 상태 확인"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "service": "Hospital Queue API"
    }), 200


# ── 환자 접수 ─────────────────────────────────────────────────
@app.route("/api/register", methods=["POST"])
def register_patient():
    """
    환자 접수 API
    
    HIS에서 접수 완료 시 이 엔드포인트를 호출합니다.
    
    Request Headers:
        X-API-Key: your-api-key
    
    Request Body (JSON):
        {
            "patient_name": "홍길동",        # 필수: 환자 이름
            "department": "내과",             # 필수: 진료과 (DEPARTMENTS 목록 중)
            "chart_number": "P2024-001234",  # 선택: 차트번호 (내부 메모로만 저장, 화면 미표시)
            "memo": "혈압약 처방 필요"         # 선택: 추가 메모
        }
    
    Response:
        {
            "success": true,
            "message": "접수 완료",
            "data": {
                "patient_id": "1703123456789",
                "masked_name": "홍X동",
                "department": "내과",
                "wait_number": 3,
                "registered_at": "2024-01-15 09:30:00"
            }
        }
    """
    if not verify_api_key(request):
        return error_response("유효하지 않은 API 키입니다.", 401)

    data = request.get_json()
    if not data:
        return error_response("JSON 바디가 필요합니다.")

    name = data.get("patient_name", "").strip()
    department = data.get("department", "").strip()
    chart_number = data.get("chart_number", "")
    memo = data.get("memo", "")

    # 유효성 검사
    if not name:
        return error_response("patient_name이 필요합니다.")
    if len(name) < 2:
        return error_response("이름은 2글자 이상이어야 합니다.")
    if not department:
        return error_response("department가 필요합니다.")
    if department not in store.DEPARTMENTS:
        return error_response(f"유효하지 않은 진료과입니다. 가능한 진료과: {', '.join(store.DEPARTMENTS)}")

    # 내부 메모에 차트번호 포함 (화면에는 표시 안됨)
    internal_note = f"차트:{chart_number}" if chart_number else ""
    if memo:
        internal_note += f" | {memo}"

    patient = store.add_patient(name, department, internal_note)

    return success_response({
        "patient_id": patient["id"],
        "masked_name": patient["masked_name"],
        "department": patient["department"],
        "wait_number": patient["wait_number"],
        "registered_at": patient["registered_at"],
    }, "접수 완료")


# ── 환자 상태 변경 ────────────────────────────────────────────
@app.route("/api/status/<patient_id>", methods=["PUT"])
def update_status(patient_id: str):
    """
    환자 상태 변경 API
    
    Request Body:
        {
            "status": "진료중"  # 대기중 / 진료중 / 진료완료 / 부재
        }
    """
    if not verify_api_key(request):
        return error_response("유효하지 않은 API 키입니다.", 401)

    data = request.get_json()
    new_status = data.get("status", "")

    valid_statuses = [store.STATUS_WAITING, store.STATUS_CALLED, store.STATUS_DONE, store.STATUS_ABSENT]
    if new_status not in valid_statuses:
        return error_response(f"유효하지 않은 상태입니다. 가능: {', '.join(valid_statuses)}")

    queue = store.load_queue()
    target = next((p for p in queue if p["id"] == patient_id), None)
    if not target:
        return error_response("해당 환자를 찾을 수 없습니다.", 404)

    store.update_status(patient_id, new_status)
    return success_response({"patient_id": patient_id, "new_status": new_status}, "상태 변경 완료")


# ── 대기열 조회 ───────────────────────────────────────────────
@app.route("/api/queue", methods=["GET"])
def get_queue():
    """
    현재 대기열 조회 API
    
    Query Params:
        department: 특정 진료과 필터 (선택)
    """
    if not verify_api_key(request):
        return error_response("유효하지 않은 API 키입니다.", 401)

    department = request.args.get("department")
    queue = store.get_active_queue(department)

    # 이름은 마스킹해서 반환 (원본 이름은 API에서도 노출 안 함)
    safe_queue = []
    for p in queue:
        safe_queue.append({
            "patient_id": p["id"],
            "masked_name": p["masked_name"],
            "department": p["department"],
            "status": p["status"],
            "wait_number": p["wait_number"],
            "registered_at": p["registered_at"],
        })

    return success_response({"queue": safe_queue, "total": len(safe_queue)})


# ── 진료과 목록 ───────────────────────────────────────────────
@app.route("/api/departments", methods=["GET"])
def get_departments():
    """사용 가능한 진료과 목록"""
    return success_response({"departments": store.DEPARTMENTS})


# ── 통계 ──────────────────────────────────────────────────────
@app.route("/api/stats", methods=["GET"])
def get_stats():
    """진료과별 통계"""
    if not verify_api_key(request):
        return error_response("유효하지 않은 API 키입니다.", 401)

    stats = store.get_department_stats()
    return success_response({"stats": stats, "timestamp": datetime.now().isoformat()})


# ── 메인 ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("🏥 병원 대기현황 API 서버 시작")
    print("=" * 50)
    print(f"  API 서버:    http://0.0.0.0:5000")
    print(f"  헬스체크:    http://localhost:5000/health")
    print(f"  API 키:      {API_KEY[:8]}****")
    print()
    print("  엔드포인트:")
    print("    POST   /api/register      환자 접수")
    print("    PUT    /api/status/:id    상태 변경")
    print("    GET    /api/queue         대기열 조회")
    print("    GET    /api/departments   진료과 목록")
    print("    GET    /api/stats         통계")
    print("=" * 50)

    app.run(host="0.0.0.0", port=5000, debug=False)
