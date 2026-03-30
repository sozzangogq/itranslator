import streamlit as st
import google.generativeai as genai
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import requests
import json

# [UI 세팅]
st.set_page_config(page_title="'그' 말투 번역기", page_icon="🤯", layout="wide")

with st.sidebar:
    st.header("😭 K-직장인 생존 지침서")
    st.markdown("1. 상사는 항상 옳다.\n2. 퇴근은 지능순이다.\n3. 이 앱을 켠 당신은 이미 승리자.")
    st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM24xb3NnaXd0YndiaXUyamk5MXRxd20wamc5NnAzamN5amphYW9zdiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3ov9jS62h1f0vXfC9i/giphy.gif")

st.markdown("<h1 style='text-align: center; color: red;'>🤯 '그' 말투 번역기 🤯</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>상사의 개소리... 원하는 모드로 조져드립니다. 🔥</p>", unsafe_allow_html=True)

# [모델 및 슬랙 설정]
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(available_models[0]) if available_models else None
    slack_token = st.secrets["SLACK_BOT_TOKEN"]
    slack_client = WebClient(token=slack_token)
    slack_webhook_url = st.secrets.get("SLACK_WEBHOOK_URL", "")
except Exception as e:
    st.error(f"설정 오류: {e}")

# [입력 섹션]
col_id, col_msg = st.columns([1, 2])
with col_id:
    channel_id = st.text_input("📍 채널 ID", placeholder="C12345...")
    user_id = st.text_input("👤 나의 멤버 ID", placeholder="U12345...")
    
    # ⭐ [추가 기능] 말투 옵션 선택창!
    st.markdown("---")
    st.subheader("🎭 답장 모드 선택")
    reply_mode = st.selectbox(
        "어떤 마인드로 답장할까요?",
        ["👸 퀸의 마인드 (자존감 폭발)", "😇 천사 모드 (지나치게 친절)", "🤖 알파고 모드 (극도로 딱딱)", "📝 반말 모드 (퇴사 각)"]
    )

with col_msg:
    boss_message = st.text_area("🤬 상사의 메시지 복붙", placeholder="예: 이거 린하게 디벨롭 해보죠^^", height=230)

if "translated_text" not in st.session_state:
    st.session_state.translated_text = ""

# [번역 실행 버튼]
if st.button("🚀 선택한 모드로 심폐소생술 시작", use_container_width=True):
    if not all([channel_id, user_id, boss_message]):
        st.warning("모든 정보를 입력해주세요!")
    else:
        with st.spinner(f"✨ {reply_mode} 장착 중..."):
            try:
                # 슬랙 메시지 수집
                result = slack_client.conversations_history(channel=channel_id, limit=50)
                my_messages = [msg["text"] for msg in result["messages"] if msg.get("user") == user_id]
                style_context = "\n- ".join(my_messages[:15]) if my_messages else "평소 말투 데이터 없음"
                
                # 모드별 프롬프트 설정
                mode_instructions = {
                    "👸 퀸의 마인드 (자존감 폭발)": "세상의 주인공은 나라는 마인드로, 상사의 지시를 '내가 해주는 우아한 서비스'처럼 표현해. 도도하고 자신감 넘치게.",
                    "😇 천사 모드 (지나치게 친절)": "간도 쓸개도 다 빼줄 것처럼 극도로 친절하고 비굴할 정도로 공손하게 답해. 이모티콘을 남발해.",
                    "🤖 알파고 모드 (극도로 딱딱)": "감정을 완전히 배제하고 오직 팩트와 업무 진행 상황만 짧고 간결하게 보고해. '~함', '~음' 체 사용.",
                    "📝 반말 모드 (퇴사 각)": "상사를 동네 친구 대하듯 편하게 반말로 대답해. 예의는 밥 말아 먹은 듯한 킹받는 말투로."
                }

                prompt = f"""
                너는 '그' 말투 번역기야. 아래 조건에 맞춰 답장을 생성해줘.
                
                1. [상사 메시지]: {boss_message}
                2. [나의 기본 말투 정보]: {style_context}
                3. [현재 장착 모드]: {mode_instructions[reply_mode]}
                
                출력 형식:
                🚨 **진짜 속뜻**: (상사가 실제로 하고 싶은 말 팩폭)
                ✅ **Action Item**: (내가 지금 해야 할 일)
                💡 **{reply_mode} 답장 추천**: (모드에 맞는 실제 전송용 답장)
                """
                
                response = model.generate_content(prompt)
                st.session_state.translated_text = response.text
                st.balloons()
            except Exception as e:
                st.error(f"에러 발생: {e}")

# [결과 출력 및 전송]
if st.session_state.translated_text:
    st.success("번역 완료!")
    st.info(st.session_state.translated_text)
    if st.button("💬 이 답장을 슬랙으로 쏘기", use_container_width=True):
        requests.post(slack_webhook_url, json={"text": st.session_state.translated_text})
        st.toast("슬랙 전송 완료! 도망가세요!🏃‍♂️")
