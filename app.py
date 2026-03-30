import streamlit as st
import google.generativeai as genai
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import requests
import json

# [UI 설정]
st.set_page_config(page_title="'그' 말투 번역기 V2", page_icon="🔥", layout="wide")

# 사이드바 (킹받는 짤과 가이드)
with st.sidebar:
    st.header("🏁 K-직장인 서바이벌")
    st.markdown("1. 꺾이지 않는 마음(퇴사)\n2. 중꺾마보다 중요한 건 중꺾그마(그냥 하는 마음)")
    st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM24xb3NnaXd0YndiaXUyamk5MXRxd20wamc5NnAzamN5amphYW9zdiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3ov9jS62h1f0vXfC9i/giphy.gif")

st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>🤯 '그' 말투 번역기 : 밈 에디션</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>상사의 말을 해독하고, 내 본심을 최신 밈으로 승화시키세요.</p>", unsafe_allow_html=True)

# [설정 로드]
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(available_models[0]) if available_models else None
    slack_token = st.secrets["SLACK_BOT_TOKEN"]
    slack_client = WebClient(token=slack_token)
    slack_webhook_url = st.secrets.get("SLACK_WEBHOOK_URL", "")
except Exception as e:
    st.error(f"⚠️ 설정 오류: {e}")

# [입력 섹션]
st.markdown("### 1️⃣ 정보 동기화")
c1, c2 = st.columns(2)
with c1:
    channel_id = st.text_input("📍 채널 ID", placeholder="C로 시작하는 코드")
with c2:
    user_id = st.text_input("👤 내 멤버 ID", placeholder="U로 시작하는 코드")

st.markdown("---")

# 2단계 섹션
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### 2️⃣ 상사 메시지 해독")
    boss_msg = st.text_area("🤬 상사의 킹받는 메시지:", placeholder="예: 이거 린하게 디벨롭 해보죠^^", height=100)
    
    st.markdown("### 3️⃣ 내 본심 (재료)")
    my_raw_reply = st.text_input("✍️ 내가 하고 싶은 말 (대충 쓰세요):", placeholder="예: 하기싫음, 알겠음, 내일함")

with col_right:
    st.markdown("### 4️⃣ 말투 옵션 (최신 밈)")
    # 밈 옵션 정의
    meme_option = st.radio(
        "원하는 필터를 선택하세요:",
        [
            "✨ 럭키비키 모드 (초긍정 원영사고)", 
            "🤔 T발 너 C야? (극강의 논리/팩폭)", 
            "🤫 누칼협 모드 (알빠노/사회성 제로)", 
            "🫡 에너제틱 신입사원 (MZ 패기)",
            "💀 은은한 광기 (친절한데 무서운)"
        ]
    )

# 실행 버튼
st.markdown("<br>", unsafe_allow_html=True)
if st.button("🚀 밈으로 승화된 답장 제조하기", use_container_width=True):
    if not all([channel_id, user_id, boss_msg]):
        st.warning("필수 정보를 입력해주세요!")
    else:
        with st.spinner("AI가 밈 저장소를 뒤지는 중..."):
            try:
                # 내 말투 수집
                result = slack_client.conversations_history(channel=channel_id, limit=40)
                my_style = "\n- ".join([m["text"] for m in result["messages"] if m.get("user") == user_id][:15])
                
                # 프롬프트 가이드
                instructions = {
                    "✨ 럭키비키 모드 (초긍정 원영사고)": "모든 상황을 초긍정적으로 해석해. '오히려 좋아!', '완전 럭키비키잖아!' 같은 말투 사용.",
                    "🤔 T발 너 C야? (극강의 논리/팩폭)": "감정 빼고 극도로 논리적으로 팩트만 공격해. 상대의 기분보다 효율이 우선인 말투.",
                    "🤫 누칼협 모드 (알빠노/사회성 제로)": "'알빠노', '누가 칼 들고 협박함?' 같은 마인드로 아주 무심하고 건방지게 대답해.",
                    "🫡 에너제틱 신입사원 (MZ 패기)": "지나치게 열정적이라 오히려 부담스러운 말투. '가보자고!', '가즈아!' 같은 에너지 뿜뿜.",
                    "💀 은은한 광기 (친절한데 무서운)": "말투는 극도로 친절한데 내용이나 이모티콘이 묘하게 압박감을 주는 스타일 (예: ^^... 네 알겠습니다...)"
                }

                prompt = f"""
                너는 '그' 말투 번역기야. 사용자의 말투를 베이스로 최신 밈을 섞어 답장을 만들어.
                
                [나의 평소 말투 데이터]: {my_style}
                [상사 메시지]: {boss_msg}
                [내 본심 내용]: {my_raw_reply if my_raw_reply else '적절하게'}
                [장착할 밈 필터]: {instructions[meme_option]}
                
                미션:
                1. 상사 메시지의 '진짜 속뜻'을 한 줄로 요약해.
                2. '나의 평소 말투'를 50% 유지하면서, '밈 필터'를 50% 섞어서 최종 답장을 만들어.
                
                출력 양식:
                🚨 **상사의 속뜻**: 
                💡 **최종 답장 ({meme_option})**: 
                """
                
                response = model.generate_content(prompt)
                st.session_state.translated_text = response.text
                st.balloons()
            except Exception as e:
                st.error(f"오류: {e}")

# 결과 출력
if st.session_state.translated_text:
    st.markdown("---")
    st.markdown("### 🏆 제조 완료!")
    st.info(st.session_state.translated_text)
    
    if slack_webhook_url and st.button("💬 슬랙으로 폭탄 배송하기"):
        requests.post(slack_webhook_url, json={"text": st.session_state.translated_text})
        st.toast("배송 완료! 이제 로그아웃 하세요.")
