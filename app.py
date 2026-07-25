import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Smart Timer & Health Tracker", page_icon="⏱️", layout="centered")

def get_worksheet_safely():
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds_dict = dict(st.secrets)
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        gc = gspread.authorize(creds)
        sh = gc.open("SmartTimerDB")
        return sh.get_worksheet(0)
    except Exception:
        return None

st.title("⏱️ 스마트 밸런스 타이머 & 헬스 트래커")
st.write("구글 시트 연동 타이머 시스템")

# 실시간 시트 연결 테스트
test_ws = get_worksheet_safely()
if test_ws:
    st.success("✨ 구글 시트와 성공적으로 연결되었습니다!")
else:
    st.warning("⚠️ 구글 시트 연결을 재시도하고 있습니다. 아래 버튼을 눌러보세요.")

st.markdown("---")
activity_name = st.text_input("📝 기록할 활동 이름", "집중 타이머")

if st.button("🚀 기록 저장하기", use_container_width=True):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ws = get_worksheet_safely()
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
        st.error("시트 연결에 실패했습니다. 자격 증명이나 시트 이름을 확인해 주세요.")

if st.button("📊 최근 기록 조회하기", use_container_width=True):
    ws = get_worksheet_safely()
    if ws:
        try:
            records = ws.get_all_records()
            if records:
                df = pd.DataFrame(records)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("시트에 아직 저장된 데이터가 없습니다.")
        except Exception as read_ex:
            st.warning("데이터 형식을 불러오는 중입니다. 시트의 첫 번째 행(헤더)에 적절한 제목이 있는지 확인해 주세요.")
    else:
        st.error("시트 연결에 실패했습니다.")
