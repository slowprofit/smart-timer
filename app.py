import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

@st.cache_resource
def init_google_sheets():
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    
    # 시크릿 정보를 복사한 뒤 private_key의 이스케이프 문자열을 진짜 줄바꿈으로 변환
    creds_dict = dict(st.secrets)
    if "private_key" in creds_dict:
        # 백슬래시 n이 문자로 들어온 경우 실제 개행 문자로 강제 치환
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    gc = gspread.authorize(creds)
    sh = gc.open("SmartTimerDB")
    return sh

st.title("⏱️ Smart Timer & Health Tracker")

try:
    sh = init_google_sheets()
    st.success("✨ 구글 시트와 완벽하게 연결되었습니다!")
except Exception as e:
    st.error(f"구글 시트 연결 에러: {e}")
