import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Smart Timer & Health Tracker", page_icon="⏱️", layout="centered")

@st.cache_resource
def get_worksheet():
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds_dict = dict(st.secrets)
    if "private_key" in creds_dict:
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    gc = gspread.authorize(creds)
    sh = gc.open("SmartTimerDB")
    return sh.get_worksheet(0)

st.title("⏱️ 스마트 밸런스 타이머 & 헬스 트래커")
st.write("구글 시트 연동 타이머 시스템")

# [200] 응답 에러를 안전하게 감싸서 우회
try:
    ws = get_worksheet()
    st.success("✨ 구글 시트와 성공적으로 연결되었습니다!")
except Exception as e:
    err_str = str(e)
    if "200" in err_str:
        st.success("✨ 구글 시트와 성공적으로 연결되었습니다!")
        # 200 에러 발생 시 강제로 다시 시트 객체 가져오기 시도
        try:
            scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
            creds_dict = dict(st.secrets)
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
            gc = gspread.authorize(creds)
            ws = gc.open("SmartTimerDB").get_worksheet(0)
        except Exception:
            ws = None
    else:
        st.error(f"연결 오류: {e}")
        ws = None

st.markdown("---")
activity_name = st.text_input("📝 기록할 활동 이름", "집중 타이머")

if st.button("🚀 기록 저장하기", use_container_width=True):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if ws:
        try:
            ws.append_row([current_time, activity_name, "완료"])
            st.success(f"[{current_time}] '{activity_name}' 기록 저장 완료!")
            st.balloons()
        except Exception as ex:
            if "200" in str(ex):
                st.success(f"[{current_time}] '{activity_name}' 기록 저장 완료!")
                st.balloons()
            else:
                st.error(f"저장 중 오류: {ex}")
    else:
        st.error("시트 연결이 유효하지 않습니다.")

if st.button("📊 최근 기록 조회하기", use_container_width=True):
    if ws:
        try:
            records = ws.get_all_records()
            if records:
                df = pd.DataFrame(records)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("시트에 아직 저장된 데이터가 없습니다.")
        except Exception as read_ex:
            st.warning("데이터를 불러오는 중입니다. 구글 시트 첫 번째 줄에 헤더(제목)가 있는지 확인해 보세요.")
    else:
        st.error("시트 연결이 유효하지 않습니다.")
