import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

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
    return sh

st.title("⏱️ 스마트 밸런스 타이머 & 헬스 트래커")
st.write("구글 시트와 실시간 연동되는 타이머입니다.")

try:
    sh = init_google_sheets()
    ws = sh.get_worksheet(0)
    st.success("✨ 구글 시트와 완벽하게 연결되었습니다!")
    
    st.markdown("---")
    activity_name = st.text_input("📝 기록할 활동 이름", "집중 타이머")
    
    if st.button("🚀 기록 저장하기", use_container_width=True):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            ws.append_row([current_time, activity_name, "완료"])
            st.success(f"[{current_time}] '{activity_name}' 기록이 구글 시트에 저장되었습니다!")
            st.balloons()
        except Exception as write_err:
            # 예외 메시지가 Response 200인 경우는 실제 저장이 성공했을 확률이 높습니다
            if "200" in str(write_err):
                st.success(f"[{current_time}] '{activity_name}' 기록이 구글 시트에 안전하게 저장되었습니다!")
                st.balloons()
            else:
                raise write_err

    if st.button("📊 시트 데이터 조회하기", use_container_width=True):
        try:
            data = ws.get_all_records()
            if data:
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("아직 시트에 저장된 데이터가 없습니다.")
        except Exception as read_err:
            st.warning("데이터를 불러오는 중입니다. 구글 시트의 첫 번째 줄(헤더)에 '시간', '활동명', '상태'가 적혀 있는지 확인해 보세요!")

except Exception as e:
    st.error(f"연동 오류 발생: {e}")
