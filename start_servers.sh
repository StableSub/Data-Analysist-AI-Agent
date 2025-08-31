#!/bin/bash

# Data Analysis AI Agent 서버 시작 스크립트

echo "🚀 Data Analysis AI Agent 서버를 시작합니다..."

# 가상환경 활성화
echo "📦 가상환경을 활성화합니다..."
source ~/.virtualenvs/ai_agent/bin/activate

# 백엔드 서버 시작
echo "🔧 백엔드 서버를 시작합니다 (포트 8000)..."
python api.py &
BACKEND_PID=$!

# 잠시 대기
sleep 3

# 프론트엔드 서버 시작
echo "🎨 프론트엔드 서버를 시작합니다 (포트 3000)..."
cd frontend
npm start &
FRONTEND_PID=$!

echo ""
echo "✅ 서버가 성공적으로 시작되었습니다!"
echo "🌐 프론트엔드: http://localhost:3000"
echo "🔧 백엔드 API: http://localhost:8000"
echo "📚 API 문서: http://localhost:8000/docs"
echo ""
echo "서버를 중지하려면 Ctrl+C를 누르세요."

# 서버 종료 처리
trap "echo '🛑 서버를 종료합니다...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT

# 서버가 실행 중인 동안 대기
wait

