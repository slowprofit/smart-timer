import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

@st.cache_resource
def init_google_sheets():
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

    # 스트림릿 Secrets에서 딕셔너리로 가져오기
    creds_dict = dict(st.secrets)

    # private_key의 줄바꿈 문자열(\n)을 실제 줄바꿈으로 안전하게 변환
    if "private_key" in creds_dict:
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
