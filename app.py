import streamlit as st
import google.generativeai as genai
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import requests
import json
import random

# [UI 설정]
st.set_page_config(page_title="'그' 말투 번역기 : 노비 에디션", page_icon="👹", layout="wide")

# 사이드바 (더 킹받는 문구)
with st.sidebar:
    st.header("📋 노비 생존 수칙")
    st.markdown("1. 부장님의 농담엔 인공지능보다 빠르게 웃는다.\n2. 점심 메뉴 결정권은 나에게 없다.\n3. 월급은 내 통장을 스쳐 지나갈 뿐.")
    st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM24xb3NnaXd0YndiaXUyamk5MXRxd20wamc5NnAzamN5amphYW9zdiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3ov9jS62h1f0vXfC9i/giphy.gif")

st.markdown("<h1 style='text-align: center; color: #1E1E1E;'>💼 '그' 말투 번역기 : 노비 에디션</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666;'>부장님의 가스라이팅을 인간의 언어로 번역해 드립니다. (안구 습기 주의)</p>", unsafe_allow_html=True)

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
        channel_id = st.text_input("📍 채널 ID", placeholder="C...로 시작하는 코드")
    with c2:
        user_id = st.text_input("👤 내 멤버 ID", placeholder="U...로 시작하는 코드")

st.markdown("---")

# ---------------------------------------------------------
# [1단계: 메시지 해독] - 더 웃기고 킹받는 버전
# ---------------------------------------------------------
if st.session_state.step >= 1:
    st.markdown("### 🔍 STEP 1. 부장님 뇌구조 심층 해독")
    boss_msg = st.text_area("🤬 분석할 상사의 메시지 (복붙 권장):", placeholder="예: 이거 린하게 디벨롭 해보죠^^", height=100)
    
    # 킹받는 로딩 문구 리스트
    loading_messages = [
        "부장님의 꼰대 지수를 측정하는 중... 📏",
        "행간에 숨겨진 야근의 향기를 맡는 중... 👃",
        "사회생활용 가짜 웃음을 장전하는 중... 😄",
        "퇴사 욕구를 억누르며 번역기를 돌리는 중... 🧘‍♂️",
        "상사의 개소리를 인간의 언어로 정제하는 중... 🧪",
        "비속어 필터를 필사적으로 가동하는 중... 🤐"
    ]

    if st.button("진실의 방으로 (해독 시작) 🧐"):
        if not boss_msg or not channel_id or not user_id:
            st.warning("정보를 다 안 넣으면 번역기가 파업합니다.")
        else:
            with st.spinner(random.choice(loading_messages)):
                decode_prompt = f"""
                너는 세상만사 다 겪고 영혼까지 찌든 15년 차 만년 과장이야. 
                아래 상사의 메시지를 '직장인 흑화 모드'로 아주 냉소적이고 웃기게 분석해줘.
                
                [상사 메시지]: "{boss_msg}"
                
                출력 양식 (무조건 이 형식을 지켜):
                🚨 **본심 (팩트 폭격)**: (상사의 구질구질한 의도를 아주 적나라하고 웃기게 한 줄 요약)
                ✅ **노비 지침 (살길)**: (사용자가 살기 위해 해야 할 행동을 자학적으로 표현)
                """
                response = model.generate_content(decode_prompt)
                st.session_state.decoded_full = response.text
                st.session_state.step = 2 
                st.rerun()

if st.session_state.decoded_full:
    st.markdown("#### 🚩 AI 과장님의 팩트 폭격")
    st.error(st.session_state.decoded_full) # 빨간색 박스로 더 눈에 띄게!

# ---------------------------------------------------------
# [2단계: 답변 제조]
# ---------------------------------------------------------
if st.session_state.step == 2:
    st.markdown("---")
    st.markdown("### 🚀 STEP 2. 생존용 답변 제조")
    
    col_a, col_b = st.columns(2)
    with col_a:
        my_raw_reply = st.text_input("✍️ 내 본심 (거칠게 써도 됨):", placeholder="예: 안해, 싫어, 니가 해")
    with col_b:
        filter_option = st.selectbox(
            "장착할 커뮤니케이션 필터:",
            [
                "✨ 초긍정 럭키비키 (원영사고)", 
                "🤔 논리중심 T발 (데이터 기반)", 
                "🫡 열정 신입사원 (패기)", 
                "🤫 쿨한 방관자 (무심한 프로)", 
                "💀 은은한 광기 (친절한 압박)"
            ]
        )

    if st.button("사회생활용 답장으로 세탁하기 ✨"):
        with st.spinner("내 말투 데이터와 필터를 섞어서 세탁 중... 🧼"):
            try:
                result = slack_client.conversations_history(channel=channel_id, limit=40)
                my_style = "\n- ".join([m["text"] for m in result["messages"] if m.get("user") == user_id][:15])
                
                instructions = {
                    "✨ 초긍정 럭키비키 (원영사고)": "모든 고난을 축복으로 생각하는 럭키비키 말투. '오히려 좋아' 남발.",
                    "🤔 논리중심 T발 (데이터 기반)": "감정은 1%도 섞지 말고 차갑고 논리적인 팩트만 전달.",
                    "🫡 열정 신입사원 (패기)": "너무 열정적이라 상사가 부담스러워할 정도의 씩씩함.",
                    "🤫 쿨한 방관자 (무심한 프로)": "영혼 없는 대답의 정석. 선을 지키면서 할 말만 함.",
                    "💀 은은한 광기 (친절한 압박)": "눈은 웃고 있는데 말은 무서운 스타일. 은근한 압박."
                }

                final_prompt = f"""
                너는 사용자의 슬랙 말투를 복제하는 AI 비서야.
                1. [내 말투 데이터]: {my_style}
                2. [내 답변 본심]: {my_raw_reply}
                3. [필터 컨셉]: {instructions[filter_option]}
                
                미션: 내 말투를 살리면서 필터를 적용해 상사에게 보낼 최종 답장을 딱 한 줄로 만들어줘.
                """
                
                response = model.generate_content(final_prompt)
                st.session_state.final_reply = response.text
                st.balloons()
            except Exception as e:
                st.error(f"오류: {e}")

if st.session_state.final_reply:
    st.markdown("#### 🏆 세탁 완료된 최종 답장")
    st.success(st.session_state.final_reply)
    
    cs1, cs2 = st.columns([1, 4])
    with cs1:
        if st.button("슬랙으로 배송"):
            requests.post(slack_webhook_url, json={"text": st.session_state.final_reply})
            st.toast("폭탄 배송 완료! 💣")
    with cs2:
        if st.button("처음부터 다시 (기억 삭제) 🔄"):
            st.session_state.step = 1
            st.session_state.decoded_full = ""
            st.session_state.final_reply = ""
            st.rerun()
