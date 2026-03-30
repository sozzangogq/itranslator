import streamlit as st
import google.generativeai as genai
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import requests
import json

# [UI 세팅] 페이지 설정
st.set_page_config(page_title="'그' 말투 번역기", page_icon="🤯", layout="wide")

with st.sidebar:
    st.header("😭 K-직장인 생존 지침서")
    st.markdown("""
    1. **상사는 항상 옳다.** (아니면 말고)
    2. **퇴근 시간은 숫자에 불과하다.**
    3. **이 앱을 켠 순간, 넌 이미 일류다.**
    ---
    *개발: 눈치 100단 비서실장 AI*
    """)
    st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM24xb3NnaXd0YndiaXUyamk5MXRxd20wamc5NnAzamN5amphYW9zdiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3ov9jS62h1f0vXfC9i/giphy.gif")

st.markdown("<h1 style='text-align: center; color: red; font-size: 60px;'>🤯 '그' 말투 번역기 🤯</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 20px;'>도대체 뭔 소린지 모르겠는 상사의 지시... AI가 피눈물을 흘리며 해독해 드립니다. 💧</p>", unsafe_allow_html=True)
st.markdown("---")

# [핵심 수정] 구글 AI 모델 "자동 검색" 기능 탑재!
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # 꼼수: 내 API 키로 쓸 수 있는 AI 모델 목록을 싹 다 가져옵니다.
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    
    if not available_models:
        st.error("🚨 구글 API 키에 문제가 있는 것 같아요. 사용 가능한 모델이 없습니다.")
    else:
        # 가장 첫 번째로 검색된 사용 가능한 모델을 무조건 가져다 씁니다! (NotFound 에러 원천 차단)
        model = genai.GenerativeModel(available_models[0])
        
    slack_webhook_url = st.secrets.get("SLACK_WEBHOOK_URL", "")
    slack_token = st.secrets["SLACK_BOT_TOKEN"]
    slack_client = WebClient(token=slack_token)
except Exception as e:
    st.error(f"🚨 설정 오류 발생: {e}")

col_id, col_msg = st.columns([1, 2])

with col_id:
    st.subheader("🕵️‍♂️ 노비 문서(슬랙) 정보 추출")
    st.markdown("<small>채널 우클릭->링크 복사 끝에꺼</small>", unsafe_allow_html=True)
    channel_id = st.text_input("📍 킹받는 채널 ID:", placeholder="예: C0123456789")
    
    st.markdown("<small>내 프로필->점3개->멤버 ID 복사</small>", unsafe_allow_html=True)
    user_id = st.text_input("👤 나의 노비 ID (멤버 ID):", placeholder="예: U0123456789")

with col_msg:
    st.subheader("🤬 상사의 주절주절 입력")
    boss_message = st.text_area("그냥 복붙하세요. 뭔 말인지 이해하려고 하지 마세요.", placeholder="예: 이거 린하게 디벨롭 해보죠^^", height=150)

if "translated_text" not in st.session_state:
    st.session_state.translated_text = ""

st.markdown("---")
button_col1, button_col2, button_col3 = st.columns([1, 2, 1])

with button_col2:
    translate_btn = st.button("🚨 사회생활 심폐소생술 시작 (내 말투 자동 학습) 🚨", use_container_width=True)

if translate_btn:
    if not channel_id or not user_id or not boss_message:
        st.warning("⚠️ ID랑 메시지 다 넣으라고요... 현기증 나니까...")
    else:
        with st.spinner("🕵️‍♂️ 슬랙에 침입하여 과거의 당신이 저지른 대화 내역을 훔치는 중..."):
            try:
                result = slack_client.conversations_history(channel=channel_id, limit=80)
                messages = result["messages"]
                my_messages = [msg["text"] for msg in messages if msg.get("user") == user_id and "text" in msg]
                
                if not my_messages:
                    st.error("🚨 헐; 이 채널에서 님이 쓴 글이 없는데요? 유령이신가요? (최근 80개 기준)")
                else:
                    my_style_data = "\n- ".join(my_messages)
                    st.toast(f"✅ 성공! 당신의 과거 {len(my_messages)}개를 훔쳐왔습니다.", icon='🔓')
                    
                    with st.spinner("🧠 비서실장 AI가 뇌 주름을 펼쳐 '그' 말투를 분석 중..."):
                        prompt = f"""
                        너는 20년 차 눈치 빠른 비서실장이야. 
                        아래 [상사의 메시지]의 속뜻을 팩트폭격 수준으로 아주 솔직하게 파악하고, 
                        [나의 평소 슬랙 말투]를 분석해서 내 말투와 똑같은 자연스러운 답장을 만들어줘.
                        
                        [상사의 메시지]: {boss_message}
                        [나의 평소 슬랙 말투 (자동 수집됨)]: \n- {my_style_data}
                        
                        출력 양식은 무조건 아래처럼 해줘 (이모티콘 과하게 써서):
                        🚨 **진짜 속뜻 (헐;)**: 
                        ✅ **Action Item (이거나 해라)**: 
                        💡 **내 말투로 쓴 답장 (살려주세요)**: 
                        """
                        # 자동으로 찾은 모델을 사용하여 번역 실행
                        response = model.generate_content(prompt)
                        st.session_state.translated_text = response.text
                        st.balloons() 
                        
            except SlackApiError as e:
                error_msg = e.response['error']
                if error_msg == "not_in_channel":
                    st.error("🚨 봇이 채널에 없습니다! 슬랙 채팅창에 `/invite @말투 번역기` 를 쳐서 봇을 초대하세요! 제발!")
                else:
                    st.error(f"슬랙 연동 에러 (망함): {error_msg}")
            except Exception as e:
                # 구글 AI 쪽 에러가 나면 무서운 빨간 글씨 대신 여기에 원인을 띄워줍니다.
                st.error(f"🚨 구글 AI 번역 중 에러가 발생했습니다: {e}")

if st.session_state.translated_text:
    st.markdown("<br><h2 style='text-align: center; color: green;'>✨ 영롱한 번역 결과 ✨</h2>", unsafe_allow_html=True)
    st.info(st.session_state.translated_text)
    
    st.markdown("---")
    if slack_webhook_url and st.button("💬 이 완벽한 답장을 슬랙으로 바로 쏴버리기 (딸깍)", use_container_width=True):
        with st.spinner("🚀 부장님에게 폭탄 배송 중..."):
            slack_data = {"text": f"🤖 *AI 비서가 피눈물 흘리며 적어준 추천 답장입니다!*\n\n{st.session_state.translated_text}"}
            res = requests.post(slack_webhook_url, data=json.dumps(slack_data), headers={'Content-Type': 'application/json'})
            if res.status_code == 200:
                st.success("부장님 채널로 메시지가 날아갔습니다! 이제 도망가세요! 🎉")
            else:
                st.error("슬랙 전송 실패! (오히려 좋아?)")
