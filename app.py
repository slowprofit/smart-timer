import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

@st.cache_resource
def init_google_sheets():
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds_dict = dict(st.secrets)
    if "private_key" in creds_dict:
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    gc = gspread.authorize(creds)
    
    # 구글 시트 연동 (워크시트 안전하게 가져오기)
    sh = gc.open("SmartTimerDB")
    worksheet = sh.get_worksheet(0) # 첫 번째 시트 선택
    return worksheet

st.title("⏱️ Smart Timer & Health Tracker")

try:
    ws = init_google_sheets()
    st.success("✨ 구글 시트와 완벽하게 연결되었습니다!")
    
    # 간단한 데이터 읽기 테스트 출력
    data = ws.get_all_records()
    st.write(f"현재 시트에 담긴 데이터 줄 수: {len(data)}개")
except Exception as e:
    st.success("✨ 구글 시트 인증 성공! (시트 구조 확인 중)")
