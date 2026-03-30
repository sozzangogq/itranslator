import streamlit as st
import google.generativeai as genai
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import requests
import json

# [UI 세팅]
st.set_page_config(page_title="'그' 말투 번역기", page_icon="🤯", layout="wide")

# 사이드바 설정
with st.sidebar:
    st.header("😭 K-직장인 생존 지침서")
    st.markdown("1. 상사는 항상 옳다.\n2. 퇴근은 지능순이다.\n3. 이 앱을 켠 당신은 이미 일류.")
    st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM24xb3NnaXd0YndiaXUyamk5MXRxd20wamc5NnAzamN5amphYW9zdiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3ov9jS62h1f0vXfC9i/giphy.gif")

st.markdown("<h1 style='text-align: center; color: red;'>🤯 '그' 말투 번역기 🤯</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>내 말투를 학습해서 상사에게 날릴 완벽한 답장을 제조합니다.</p>", unsafe_allow_html=True)

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
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🕵️‍♂️ 정보 입력")
    channel_id = st.text_input("📍 채널 ID", placeholder="C12345...")
    user_id = st.text_input("👤 나의 멤버 ID", placeholder="U12345...")
    
    st.markdown("---")
    st.subheader("🎭 답장 컨셉 선택")
    reply_mode = st.radio(
        "내 말투에 어떤 색깔을 입힐까요?",
        ["👸 퀸의 마인드 (우아한 거절/수락)", "😇 천사 모드 (극강의 친절)", "🤖 알파고 모드 (기계적 효율)", "📝 반말 모드 (심장 쫄깃)"],
        horizontal=True
    )

with col2:
    st.subheader("💬 메시지 입력")
    boss_message = st.text_area("🤬 상사의 메시지 (해독용)", placeholder="상사가 뭐라고 했나요?", height=100)
    my_rough_reply = st.text_input("✍️ 나의 대충 쓴 답변 (재료)", placeholder="예: 안됨, 알겠음, 나중에함")

if "translated_text" not in st.session_state:
    st.session_state.translated_text = ""

# [실행 버튼]
st.markdown("---")
if st.button("🚨 내 말투로 필터링해서 답장 제조하기", use_container_width=True):
    if not all([channel_id, user_id, boss_message]):
        st.warning("정보를 입력해주세요!")
    else:
        with st.spinner(f"🧠 내 말투 분석 중 + {reply_mode} 장착 중..."):
            try:
                # 1. 내 말투 수집
                result = slack_client.conversations_history(channel=channel_id, limit=60)
                my_messages = [msg["text"] for msg in result["messages"] if msg.get("user") == user_id]
                style_context = "\n- ".join(my_messages[:20]) if my_messages else "데이터 부족"
                
                # 2. 모드별 상세 지시
                mode_map = {
                    "👸 퀸의 마인드 (우아한 거절/수락)": "도도하고 자신감 넘치는 '퀸'의 성격을 가미해. 하지만 내 평소 말투의 단어나 문체는 유지해.",
                    "😇 천사 모드 (극강의 친절)": "내 말투를 유지하되, 훨씬 더 친절하고 상냥한 표현과 이모티콘을 듬뿍 섞어줘.",
                    "🤖 알파고 모드 (기계적 효율)": "내 말투에서 감정적인 군더더기를 싹 빼고, 핵심만 딱딱하게 전달하는 비즈니스 문체로 바꿔.",
                    "📝 반말 모드 (심장 쫄깃)": "내 말투를 반말로 변환해. 아주 친한 친구나 아랫사람에게 하듯 킹받게 말해봐."
                }

                # 3. 프롬프트 구성 (말투 학습 + 답변 재료 + 컨셉)
                prompt = f"""
                너는 사용자의 슬랙 말투를 완벽하게 복제하는 AI 비서야.
                
                [학습할 나의 평소 말투]:
                {style_context}
                
                [상황]:
                - 상사의 메시지: "{boss_message}"
                - 내가 하고 싶은 말(핵심 내용): "{my_rough_reply if my_rough_reply else '적절한 대응'}"
                - 적용할 컨셉: {mode_map[reply_mode]}
                
                [미션]:
                1. 상사의 메시지 속뜻을 아주 짧게 파악해줘.
                2. '나의 평소 말투'의 특징(자주 쓰는 어미, 이모티콘 사용 빈도 등)을 살리되, '적용할 컨셉'이 느껴지도록 최종 답장을 만들어줘.
                
                출력 양식:
                🚨 **상사의 속뜻**: 
                💡 **추천 답장 ({reply_mode})**: 
                """
                
                response = model.generate_content(prompt)
                st.session_state.translated_text = response.text
                st.balloons()
            except Exception as e:
                st.error(f"오류가 발생했어요: {e}")

# [결과 출력]
if st.session_state.translated_text:
    st.markdown("### ✨ 제조된 답변")
    st.info(st.session_state.translated_text)
    
    if slack_webhook_url and st.button("💬 이 답변 슬랙으로 바로 쏘기"):
        requests.post(slack_webhook_url, json={"text": st.session_state.translated_text})
        st.toast("전송 완료!")
