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
st.write("집중 타이머와 건강 상태를 기록하고 구글 시트에 저장하는 시스템입니다.")

# 시트 연결 확인
test_ws = get_worksheet_safely()
if test_ws:
    st.success("✨ 구글 시트와 성공적으로 연결되었습니다!")
else:
    st.warning("⚠️ 구글 시트 연결을 확인해 주세요.")

st.markdown("---")

# 탭 나누기 (타이머 vs 건강 기록)
tab1, tab2 = st.tabs(["⏱️ 타이머 & 집중 기록", "💪 건강 & 컨디션 기록"])

with tab1:
    st.subheader("집중 및 활동 타이머")
    activity_name = st.text_input("📝 활동 이름 (예: 집중 공부, 도자기 작업, 스트레칭)", "집중 작업")
    duration_min = st.number_input("⏱️ 소요 시간 (분)", min_value=1, max_value=300, value=25)
    
    if st.button("🚀 타이머 기록 저장하기", use_container_width=True):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ws = get_worksheet_safely()
        if ws:
            try:
                # [시간, 카테고리/활동명, 내용/시간(분), 상태]
                ws.append_row([current_time, "타이머", f"{activity_name} ({duration_min}분)", "완료"])
                st.success(f"[{current_time}] '{activity_name}' {duration_min}분 기록이 저장되었습니다!")
                st.balloons()
            except Exception as ex:
                if "200" in str(ex):
                    st.success(f"[{current_time}] '{activity_name}' {duration_min}분 기록이 저장되었습니다!")
                    st.balloons()
                else:
                    st.error(f"저장 중 오류: {ex}")
        else:
            st.error("시트 연결 실패")

with tab2:
    st.subheader("오늘의 건강 & 컨디션 체크")
    condition = st.select_slider("⚡ 컨디션 상태", options=["매우 피곤", "피곤함", "보통", "가벼움", "최상"], value="보통")
    water_intake = st.number_input("💧 물 마신 양 (컵)", min_value=0, max_value=20, value=5)
    health_memo = st.text_input("💬 건강 메모 (예: 어깨 스트레칭 완료, 가벼운 산책)", "가벼운 스트레칭 완료")
    
    if st.button("💪 건강 기록 저장하기", use_container_width=True):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ws = get_worksheet_safely()
        if ws:
            try:
                memo_str = f"컨디션: {condition} | 물: {water_intake}컵 | 메모: {health_memo}"
                ws.append_row([current_time, "건강", memo_str, "완료"])
                st.success(f"[{current_time}] 건강 기록이 저장되었습니다!")
                st.balloons()
            except Exception as ex:
                if "200" in str(ex):
                    st.success(f"[{current_time}] 건강 기록이 저장되었습니다!")
                    st.balloons()
                else:
                    st.error(f"저장 중 오류: {ex}")
        else:
            st.error("시트 연결 실패")

st.markdown("---")
if st.button("📊 전체 기록 조회하기", use_container_width=True):
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
            st.warning("데이터 형식을 불러오는 중입니다. 시트 첫 번째 줄에 헤더(시간, 분류, 내용, 상태)가 있는지 확인해 주세요.")
    else:
        st.error("시트 연결에 실패했습니다.")
