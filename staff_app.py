"""
staff_app.py - 원무과 직원용 환자 접수 및 대기 관리 툴
실행: streamlit run staff_app.py --server.port 8501
"""

import streamlit as st
import time
from datetime import datetime
import shared_store as store

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="원무과 대기 관리 시스템",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 전역 CSS ─────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap');

* { font-family: 'Noto Sans KR', sans-serif; }

/* 전체 배경 */
.stApp { background: #0F172A; color: #E2E8F0; }
section[data-testid="stSidebar"] { background: #1E293B; border-right: 1px solid #334155; }
section[data-testid="stSidebar"] * { color: #E2E8F0 !important; }

/* 헤더 */
.staff-header {
    background: linear-gradient(135deg, #1E3A5F 0%, #0F2940 100%);
    border: 1px solid #2563EB44;
    border-radius: 12px;
    padding: 20px 28px;
    margin-bottom: 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 4px 24px #2563EB22;
}
.staff-header h1 { margin: 0; font-size: 1.5rem; font-weight: 700; color: #BFDBFE; }
.staff-header .time-badge {
    background: #1D4ED8;
    color: #DBEAFE;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 0.9rem;
    font-weight: 500;
}

/* 카드 */
.stat-card {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
}
.stat-card .label { font-size: 0.75rem; color: #94A3B8; margin-bottom: 4px; }
.stat-card .value { font-size: 2rem; font-weight: 900; }

/* 접수 폼 */
.form-card {
    background: #1E293B;
    border: 1px solid #2563EB55;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 20px;
}
.form-card h3 { color: #93C5FD; margin-top: 0; font-size: 1.1rem; }

/* 대기자 테이블 */
.queue-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
}
.queue-table th {
    background: #0F172A;
    color: #64748B;
    font-weight: 500;
    padding: 10px 12px;
    text-align: left;
    border-bottom: 1px solid #334155;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.queue-table td {
    padding: 10px 12px;
    border-bottom: 1px solid #1E293B;
    color: #CBD5E1;
}
.queue-table tr:hover td { background: #1E293B55; }

/* 상태 뱃지 */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}
.badge-waiting  { background: #1D4ED822; color: #60A5FA; border: 1px solid #2563EB44; }
.badge-called   { background: #05966922; color: #34D399; border: 1px solid #10B98144; }
.badge-done     { background: #1E293B;   color: #475569; border: 1px solid #33415544; }
.badge-absent   { background: #7F1D1D22; color: #F87171; border: 1px solid #EF444444; }

/* 입력 필드 스타일 */
.stTextInput > div > div > input,
.stSelectbox > div > div > div {
    background: #0F172A !important;
    border: 1px solid #334155 !important;
    color: #E2E8F0 !important;
    border-radius: 8px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3px #2563EB22 !important;
}

/* 버튼 */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}
.stButton > button:hover { transform: translateY(-1px) !important; }

/* 구분선 */
hr { border-color: #334155 !important; }

/* 알림 */
.stSuccess { background: #05966922 !important; border: 1px solid #10B98155 !important; }
.stError   { background: #7F1D1D22 !important; border: 1px solid #EF444455 !important; }

/* 사이드바 선택 정보 */
.dept-stat-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    background: #0F172A;
    border-radius: 8px;
    margin: 4px 0;
    font-size: 0.85rem;
}
.dept-stat-row .dept-name { color: #CBD5E1; }
.dept-stat-row .dept-count { color: #60A5FA; font-weight: 700; }

/* 라이브 도트 */
.live-dot {
    display: inline-block;
    width: 8px; height: 8px;
    background: #10B981;
    border-radius: 50%;
    margin-right: 6px;
    animation: pulse-dot 1.4s infinite;
}
@keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.4; transform: scale(0.8); }
}
</style>
""", unsafe_allow_html=True)


# ── 세션 상태 초기화 ─────────────────────────────────────────
if "selected_dept_filter" not in st.session_state:
    st.session_state.selected_dept_filter = "전체"
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()
if "msg" not in st.session_state:
    st.session_state.msg = None  # {"type": "success"/"error", "text": "..."}


# ── 헬퍼 함수 ────────────────────────────────────────────────
def status_badge(status: str) -> str:
    cls_map = {
        store.STATUS_WAITING: "waiting",
        store.STATUS_CALLED:  "called",
        store.STATUS_DONE:    "done",
        store.STATUS_ABSENT:  "absent",
    }
    cls = cls_map.get(status, "done")
    return f'<span class="badge badge-{cls}">{status}</span>'


def render_header():
    now = datetime.now().strftime("%Y년 %m월 %d일  %H:%M:%S")
    st.markdown(f"""
    <div class="staff-header">
        <div>
            <h1>🏥 원무과 대기 관리 시스템</h1>
            <div style="color:#64748B;font-size:0.8rem;margin-top:4px;">
                <span class="live-dot"></span>실시간 운영 중 · 환자용 화면과 자동 동기화
            </div>
        </div>
        <div class="time-badge">🕐 {now}</div>
    </div>
    """, unsafe_allow_html=True)


# ── 사이드바 ─────────────────────────────────────────────────
def render_sidebar():
    st.sidebar.markdown("## 📋 진료과 현황")

    stats = store.get_department_stats()
    all_waiting = sum(v["waiting"] for v in stats.values())
    all_called  = sum(v["called"]  for v in stats.values())

    st.sidebar.markdown(f"""
    <div style="background:#0F172A;border-radius:10px;padding:14px;margin-bottom:12px;">
        <div style="color:#94A3B8;font-size:0.75rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px;">전체 현황</div>
        <div style="display:flex;gap:16px;">
            <div style="text-align:center;">
                <div style="font-size:1.8rem;font-weight:900;color:#60A5FA;">{all_waiting}</div>
                <div style="font-size:0.7rem;color:#64748B;">대기중</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:1.8rem;font-weight:900;color:#34D399;">{all_called}</div>
                <div style="font-size:0.7rem;color:#64748B;">진료중</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 진료과 필터
    options = ["전체"] + store.DEPARTMENTS
    for opt in options:
        if opt == "전체":
            count_text = f"대기 {all_waiting}"
            active = st.session_state.selected_dept_filter == "전체"
        else:
            w = stats[opt]["waiting"]
            c = stats[opt]["called"]
            count_text = f"대기 {w} · 진료 {c}"
            active = st.session_state.selected_dept_filter == opt

        bg = "#1D4ED833" if active else "transparent"
        border = "#2563EB" if active else "transparent"

        if st.sidebar.button(
            f"{'✦ ' if active else '　'}{opt}  ({count_text})",
            key=f"dept_btn_{opt}",
            use_container_width=True
        ):
            st.session_state.selected_dept_filter = opt
            st.rerun()

    st.sidebar.divider()
    st.sidebar.markdown("### ⚙️ 도구")
    if st.sidebar.button("🔄 완료 환자 전체 삭제", use_container_width=True):
        queue = store.load_queue()
        queue = [p for p in queue if p["status"] not in (store.STATUS_DONE, store.STATUS_ABSENT)]
        store.save_queue(queue)
        st.session_state.msg = {"type": "success", "text": "완료/부재 환자를 모두 삭제했습니다."}
        st.rerun()

    if st.sidebar.button("🗑️ 전체 초기화", use_container_width=True, type="secondary"):
        store.save_queue([])
        st.session_state.msg = {"type": "success", "text": "대기열을 전체 초기화했습니다."}
        st.rerun()

    st.sidebar.divider()
    st.sidebar.markdown("""
    <div style="font-size:0.72rem;color:#475569;line-height:1.6;">
    <b style="color:#64748B;">📡 연동 안내</b><br>
    환자용 화면 주소:<br>
    <code style="color:#60A5FA;">http://[서버IP]:8502</code><br><br>
    데이터 파일 위치:<br>
    <code style="color:#94A3B8;">./data/queue.json</code><br><br>
    HIS 연동 API:<br>
    <code style="color:#94A3B8;">POST /api/register</code>
    </div>
    """, unsafe_allow_html=True)


# ── 접수 폼 ───────────────────────────────────────────────────
def render_registration_form():
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    st.markdown("### ➕ 환자 접수")

    col1, col2, col3, col4 = st.columns([2, 2, 3, 1])

    with col1:
        name = st.text_input("환자 이름 *", placeholder="예: 박민지", key="reg_name")
    with col2:
        dept = st.selectbox("진료과 *", store.DEPARTMENTS, key="reg_dept")
    with col3:
        note = st.text_input("내부 메모 (선택)", placeholder="차트번호·특이사항 등 내부용 (화면 미표시)", key="reg_note")
    with col4:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        submit = st.button("📋 접수", type="primary", use_container_width=True)

    if submit:
        name_clean = name.strip()
        if not name_clean:
            st.error("⚠️ 환자 이름을 입력해주세요.")
        elif len(name_clean) < 2:
            st.error("⚠️ 이름은 2글자 이상 입력해주세요.")
        else:
            patient = store.add_patient(name_clean, dept, note)
            masked = store.mask_name(name_clean)
            st.session_state.msg = {
                "type": "success",
                "text": f"✅ [{dept}] {masked} 님이 접수되었습니다. (대기번호 {patient['wait_number']}번)"
            }
            # 입력 필드 초기화
            for key in ["reg_name", "reg_note"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ── 대기열 테이블 ─────────────────────────────────────────────
def render_queue_table():
    dept_filter = st.session_state.selected_dept_filter

    if dept_filter == "전체":
        queue = store.get_active_queue()
        title = "전체 대기 현황"
    else:
        queue = store.get_active_queue(dept_filter)
        title = f"{dept_filter} 대기 현황"

    # 정렬: 진료중 → 대기중 순, 접수시간 순
    status_order = {store.STATUS_CALLED: 0, store.STATUS_WAITING: 1}
    queue.sort(key=lambda p: (status_order.get(p["status"], 9), p["registered_at"]))

    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
        <h3 style="margin:0;color:#93C5FD;font-size:1.05rem;">📋 {title}</h3>
        <span style="color:#475569;font-size:0.8rem;">총 {len(queue)}명</span>
    </div>
    """, unsafe_allow_html=True)

    if not queue:
        st.markdown("""
        <div style="text-align:center;padding:40px;color:#334155;border:1px dashed #334155;border-radius:10px;">
            현재 대기 중인 환자가 없습니다
        </div>
        """, unsafe_allow_html=True)
        return

    # 테이블 헤더
    header_cols = st.columns([0.5, 1.2, 1.5, 1, 1.2, 1.2, 2])
    headers = ["순번", "이름(표시)", "진료과", "상태", "접수시간", "호출시간", "액션"]
    for col, h in zip(header_cols, headers):
        col.markdown(f"<div style='color:#475569;font-size:0.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;padding:4px 0;border-bottom:1px solid #334155;'>{h}</div>", unsafe_allow_html=True)

    for i, p in enumerate(queue):
        cols = st.columns([0.5, 1.2, 1.5, 1, 1.2, 1.2, 2])

        with cols[0]:
            st.markdown(f"<div style='padding:10px 0;color:#475569;font-size:0.85rem;'>{i+1}</div>", unsafe_allow_html=True)
        with cols[1]:
            st.markdown(f"<div style='padding:10px 0;color:#E2E8F0;font-weight:600;font-size:0.95rem;'>{p['masked_name']}</div>", unsafe_allow_html=True)
        with cols[2]:
            st.markdown(f"<div style='padding:10px 0;color:#94A3B8;'>{p['department']}</div>", unsafe_allow_html=True)
        with cols[3]:
            st.markdown(f"<div style='padding:6px 0;'>{status_badge(p['status'])}</div>", unsafe_allow_html=True)
        with cols[4]:
            t = p['registered_at'][11:16] if p['registered_at'] else "-"
            st.markdown(f"<div style='padding:10px 0;color:#64748B;font-size:0.82rem;'>{t}</div>", unsafe_allow_html=True)
        with cols[5]:
            t = p['called_at'][11:16] if p['called_at'] else "-"
            st.markdown(f"<div style='padding:10px 0;color:#64748B;font-size:0.82rem;'>{t}</div>", unsafe_allow_html=True)
        with cols[6]:
            btn_cols = st.columns([1, 1, 1])
            with btn_cols[0]:
                if p["status"] == store.STATUS_WAITING:
                    if st.button("📢 호출", key=f"call_{p['id']}", use_container_width=True):
                        store.update_status(p["id"], store.STATUS_CALLED)
                        st.session_state.msg = {"type": "success", "text": f"📢 {p['masked_name']} 님을 호출했습니다."}
                        st.rerun()
                elif p["status"] == store.STATUS_CALLED:
                    if st.button("✅ 완료", key=f"done_{p['id']}", use_container_width=True):
                        store.update_status(p["id"], store.STATUS_DONE)
                        st.rerun()
            with btn_cols[1]:
                if p["status"] == store.STATUS_WAITING:
                    if st.button("🔔 재호출", key=f"recall_{p['id']}", use_container_width=True):
                        store.update_status(p["id"], store.STATUS_CALLED)
                        st.session_state.msg = {"type": "success", "text": f"🔔 {p['masked_name']} 님을 재호출했습니다."}
                        st.rerun()
            with btn_cols[2]:
                if st.button("❌", key=f"del_{p['id']}", use_container_width=True, help="부재/취소 처리"):
                    store.update_status(p["id"], store.STATUS_ABSENT)
                    st.session_state.msg = {"type": "success", "text": f"❌ {p['masked_name']} 님을 부재 처리했습니다."}
                    st.rerun()

        st.markdown("<hr style='margin:0;border-color:#1E293B;'>", unsafe_allow_html=True)


# ── 메인 ──────────────────────────────────────────────────────
def main():
    render_header()
    render_sidebar()

    # 알림 메시지
    if st.session_state.msg:
        m = st.session_state.msg
        if m["type"] == "success":
            st.success(m["text"])
        else:
            st.error(m["text"])
        st.session_state.msg = None

    render_registration_form()
    render_queue_table()

    # 자동 새로고침 (10초마다)
    st.markdown("""
    <div style="text-align:right;color:#334155;font-size:0.72rem;margin-top:20px;">
        🔄 10초마다 자동 갱신
    </div>
    """, unsafe_allow_html=True)
    time.sleep(10)
    st.rerun()


if __name__ == "__main__":
    main()
