import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json

@st.cache_resource
def init_google_sheets():
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    # 스트림릿 클라우드 Secrets 설정에서 안전하게 가져오기
    creds_dict = dict(st.secrets)
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    gc = gspread.authorize(creds)
    
    # 구글 시트 문서 열기 (시트 이름에 맞게 수정됨)
    sh = gc.open("SmartTimerDB") # 혹은 실제 사용 중이신 구글 시트 이름
    return sh

st.title("⏱️ Smart Timer & Health Tracker")
st.write("스마트 타이머와 연동이 정상적으로 시작되었습니다!")

# 구글 시트 연동 테스트
try:
    sh = init_google_sheets()
    st.success("✨ 구글 시트와 완벽하게 연결되었습니다!")
except Exception as e:
    st.error(f"구글 시트 연결 에러: {e}")
