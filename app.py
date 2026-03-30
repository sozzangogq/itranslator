import streamlit as st
import google.generativeai as genai
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import requests
import json

# [UI 설정]
st.set_page_config(page_title="'그' 말투 번역기 Professional", page_icon="💼", layout="wide")

# 사이드바
with st.sidebar:
    st.header("😭 직장인 서바이벌 가이드")
    st.markdown("1. 꺾이지 않는 마음(퇴사)\n2. 중꺾그마(그냥 하는 마음)")
    st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM24xb3NnaXd0YndiaXUyamk5MXRxd20wamc5NnAzamN5amphYW9zdiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3ov9jS62h1f0vXfC9i/giphy.gif")

st.markdown("<h1 style='text-align: center; color: #1E1E1E;'>💼 '그' 말투 번역기 : Pro</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666;'>상사의 의도를 정확히 파악하고, 최적화된 비즈니스 응답을 생성합니다.</p>", unsafe_allow_html=True)

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

# 세션 상태 초기화 (단계별 진행을 위해)
if "step" not in st.session_state:
    st.session_state.step = 1
if "decoded_text" not in st.session_state:
    st.session_state.decoded_text = ""
if "final_reply" not in st.session_state:
    st.session_state.final_reply = ""

# [기본 정보 입력]
with st.expander("🔑 연동 정보 설정 (최초 1회)", expanded=(st.session_state.step == 1)):
    c1, c2 = st.columns(2)
    with c1:
        channel_id = st.text_input("📍 채널 ID", placeholder="C로 시작하는 코드")
    with c2:
        user_id = st.text_input("👤 내 멤버 ID", placeholder="U로 시작하는 코드")

st.markdown("---")

# ---------------------------------------------------------
# [1단계: 메시지 해독]
# ---------------------------------------------------------
if st.session_state.step >= 1:
    st.markdown("### 🔍 STEP 1. 메시지 해독")
    boss_msg = st.text_area("🤬 분석할 상사의 메시지:", placeholder="예: 이거 린하게 디벨롭 해보죠^^", height=100)
    
    if st.button("해독 시작 🧐"):
        if not boss_msg or not channel_id or not user_id:
            st.warning("연동 정보와 메시지를 입력해주세요!")
        else:
            with st.spinner("AI가 행간의 의미를 분석 중..."):
                decode_prompt = f"너는 눈치 100단 직장인이야. 다음 메시지의 숨겨진 진짜 의도를 팩트 폭격 수준으로 한 줄 요약해줘: '{boss_msg}'"
                response = model.generate_content(decode_prompt)
                st.session_state.decoded_text = response.text
                st.session_state.step = 2 # 2단계로 이동
                st.rerun()

if st.session_state.decoded_text:
    st.info(f"🚨 **상사의 속뜻:** {st.session_state.decoded_text}")

# ---------------------------------------------------------
# [2단계: 답변 제조]
# ---------------------------------------------------------
if st.session_state.step == 2:
    st.markdown("---")
    st.markdown("### 🚀 STEP 2. 맞춤형 답변 생성")
    
    col_a, col_b = st.columns(2)
    with col_a:
        my_raw_reply = st.text_input("✍️ 내 본심 입력 (대충):", placeholder="예: 안됨, 내일함, 확인")
    with col_b:
        filter_option = st.selectbox(
            "적용할 커뮤니케이션 필터:",
            [
                "✨ 초긍정 럭키비키 (원영사고)", 
                "🤔 논리중심 T발 (데이터 기반)", 
                "🫡 열정 신입사원 (패기)", 
                "🤫 쿨한 방관자 (알빠노)", 
                "💀 은은한 광기 (친절한 압박)"
            ]
        )

    if st.button("최종 답장 제조하기 ✨"):
        with st.spinner("내 말투 학습 및 필터 적용 중..."):
            try:
                # 슬랙 말투 수집
                result = slack_client.conversations_history(channel=channel_id, limit=40)
                my_style = "\n- ".join([m["text"] for m in result["messages"] if m.get("user") == user_id][:15])
                
                instructions = {
                    "✨ 초긍정 럭키비키 (원영사고)": "모든 상황을 초긍정적으로 해석. '오히려 좋아', '완전 럭키비키' 표현 필수.",
                    "🤔 논리중심 T발 (데이터 기반)": "감정을 배제하고 극도로 논리적인 팩트만 전달.",
                    "🫡 열정 신입사원 (패기)": "지나치게 열정적이고 에너제틱한 신입사원 말투.",
                    "🤫 쿨한 방관자 (알빠노)": "매우 무심하고 건조하게, 책임 소재를 확실히 하는 말투.",
                    "💀 은은한 광기 (친절한 압박)": "말투는 극도로 친절하나 내용에 묘한 압박이 느껴짐."
                }

                final_prompt = f"""
                너는 '그' 말투 번역기야. 
                1. [학습된 내 말투]: {my_style}
                2. [내 본심]: {my_raw_reply}
                3. [적용 필터]: {instructions[filter_option]}
                
                미션: 내 말투를 50% 유지하면서 위 필터를 적용해 상사에게 보낼 최종 답장을 완성해줘.
                결과는 딱 답장 내용만 한 줄로 출력해.
                """
                
                response = model.generate_content(final_prompt)
                st.session_state.final_reply = response.text
                st.balloons()
            except Exception as e:
                st.error(f"오류: {e}")

if st.session_state.final_reply:
    st.markdown("#### 🏆 제안된 최종 답변")
    st.success(st.session_state.final_reply)
    
    c_send1, c_send2 = st.columns([1, 4])
    with c_send1:
        if st.button("슬랙으로 전송"):
            requests.post(slack_webhook_url, json={"text": st.session_state.final_reply})
            st.toast("전송 완료!")
    with c_send2:
        if st.button("처음부터 다시 하기 🔄"):
            st.session_state.step = 1
            st.session_state.decoded_text = ""
            st.session_state.final_reply = ""
            st.rerun()
