import streamlit as st
import gspread

@st.cache_resource
def init_google_sheets():
    gc = gspread.service_account_from_dict(dict(st.secrets))
    sh = gc.open("SmartTimerDB")
    return sh

st.title("⏱️ Smart Timer & Health Tracker")

try:
    sh = init_google_sheets()
    st.success("✨ 구글 시트와 완벽하게 연결되었습니다!")
except Exception as e:
    st.error(f"구글 시트 연결 에러: {e}")
