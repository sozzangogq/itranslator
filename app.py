import streamlit as st
import google.generativeai as genai
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import requests
import json

st.set_page_config(page_title="대표님 말투 번역기", page_icon="😎")
st.title("😎 대표님 말투 번역기 (슬랙 자동 학습 버전)")
st.write("슬랙에서 내 평소 말투를 자동으로 긁어와서, 상사의 외계어에 찰떡같이 답장해 줍니다!")

# 설정 불러오기
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
    slack_webhook_url = st.secrets.get("SLACK_WEBHOOK_URL", "")
    slack_token = st.secrets["SLACK_BOT_TOKEN"]
    slack_client = WebClient(token=slack_token)
except KeyError:
    st.error("앗! 설정(Secrets)에 API 키나 슬랙 토큰이 빠져있어요.")

# UI: 사용자 입력 받기
st.subheader("1. 기본 정보 입력 (데모 시연용)")
col1, col2 = st.columns(2)
with col1:
    # 슬랙 채널 ID (채널 이름 우클릭 -> 링크 복사 후 맨 끝 영문숫자 조합)
    channel_id = st.text_input("데이터를 긁어올 슬랙 채널 ID:", placeholder="예: C12345678")
with col2:
    # 내 슬랙 멤버 ID (내 프로필 클릭 -> 점 3개 -> 멤버 ID 복사)
    user_id = st.text_input("나의 슬랙 멤버 ID:", placeholder="예: U12345678")

boss_message = st.text_area("2. 대표님(또는 타팀)이 보낸 킹받는 메시지:", placeholder="예: 이거 린하게 디벨롭 해보죠^^")

if "translated_text" not in st.session_state:
    st.session_state.translated_text = ""

# 대망의 버튼!
if st.button("🚀 내 말투 자동 수집 & 번역 시작!"):
    if not channel_id or not user_id or not boss_message:
        st.warning("채널 ID, 멤버 ID, 상사의 메시지를 모두 입력해 주세요!")
    else:
        with st.spinner("슬랙에 잠입하여 내 말투를 긁어오는 중... 🕵️‍♂️"):
            try:
                # 1. 슬랙 채널에서 최근 대화 50개 가져오기
                result = slack_client.conversations_history(channel=channel_id, limit=50)
                messages = result["messages"]
                
                # 2. 그 중에서 '내가(user_id)' 쓴 글만 필터링하기
                my_messages = [msg["text"] for msg in messages if msg.get("user") == user_id and "text" in msg]
                
                if not my_messages:
                    st.error("앗! 해당 채널에서 최근에 님이 쓰신 메시지를 찾을 수 없어요. (최근 50개 기준)")
                else:
                    # 3. 내 말투 데이터를 하나의 텍스트로 묶기
                    my_style_data = "\n- ".join(my_messages)
                    st.success(f"성공! 슬랙에서 내 말투 {len(my_messages)}개를 성공적으로 긁어왔습니다.")
                    
                    # 4. AI에게 번역 시키기
                    with st.spinner("말투 분석 및 번역 중... 짱구 굴리는 중... 🧠"):
                        prompt = f"""
                        너는 20년 차 눈치 빠른 비서실장이야. 
                        아래 [상사의 메시지]의 속뜻을 파악하고, [나의 평소 슬랙 말투]를 분석해서 
                        내 말투와 똑같은 자연스러운 답장을 만들어줘.
                        
                        [상사의 메시지]: {boss_message}
                        [나의 평소 슬랙 말투 (자동 수집됨)]: \n- {my_style_data}
                        
                        출력 양식:
                        🚨 **진짜 속뜻**: (솔직하게 해석)
                        ✅ **Action Item**: (내가 해야 할 행동)
                        💡 **내 말투로 쓴 답장**: (내 평소 말투를 완벽히 모방한 답장)
                        """
                        response = model.generate_content(prompt)
                        st.session_state.translated_text = response.text
                        
            except SlackApiError as e:
                # 에러 발생 시 (봇이 채널에 초대 안 된 경우 등)
                error_msg = e.response['error']
                if error_msg == "not_in_channel":
                    st.error("🚨 봇이 해당 채널에 없습니다! 슬랙 채널 채팅창에 `/invite @말투 번역기` 를 쳐서 봇을 초대해 주세요.")
                else:
                    st.error(f"슬랙 연동 에러: {error_msg}")

# 결과 출력 및 슬랙 쏘기
if st.session_state.translated_text:
    st.markdown("---")
    st.markdown(st.session_state.translated_text)
    
    if slack_webhook_url and st.button("💬 이 답장을 슬랙으로 바로 쏘기"):
        slack_data = {"text": f"🤖 *AI가 번역한 추천 답장입니다!*\n\n{st.session_state.translated_text}"}
        res = requests.post(slack_webhook_url, data=json.dumps(slack_data), headers={'Content-Type': 'application/json'})
        if res.status_code == 200:
            st.success("슬랙 채널로 메시지가 날아갔습니다! 🎉")
        else:
            st.error("슬랙 전송 실패!")
