"""
patient_display.py - 환자용 대기현황판
실행: streamlit run patient_display.py --server.port 8502

원내 TV/모니터에 띄우는 화면입니다.
- 차트번호 미표시
- 이름 마스킹 처리 (박X지)
- 3초마다 자동 갱신
- 진료과별 탭 자동 슬라이드
"""

import streamlit as st
import time
from datetime import datetime
import shared_store as store

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="진료 대기현황",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── 전역 CSS (대형 디스플레이 최적화) ──────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap');

* { font-family: 'Noto Sans KR', sans-serif !important; box-sizing: border-box; }

/* 배경 - 병원 느낌의 깔끔한 다크 블루 */
.stApp {
    background: linear-gradient(160deg, #040D1F 0%, #071428 50%, #040D1F 100%);
    color: #E2E8F0;
}

/* 사이드바 숨김 */
section[data-testid="stSidebar"] { display: none !important; }
header[data-testid="stHeader"] { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* 최상단 헤더 바 */
.display-header {
    background: linear-gradient(90deg, #0A1628 0%, #0D1F3C 50%, #0A1628 100%);
    border-bottom: 2px solid #1D4ED8;
    padding: 18px 40px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: sticky;
    top: 0;
    z-index: 100;
}
.hospital-name {
    font-size: 1.6rem;
    font-weight: 900;
    color: #BFDBFE;
    letter-spacing: -0.02em;
}
.hospital-sub {
    font-size: 0.85rem;
    color: #3B82F6;
    margin-top: 2px;
    letter-spacing: 0.08em;
}
.header-right {
    text-align: right;
}
.current-time {
    font-size: 2rem;
    font-weight: 700;
    color: #DBEAFE;
    font-variant-numeric: tabular-nums;
    letter-spacing: 0.04em;
}
.current-date {
    font-size: 0.85rem;
    color: #64748B;
}

/* 라이브 인디케이터 */
.live-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #05966922;
    border: 1px solid #10B98144;
    color: #34D399;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}
.live-dot {
    width: 8px; height: 8px;
    background: #10B981;
    border-radius: 50%;
    animation: pulse 1.4s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.3; transform: scale(0.7); }
}

/* 진료과 탭 */
.dept-tabs {
    display: flex;
    gap: 8px;
    padding: 16px 32px 0;
    border-bottom: 1px solid #1E293B;
    overflow-x: auto;
    background: #040D1F;
}
.dept-tab {
    padding: 10px 20px;
    border-radius: 8px 8px 0 0;
    cursor: pointer;
    font-weight: 600;
    font-size: 0.9rem;
    white-space: nowrap;
    transition: all 0.2s;
    border: 1px solid transparent;
    border-bottom: none;
    color: #475569;
}
.dept-tab:hover { color: #94A3B8; background: #0F172A; }
.dept-tab.active {
    background: #0F172A;
    color: #60A5FA;
    border-color: #1D4ED8;
    border-bottom: 1px solid #0F172A;
}
.dept-tab .badge-count {
    display: inline-block;
    background: #1D4ED8;
    color: #BFDBFE;
    border-radius: 12px;
    padding: 1px 8px;
    font-size: 0.72rem;
    margin-left: 6px;
}

/* 메인 콘텐츠 영역 */
.main-content { padding: 24px 32px; }

/* 진료중 섹션 */
.section-title {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-weight: 700;
    margin-bottom: 12px;
    padding-left: 4px;
}
.calling-section .section-title { color: #10B981; }
.waiting-section .section-title { color: #3B82F6; }

/* 진료중 카드 (크고 눈에 띄게) */
.calling-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 12px;
    margin-bottom: 28px;
}
.calling-card {
    background: linear-gradient(135deg, #064E3B 0%, #065F46 100%);
    border: 1px solid #10B98155;
    border-radius: 12px;
    padding: 18px 20px;
    text-align: center;
    position: relative;
    overflow: hidden;
    animation: callPulse 2s ease-in-out infinite;
}
.calling-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #10B981, #34D399, #10B981);
    animation: shimmer 2s infinite;
    background-size: 200% 100%;
}
@keyframes callPulse {
    0%, 100% { box-shadow: 0 0 0 0 #10B98100; }
    50%       { box-shadow: 0 0 20px 4px #10B98133; }
}
@keyframes shimmer {
    0%   { background-position: -200% 0; }
    100% { background-position:  200% 0; }
}
.calling-label {
    font-size: 0.7rem;
    color: #6EE7B7;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.calling-name {
    font-size: 2rem;
    font-weight: 900;
    color: #ECFDF5;
    letter-spacing: -0.02em;
    line-height: 1.1;
}
.calling-dept {
    font-size: 0.78rem;
    color: #6EE7B7;
    margin-top: 6px;
}

/* 대기자 그리드 */
.waiting-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 10px;
}
.waiting-card {
    background: #0F172A;
    border: 1px solid #1E3A5F;
    border-radius: 10px;
    padding: 14px 16px;
    text-align: center;
    transition: all 0.3s;
    position: relative;
}
.waiting-card:hover {
    border-color: #2563EB44;
    background: #0F1F3A;
}
.waiting-number {
    font-size: 0.65rem;
    color: #334155;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.waiting-name {
    font-size: 1.4rem;
    font-weight: 700;
    color: #93C5FD;
    letter-spacing: -0.01em;
}
.waiting-time {
    font-size: 0.7rem;
    color: #334155;
    margin-top: 6px;
}

/* 빈 상태 */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #1E3A5F;
}
.empty-state .icon { font-size: 3rem; margin-bottom: 12px; }
.empty-state .text { font-size: 1rem; }

/* 하단 안내 바 */
.footer-bar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: #0A1628;
    border-top: 1px solid #1E293B;
    padding: 10px 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    z-index: 100;
}
.footer-notice {
    color: #334155;
    font-size: 0.78rem;
}
.footer-notice span {
    color: #1D4ED8;
    margin-right: 4px;
}
.refresh-info {
    color: #334155;
    font-size: 0.72rem;
}

/* 전체 통계 바 */
.stats-bar {
    display: flex;
    gap: 24px;
    padding: 12px 32px;
    background: #040D1F;
    border-bottom: 1px solid #0F172A;
}
.stat-item { text-align: center; }
.stat-item .num { font-size: 1.4rem; font-weight: 800; }
.stat-item .lbl { font-size: 0.65rem; color: #334155; text-transform: uppercase; letter-spacing: 0.08em; }
.stat-waiting .num { color: #3B82F6; }
.stat-calling .num { color: #10B981; }

/* 구분선 */
.section-divider {
    height: 1px;
    background: #1E293B;
    margin: 20px 0;
}
</style>
""", unsafe_allow_html=True)


# ── 현재 시각 표시 ────────────────────────────────────────────
def render_header():
    now = datetime.now()
    time_str = now.strftime("%H:%M:%S")
    date_str = now.strftime("%Y년 %m월 %d일 (%a)")

    # 요일 한글화
    weekday_map = {"Mon":"월","Tue":"화","Wed":"수","Thu":"목","Fri":"금","Sat":"토","Sun":"일"}
    for eng, kor in weekday_map.items():
        date_str = date_str.replace(f"({eng})", f"({kor})")

    st.markdown(f"""
    <div class="display-header">
        <div>
            <div class="hospital-name">🏥 진료 대기현황</div>
            <div class="hospital-sub">PATIENT WAITING STATUS</div>
        </div>
        <div style="display:flex;align-items:center;gap:20px;">
            <div class="live-badge">
                <div class="live-dot"></div>
                LIVE
            </div>
            <div class="header-right">
                <div class="current-time">{time_str}</div>
                <div class="current-date">{date_str}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── 전체 통계 바 ──────────────────────────────────────────────
def render_stats_bar(queue: list):
    waiting_count = len([p for p in queue if p["status"] == store.STATUS_WAITING])
    calling_count = len([p for p in queue if p["status"] == store.STATUS_CALLED])

    # 활성 진료과 수
    depts = set(p["department"] for p in queue)

    st.markdown(f"""
    <div class="stats-bar">
        <div class="stat-item stat-waiting">
            <div class="num">{waiting_count}</div>
            <div class="lbl">전체 대기</div>
        </div>
        <div class="stat-item stat-calling">
            <div class="num">{calling_count}</div>
            <div class="lbl">진료 중</div>
        </div>
        <div class="stat-item" style="margin-left:auto;">
            <div class="num" style="color:#475569;">{len(depts)}</div>
            <div class="lbl">운영 진료과</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── 진료과별 대기현황 렌더링 ──────────────────────────────────
def render_department(dept: str, patients: list):
    calling = [p for p in patients if p["status"] == store.STATUS_CALLED]
    waiting = [p for p in patients if p["status"] == store.STATUS_WAITING]

    # 진료중 환자
    if calling:
        cards_html = ""
        for p in calling:
            cards_html += f"""
            <div class="calling-card">
                <div class="calling-label">📢 진료 중</div>
                <div class="calling-name">{p['masked_name']}</div>
                <div class="calling-dept">{p['department']}</div>
            </div>
            """
        st.markdown(f"""
        <div class="calling-section" style="margin-bottom:20px;">
            <div class="section-title">📢 현재 진료 중</div>
            <div class="calling-grid">{cards_html}</div>
        </div>
        """, unsafe_allow_html=True)

    # 대기 중 환자
    if waiting:
        cards_html = ""
        for i, p in enumerate(waiting):
            reg_time = p['registered_at'][11:16] if p['registered_at'] else ""
            cards_html += f"""
            <div class="waiting-card">
                <div class="waiting-number">대기 {i+1}번</div>
                <div class="waiting-name">{p['masked_name']}</div>
                <div class="waiting-time">접수 {reg_time}</div>
            </div>
            """
        st.markdown(f"""
        <div class="waiting-section">
            <div class="section-title">🕐 대기 중 ({len(waiting)}명)</div>
            <div class="waiting-grid">{cards_html}</div>
        </div>
        """, unsafe_allow_html=True)

    if not calling and not waiting:
        st.markdown("""
        <div class="empty-state">
            <div class="icon">✓</div>
            <div class="text">현재 대기 환자가 없습니다</div>
        </div>
        """, unsafe_allow_html=True)


# ── 메인 ──────────────────────────────────────────────────────
def main():
    render_header()

    queue = store.get_active_queue()
    render_stats_bar(queue)

    # 운영 중인 진료과만 표시 (대기자 있는 과)
    active_depts = []
    dept_map = {}
    for dept in store.DEPARTMENTS:
        dept_patients = [p for p in queue if p["department"] == dept]
        if dept_patients:
            active_depts.append(dept)
            dept_map[dept] = dept_patients

    if not active_depts:
        st.markdown("""
        <div style="text-align:center;padding:80px 20px;">
            <div style="font-size:4rem;margin-bottom:16px;">🏥</div>
            <div style="font-size:1.2rem;color:#1E3A5F;">현재 접수된 환자가 없습니다</div>
            <div style="font-size:0.85rem;color:#1E293B;margin-top:8px;">원무과에서 접수 후 이 화면에 표시됩니다</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Streamlit 탭으로 진료과별 표시
        tab_labels = []
        for dept in active_depts:
            pts = dept_map[dept]
            waiting_n = len([p for p in pts if p["status"] == store.STATUS_WAITING])
            calling_n = len([p for p in pts if p["status"] == store.STATUS_CALLED])
            label = f"{dept}"
            if calling_n > 0:
                label += f" 🟢{calling_n}"
            if waiting_n > 0:
                label += f" 🔵{waiting_n}"
            tab_labels.append(label)

        tabs = st.tabs(tab_labels)

        for tab, dept in zip(tabs, active_depts):
            with tab:
                st.markdown('<div class="main-content">', unsafe_allow_html=True)
                render_department(dept, dept_map[dept])
                st.markdown('</div>', unsafe_allow_html=True)

    # 하단 안내 바
    st.markdown("""
    <div class="footer-bar">
        <div class="footer-notice">
            <span>ℹ</span> 이름 가운데 별표(X)는 개인정보 보호를 위한 마스킹 처리입니다 &nbsp;|&nbsp;
            <span>🔔</span> 호명 시 신속히 진료실로 입장해 주세요
        </div>
        <div class="refresh-info">🔄 3초마다 자동 갱신</div>
    </div>
    <div style="height:50px;"></div>
    """, unsafe_allow_html=True)

    # 3초마다 자동 새로고침
    time.sleep(3)
    st.rerun()


if __name__ == "__main__":
    main()
