import streamlit as st
import google.generativeai as genai

# 웹페이지 탭 설정
st.set_page_config(page_title="대표님 말투 번역기", page_icon="😎")

# 제목과 설명
st.title("😎 대표님 말투 번역기 & 내 말투로 포장하기")
st.write("도대체 무슨 뜻인지 모를 대표님의 외계어... AI가 해독하고, 내 평소 말투로 자연스럽게 답장을 써줍니다!")

# Streamlit 환경변수(Secrets)에서 구글 API 키 가져오기 (보안)
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash') # 빠르고 가벼운 무료 모델
except KeyError:
    st.error("앗! API 키가 설정되지 않았어요. Streamlit 설정에서 키를 넣어주세요.")

# 사용자 입력 칸 만들기
st.subheader("1. 해독할 메시지와 내 평소 말투를 넣어주세요.")
boss_message = st.text_area("대표님(또는 타팀)이 보낸 킹받는 메시지:", placeholder="예: 이거 린하게 디벨롭 해보죠^^")
my_style = st.text_area("나의 평소 메신저 말투 (최근 보낸 카톡/슬랙 몇 개 복붙):", placeholder="예: 아 넵! 그거 내일 오전까지 해서 드릴게여 ㅠㅠ")

# 번역 시작 버튼
if st.button("🚀 번역 및 답장 생성하기"):
    if not boss_message or not my_style:
        st.warning("메시지와 평소 말투를 모두 입력해 주세요!")
    else:
        with st.spinner("눈치 100단 비서실장 AI가 짱구를 굴리고 있습니다..."):
            # AI에게 내릴 프롬프트(명령)
            prompt = f"""
            너는 20년 차 눈치 빠른 비서실장이야. 
            아래 [상사의 메시지]의 진짜 속뜻을 파악하고, [나의 평소 말투]를 분석해서 
            내 말투와 똑같은 자연스러운 답장을 만들어줘.
            
            [상사의 메시지]: {boss_message}
            [나의 평소 말투]: {my_style}
            
            출력 양식은 무조건 아래처럼 해줘:
            🚨 **진짜 속뜻**: (솔직하게 해석)
            ✅ **Action Item**: (내가 해야 할 행동)
            💡 **내 말투로 쓴 답장**: (내 평소 말투를 완벽히 모방한 답장)
            """
            
            # AI 실행 및 결과 출력
            response = model.generate_content(prompt)
            st.success("번역 완료!")
            st.markdown(response.text)
