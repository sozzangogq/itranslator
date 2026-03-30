import streamlit as st
import google.generativeai as genai
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import requests
import json

# [UI 설정]
st.set_page_config(page_title="'그' 말투 번역기 Pro", page_icon="💼", layout="wide")

# 사이드바
with st.sidebar:
    st.header("😭 직장인 서바이벌 가이드")
    st.markdown("1. 상사는 항상 옳다. (아니면 말고)\n2. 퇴근은 지능순이다.\n3. 이 앱을 켠 당신은 이미 일류.")
    st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM24xb3NnaXd0YndiaXUyamk5MXRxd20wamc5NnAzamN5amphYW9zdiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3ov9jS62h1f0vXfC9i/giphy.gif")

st.markdown("<h1 style='text-align: center; color: #1E1E1E;'>💼 '그' 말투 번역기 : Pro</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666;'>상사의 의도를 낱낱이 파헤치고, 완벽한 비즈니스 응답을 제조합니다.</p>", unsafe_allow_html=True)

# [설정 로드]
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(available_models[0]) if available_models else None
    slack_token = st.secrets["SLACK_BOT_TOKEN"]
    slack_client = WebClient(token=slack_token)
    slack_webhook_url = st.secrets.get("SLACK_WEBHOOK_URL", "")
except Exception as e:
    st.error(f"⚠️ 시스템 설정 확인 필요: {e}")

# 세션 상태 초기화
if "step" not in st.session_state:
    st.session_state.step = 1
if "decoded_full" not in st.session_state:
    st.session_state.decoded_full = ""
if "final_reply" not in st.session_state:
    st.session_state.final_reply = ""

# [기본 정보 입력]
with st.expander("🔑 연동 정보 설정", expanded=(st.session_state.step == 1)):
    c1, c2 = st.columns(2)
    with c1:
        channel_id = st.text_input("📍 채널 ID", placeholder="C로 시작하는 코드")
    with c2:
        user_id = st.text_input("👤 내 멤버 ID", placeholder="U로 시작하는 코드")

st.markdown("---")

# ---------------------------------------------------------
# [1단계: 메시지 해독] - 디테일 버전
# ---------------------------------------------------------
if st.session_state.step >= 1:
    st.markdown("### 🔍 STEP 1. 심층 메시지 해독")
    boss_msg = st.text_area("🤬 분석할 상사의 메시지:", placeholder="예: 이거 린하게 디벨롭 해보죠^^", height=100)
    
    if st.button("전문가 모드로 해독 시작 🧐"):
        if not boss_msg or not channel_id or not user_id:
            st.warning("연동 정보와 메시지를 입력해주세요!")
        else:
            with st.spinner("행간의 의미와 의도를 심층 분석 중..."):
                decode_prompt = f"""
                너는 20년 차 눈치 100단 비서실장이야. 아래 상사의 메시지를 분석해줘.
                [상사 메시지]: "{boss_msg}"
                
                출력 양식:
                🚨 **진짜 속뜻 (팩폭)**: (상사의 숨겨진 의도 1줄 요약)
                ✅ **Action Item (생존 지침)**: (사용자가 당장 해야 할 구체적인 행동 1~2개)
                """
                response = model.generate_content(decode_prompt)
                st.session_state.decoded_full = response.text
                st.session_state.step = 2 
                st.rerun()

if st.session_state.decoded_full:
    st.markdown("#### 🚩 AI의 심층 분석 결과")
    st.info(st.session_state.decoded_full)

# ---------------------------------------------------------
# [2단계: 답변 제조]
# ---------------------------------------------------------
if st.session_state.step == 2:
    st.markdown("---")
    st.markdown("### 🚀 STEP 2. 맞춤형 답변 생성")
    
    col_a, col_b = st.columns(2)
    with col_a:
        my_raw_reply = st.text_input("✍️ 내 본심 입력 (대충 써도 됨):", placeholder="예: 안됨, 내일 할게요, 확인했습니다")
    with col_b:
        filter_option = st.selectbox(
            "적용할 커뮤니케이션 필터:",
            [
                "✨ 초긍정 럭키비키 (원영사고)", 
                "🤔 논리중심 T발 (데이터 기반)", 
                "🫡 열정 신입사원 (패기)", 
                "🤫 쿨한 방관자 (무심한 프로)", 
                "💀 은은한 광기 (친절한 압박)"
            ]
        )

    if st.button("내 말투로 최종 답장 제조하기 ✨"):
        with st.spinner("슬랙 말투 학습 데이터 적용 중..."):
            try:
                # 슬랙 말투 수집
                result = slack_client.conversations_history(channel=channel_id, limit=40)
                my_style = "\n- ".join([m["text"] for m in result["messages"] if m.get("user") == user_id][:15])
                
                instructions = {
                    "✨ 초긍정 럭키비키 (원영사고)": "모든 상황을 초긍정적으로 해석. '오히려 좋아', '럭키비키' 필수.",
                    "🤔 논리중심 T발 (데이터 기반)": "감정을 완전히 배제하고 팩트와 수치 위주로 답변.",
                    "🫡 열정 신입사원 (패기)": "지나치게 열정적이고 씩씩한 신입사원 말투.",
                    "🤫 쿨한 방관자 (무심한 프로)": "무심하고 건조하게, 내 할 일만 하겠다는 느낌.",
                    "💀 은은한 광기 (친절한 압박)": "말투는 극도로 친절하나 묘하게 상대의 답변을 압박하는 느낌."
                }

                final_prompt = f"""
                너는 사용자의 슬랙 말투를 복제하는 AI 비서야. 
                1. [내 말투 데이터]: {my_style}
                2. [내 답변 본심]: {my_raw_reply}
                3. [필터 지시어]: {instructions[filter_option]}
                
                미션: 내 평소 말투의 특징(어미, 이모티콘 등)을 살리되, 위 필터 컨셉을 적용해서 상사에게 보낼 최종 답장을 만들어줘.
                결과는 딱 전송용 답장 내용만 1줄로 출력해.
                """
                
                response = model.generate_content(final_prompt)
                st.session_state.final_reply = response.text
                st.balloons()
            except Exception as e:
                st.error(f"오류: {e}")

if st.session_state.final_reply:
    st.markdown("#### 🏆 제안된 최종 답변")
    st.success(st.session_state.final_reply)
    
    cs1, cs2 = st.columns([1, 4])
    with cs1:
        if st.button("슬랙으로 전송"):
            requests.post(slack_webhook_url, json={"text": st.session_state.final_reply})
            st.toast("전송 완료! 이제 폰 끄세요.")
    with cs2:
        if st.button("처음부터 다시 하기 🔄"):
            st.session_state.step = 1
            st.session_state.decoded_full = ""
            st.session_state.final_reply = ""
            st.rerun()
