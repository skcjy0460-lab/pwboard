"""
shared_store.py - 공유 데이터 저장소 (JSON 파일 기반 실시간 동기화)
병원 대기현황판 시스템의 핵심 데이터 레이어
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path

# 데이터 파일 경로 (같은 서버에서 두 앱이 공유)
DATA_DIR = Path(__file__).parent / "data"
QUEUE_FILE = DATA_DIR / "queue.json"
LOG_FILE = DATA_DIR / "audit_log.json"

# 진료과 목록
DEPARTMENTS = [
    "내과",
    "외과",
    "정형외과",
    "소아과",
    "산부인과",
    "안과",
    "이비인후과",
    "피부과",
    "신경과",
    "정신건강의학과",
    "비뇨기과",
    "재활의학과",
]

# 상태 정의
STATUS_WAITING = "대기중"
STATUS_CALLED = "진료중"
STATUS_DONE = "진료완료"
STATUS_ABSENT = "부재"

STATUS_COLORS = {
    STATUS_WAITING: "#3B82F6",
    STATUS_CALLED: "#10B981",
    STATUS_DONE: "#6B7280",
    STATUS_ABSENT: "#EF4444",
}


def ensure_data_dir():
    """데이터 디렉토리 및 파일 초기화"""
    DATA_DIR.mkdir(exist_ok=True)
    if not QUEUE_FILE.exists():
        save_queue([])
    if not LOG_FILE.exists():
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False)


def load_queue() -> list:
    """대기열 불러오기"""
    ensure_data_dir()
    try:
        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_queue(queue: list):
    """대기열 저장"""
    ensure_data_dir()
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)


def mask_name(name: str) -> str:
    """
    환자 이름 마스킹 처리
    - 2글자: 첫글자 + X  (예: 김철 → 김X)
    - 3글자: 첫글자 + X + 마지막글자  (예: 박민지 → 박X지)
    - 4글자 이상: 첫글자 + XX + 마지막글자  (예: 남궁민수 → 남XX수)
    """
    name = name.strip()
    if len(name) == 0:
        return ""
    if len(name) == 1:
        return name
    if len(name) == 2:
        return name[0] + "X"
    if len(name) == 3:
        return name[0] + "X" + name[2]
    # 4글자 이상
    return name[0] + "X" * (len(name) - 2) + name[-1]


def add_patient(name: str, department: str, chart_note: str = "") -> dict:
    """
    환자 접수 추가
    chart_note: 내부 메모용 (화면에 표시 안됨)
    """
    queue = load_queue()

    # 해당 진료과의 현재 대기번호 계산
    dept_patients = [p for p in queue if p["department"] == department and p["status"] != STATUS_DONE]
    wait_number = len([p for p in dept_patients if p["status"] == STATUS_WAITING]) + 1

    patient = {
        "id": f"{int(time.time() * 1000)}",  # 밀리초 타임스탬프를 ID로
        "name": name,
        "masked_name": mask_name(name),
        "department": department,
        "status": STATUS_WAITING,
        "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "called_at": None,
        "done_at": None,
        "wait_number": wait_number,
        "note": chart_note,  # 내부 메모 (환자 화면에 미표시)
    }

    queue.append(patient)
    save_queue(queue)
    _add_log("접수", name, department)
    return patient


def update_status(patient_id: str, new_status: str):
    """환자 상태 변경"""
    queue = load_queue()
    for p in queue:
        if p["id"] == patient_id:
            p["status"] = new_status
            if new_status == STATUS_CALLED:
                p["called_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            elif new_status in (STATUS_DONE, STATUS_ABSENT):
                p["done_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            _add_log(new_status, p["name"], p["department"])
            break
    save_queue(queue)


def remove_patient(patient_id: str):
    """환자 대기열에서 제거"""
    queue = load_queue()
    queue = [p for p in queue if p["id"] != patient_id]
    save_queue(queue)


def get_active_queue(department: str = None) -> list:
    """진료완료 제외한 활성 대기열 반환"""
    queue = load_queue()
    active = [p for p in queue if p["status"] != STATUS_DONE and p["status"] != STATUS_ABSENT]
    if department:
        active = [p for p in active if p["department"] == department]
    return active


def get_department_stats() -> dict:
    """진료과별 통계"""
    queue = load_queue()
    stats = {}
    for dept in DEPARTMENTS:
        dept_q = [p for p in queue if p["department"] == dept]
        stats[dept] = {
            "waiting": len([p for p in dept_q if p["status"] == STATUS_WAITING]),
            "called": len([p for p in dept_q if p["status"] == STATUS_CALLED]),
            "done": len([p for p in dept_q if p["status"] == STATUS_DONE]),
            "absent": len([p for p in dept_q if p["status"] == STATUS_ABSENT]),
        }
    return stats


def _add_log(action: str, name: str, department: str):
    """감사 로그 기록"""
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)
    except Exception:
        logs = []

    logs.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "masked_name": mask_name(name),
        "department": department,
    })

    # 최근 500건만 보관
    logs = logs[-500:]
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


def get_file_mtime() -> float:
    """queue.json 최종 수정시간 반환 (변경감지용)"""
    try:
        return QUEUE_FILE.stat().st_mtime
    except FileNotFoundError:
        return 0.0
