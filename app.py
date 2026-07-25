import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

@st.cache_resource
def init_google_sheets():
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

    # 스트림릿 Secrets 정보를 딕셔너리로 복사
    creds_dict = dict(st.secrets)

    # private_key 양쪽의 불필요한 따옴표나 공백을 제거하고 줄바꿈 정상화
    if "private_key" in creds_dict:
        pk = creds_dict["private_key"]
        pk = pk.strip().strip('"').strip("'")
        pk = pk.replace("\\n", "\n")
        creds_dict["private_key"] = pk

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
