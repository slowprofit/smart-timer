import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="Smart Timer & Health Tracker", page_icon="⏱️", layout="centered")

@st.cache_resource
def init_google_sheets():
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds_dict = dict(st.secrets)
    if "private_key" in creds_dict:
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    gc = gspread.authorize(creds)
    sh = gc.open("SmartTimerDB")
    worksheet = sh.get_worksheet(0)
    return worksheet

st.title("⏱️ 스마트 밸런스 타이머 & 헬스 트래커")
st.write("구글 시트와 실시간 연동되어 기록이 저장되는 타이머입니다.")

try:
    ws = init_google_sheets()
    st.success("✨ 구글 시트와 완벽하게 연결되었습니다!")
    
    # 사용자 입력 및 타이머 컨트롤 영역
    st.markdown("---")
    activity_name = st.text_input("📝 기록할 활동 이름 (예: 집중 공부, 스트레칭 등)", "집중 타이머")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 기록 저장하기 (테스트)", use_container_width=True):
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # 구글 시트에 데이터 행 추가 (시간, 활동명)
            ws.append_row([current_time, activity_name, "완료"])
            st.success(f"[{current_time}] '{activity_name}' 기록이 구글 시트에 저장되었습니다!")
            st.balloons()

    with col2:
        if st.button("📊 시트 데이터 조회하기", use_container_width=True):
            data = ws.get_all_records()
            if data:
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("아직 시트에 저장된 데이터가 없습니다. 기록을 저장해 보세요!")

except Exception as e:
    st.error(f"연동 오류 발생: {e}")
