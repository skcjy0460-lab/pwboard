#!/usr/bin/env bash
# start_all.sh - 전체 시스템 한번에 실행 (Linux/Mac)
# 실행: chmod +x start_all.sh && ./start_all.sh

echo "=============================================="
echo "   🏥 병원 대기현황판 시스템 시작"
echo "=============================================="

# 데이터 디렉토리 생성
mkdir -p data

# 패키지 설치
pip install -r requirements.txt -q

# 1. 직원용 앱 (포트 8501)
echo "▶ 직원용 앱 시작 (포트 8501)..."
streamlit run staff_app.py --server.port 8501 --server.headless true &
STAFF_PID=$!

# 2. 환자용 앱 (포트 8502)
echo "▶ 환자용 대기현황판 시작 (포트 8502)..."
streamlit run patient_display.py --server.port 8502 --server.headless true &
PATIENT_PID=$!

# 3. API 서버 (포트 5000)
echo "▶ HIS 연동 API 서버 시작 (포트 5000)..."
python api_server.py &
API_PID=$!

echo ""
echo "=============================================="
echo "   ✅ 모든 서비스 실행 완료"
echo "=============================================="
echo ""
echo "  🖥️  직원용 (원무과):  http://localhost:8501"
echo "  📺  환자용 (대기현황): http://localhost:8502"
echo "  🔌  HIS 연동 API:     http://localhost:5000"
echo ""
echo "  종료하려면 Ctrl+C 를 누르세요"
echo "=============================================="

# Ctrl+C 시 모든 프로세스 종료
trap "echo '시스템 종료 중...'; kill $STAFF_PID $PATIENT_PID $API_PID 2>/dev/null; exit 0" INT

wait
