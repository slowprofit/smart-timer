import streamlit as st
import pandas as pd
from datetime import datetime
import os
import uuid
import json
import time

# --- 파일 경로 설정 ---
FILE_NAME = "time_management.xlsx"
HEALTH_FILE_NAME = "health_log.xlsx"
CAT_FILE = "categories.txt"
HEALTH_SETTING_FILE = "health_settings.json"
APP_SETTING_FILE = "app_settings.json"

DEFAULT_CATS = ['카페', '온라인', '개인', '집안일']
DEFAULT_HEALTH = {'pushup': 20, 'drink water': 4, 'take vitamins': 20}
DEFAULT_APP = {'work_start': '10:00', 'work_end': '21:00'}

# --- 모바일 최적화 및 커스텀 사각 버튼 CSS ---
st.markdown("""
    <style>
    .block-container {
        padding-top: 3.5rem !important; 
        padding-bottom: 1rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 5px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 12px !important;
        font-size: 15px !important;
    }
    div[data-testid="stForm"] {
        padding: 10px !important;
    }
    h1, h2, h3 { margin-bottom: 0.2rem !important; }
    
    /* 건강 탭의 사각형 빅버튼 디자인 및 줄바꿈 허용 */
    .stButton>button {
        height: 75px !important; 
        white-space: pre-wrap !important; 
        border-radius: 12px !important;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- 설정 데이터 함수 ---
def load_settings(file_name, default_val):
    if os.path.exists(file_name):
        with open(file_name, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default_val

def save_settings(file_name, settings):
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False)

def load_categories():
    if os.path.exists(CAT_FILE):
        with open(CAT_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip().split(',')
    return DEFAULT_CATS

def save_categories(cats):
    with open(CAT_FILE, 'w', encoding='utf-8') as f:
        f.write(','.join(cats))

# --- 세션 초기화 ---
if 'intro_shown' not in st.session_state:
    st.session_state.intro_shown = False
if 'tasks' not in st.session_state:
    st.session_state.tasks = {}
if 'admin_mode' not in st.session_state:
    st.session_state.admin_mode = False
if 'categories' not in st.session_state:
    st.session_state.categories = load_categories()
if 'health_settings' not in st.session_state:
    st.session_state.health_settings = load_settings(HEALTH_SETTING_FILE, DEFAULT_HEALTH)
if 'app_settings' not in st.session_state:
    st.session_state.app_settings = load_settings(APP_SETTING_FILE, DEFAULT_APP)

# --- 인트로 화면 ---
if not st.session_state.intro_shown:
    intro_placeholder = st.empty()
    with intro_placeholder.container():
        st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #4A4A4A;'>⏱️ 스마트 밸런스 타이머</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #888;'>Created by <b>Minu Minu</b></p>", unsafe_allow_html=True)
    time.sleep(2.5) 
    intro_placeholder.empty() 
    st.session_state.intro_shown = True

# --- 업무 타이머 제어 함수 ---
def create_task(main_cat, task, sub_task, amount):
    task_id = str(uuid.uuid4())[:8]
    now = datetime.now()
    st.session_state.tasks[task_id] = {
        '큰 분류': main_cat, '업무분류': task, '업무세부분류': sub_task,
        '작업량': amount, 'status': 'running', 'start_time': now,
        'last_resume_time': now, 'actual_seconds': 0
    }

def pause_task(task_id):
    now = datetime.now()
    t = st.session_state.tasks[task_id]
    if t['status'] == 'running':
        t['actual_seconds'] += (now - t['last_resume_time']).total_seconds()
        t['status'] = 'paused'

def resume_task(task_id):
    t = st.session_state.tasks[task_id]
    if t['status'] == 'paused':
        t['last_resume_time'] = datetime.now()
        t['status'] = 'running'

def end_task(task_id):
    now = datetime.now()
    t = st.session_state.tasks[task_id]
    if t['status'] == 'running':
        t['actual_seconds'] += (now - t['last_resume_time']).total_seconds()

    total_minutes = max(1, int((now - t['start_time']).total_seconds() / 60))
    actual_minutes = max(1, int(t['actual_seconds'] / 60))
    unit_time = round(actual_minutes / t['작업량'], 1) if t['작업량'] > 0 else 0

    df = pd.read_excel(FILE_NAME) if os.path.exists(FILE_NAME) else pd.DataFrame(columns=[
        '날짜', '연도', '월', '큰 분류', '업무분류', '업무세부분류', '작업량', '시작시간', '끝시간', '총 시간(분)', '실제 일한 시간(분)', '단위 소요시간(분/개)'
    ])

    new_record = pd.DataFrame([{
        '날짜': now.strftime("%Y-%m-%d"), '연도': now.year, '월': now.month,
        '큰 분류': t['큰 분류'], '업무분류': t['업무분류'], '업무세부분류': t['업무세부분류'], '작업량': t['작업량'],
        '시작시간': t['start_time'].strftime("%H:%M"), '끝시간': now.strftime("%H:%M"),
        '총 시간(분)': total_minutes, '실제 일한 시간(분)': actual_minutes, '단위 소요시간(분/개)': unit_time
    }])

    pd.concat([df, new_record], ignore_index=True).to_excel(FILE_NAME, index=False)
    del st.session_state.tasks[task_id]

# --- 건강 기록 함수 ---
def log_health(item_name, earned_minutes):
    now = datetime.now()
    df = pd.read_excel(HEALTH_FILE_NAME) if os.path.exists(HEALTH_FILE_NAME) else pd.DataFrame(columns=['날짜', '시간', '건강항목', '획득시간(분)'])
    new_record = pd.DataFrame([{'날짜': now.strftime("%Y-%m-%d"), '시간': now.strftime("%H:%M:%S"), '건강항목': item_name, '획득시간(분)': earned_minutes}])
    pd.concat([df, new_record], ignore_index=True).to_excel(HEALTH_FILE_NAME, index=False)

# ==========================================
# 1. 관리자 화면 
# ==========================================
if st.session_state.admin_mode:
    st.subheader("⚙️ 관리자 메뉴")
    admin_tab1, admin_tab2, admin_tab3, admin_tab4 = st.tabs(["📂 데이터", "🏷️ 분류", "💪 건강", "⏰ 시간"])
    
    with admin_tab1:
        st.write("**📊 단위 작업 평균 소요시간**")
        if os.path.exists(FILE_NAME): 
            df_all = pd.read_excel(FILE_NAME)
            if not df_all.empty:
                unit_df = df_all.groupby(['큰 분류', '업무분류', '업무세부분류']).agg({
                    '작업량': 'sum', '실제 일한 시간(분)': 'sum'
                }).reset_index()
                unit_df = unit_df[unit_df['작업량'] > 0]
                unit_df['1개당 평균(분)'] = (unit_df['실제 일한 시간(분)'] / unit_df['작업량']).round(1)
                st.dataframe(unit_df[['큰 분류', '업무분류', '업무세부분류', '작업량', '1개당 평균(분)']], use_container_width=True)
            
        st.markdown("---")
        st.write("**전체 원본 데이터**")
        if os.path.exists(FILE_NAME): st.dataframe(pd.read_excel(FILE_NAME), use_container_width=True, height=200)
            
    with admin_tab2:
        new_cat = st.text_input("새로운 업무 분류 추가")
        if st.button("➕ 추가") and new_cat not in st.session_state.categories:
            st.session_state.categories.append(new_cat)
            save_categories(st.session_state.categories)
            st.rerun()
        for cat in st.session_state.categories:
            c1, c2 = st.columns([8, 2])
            c1.write(f"- {cat}")
            if c2.button("❌", key=f"del_cat_{cat}"):
                st.session_state.categories.remove(cat)
                save_categories(st.session_state.categories)
                st.rerun()

    with admin_tab3:
        hc1, hc2, hc3 = st.columns([4, 4, 2])
        new_h_name = hc1.text_input("항목명")
        new_h_time = hc2.number_input("시간(분)", min_value=1, value=10)
        if hc3.button("➕") and new_h_name:
            st.session_state.health_settings[new_h_name] = new_h_time
            save_settings(HEALTH_SETTING_FILE, st.session_state.health_settings)
            st.rerun()
        for h_name, h_time in st.session_state.health_settings.items():
            cc1, cc2 = st.columns([8, 2])
            cc1.write(f"**{h_name}** / **{h_time}분**")
            if cc2.button("❌", key=f"del_h_{h_name}"):
                del st.session_state.health_settings[h_name]
                save_settings(HEALTH_SETTING_FILE, st.session_state.health_settings)
                st.rerun()
                
    with admin_tab4:
        st.write("**하루 전체 통계 기준 시간**")
        w_start = st.text_input("시작 (HH:MM)", value=st.session_state.app_settings['work_start'])
        w_end = st.text_input("종료 (HH:MM)", value=st.session_state.app_settings['work_end'])
        if st.button("💾 기준 시간 저장"):
            st.session_state.app_settings['work_start'] = w_start
            st.session_state.app_settings['work_end'] = w_end
            save_settings(APP_SETTING_FILE, st.session_state.app_settings)
            st.success("저장 완료!")

# ==========================================
# 2. 메인 화면 
# ==========================================
else:
    tab1, tab2, tab3, tab4 = st.tabs(["▶️ 1작업중", "📝 2작업", "💪 3건강", "📊 4통계"])
    
    with tab1:
        if not st.session_state.tasks:
            st.info("실행 중인 작업이 없습니다.")
        for task_id, t_info in list(st.session_state.tasks.items()):
            st.markdown(f"**[{t_info['큰 분류']}] {t_info['업무분류']} - {t_info['업무세부분류']}**")
            col_b1, col_b2 = st.columns(2)
            if t_info['status'] == 'running':
                if col_b1.button("⏸️ 멈춤", key=f"p_{task_id}"): pause_task(task_id); st.rerun()
            else:
                if col_b1.button("▶️ 재시작", key=f"r_{task_id}"): resume_task(task_id); st.rerun()
            if col_b2.button("⏹️ 저장", key=f"e_{task_id}"): end_task(task_id); st.rerun()
            st.markdown("---")

    with tab2:
        with st.form("start_form"):
            main_cat = st.selectbox("큰 분류", st.session_state.categories)
            c1, c2 = st.columns(2)
            task = c1.text_input("업무분류")
            sub_task = c2.text_input("업무세부분류")
            amount = st.number_input("목표량(개)", min_value=1, value=1, step=1)
            if st.form_submit_button("타이머 시작"):
                if task and sub_task:
                    create_task(main_cat, task, sub_task, amount)
                    st.success("시작됨!")

    # --- 💡 탭 3: 2열 배치 및 진행률 바(블럭) 버튼으로 진화 ---
    with tab3:
        today_health_counts = {}
        if os.path.exists(HEALTH_FILE_NAME):
            hdf = pd.read_excel(HEALTH_FILE_NAME)
            hdf_today = hdf[hdf['날짜'] == datetime.now().strftime("%Y-%m-%d")]
            today_health_counts = hdf_today.groupby('건강항목').size().to_dict()

        items = list(st.session_state.health_settings.items())
        
        # 2열(바둑판) 배치를 위해 리스트를 2개씩 짝지어 출력합니다.
        for i in range(0, len(items), 2):
            cols = st.columns(2)
            
            # 첫 번째 열
            h_name, h_time = items[i]
            count = today_health_counts.get(h_name, 0)
            is_vitamin = "비타민" in h_name or "vitamin" in h_name.lower()
            
            with cols[0]:
                if is_vitamin:
                    if count >= 1:
                        btn_label = f"✅ {h_name}\n[ 완료됨 ]"
                        is_disabled = True
                    else:
                        btn_label = f"💊 {h_name}\n(+{h_time}분 획득)"
                        is_disabled = False
                else:
                    blocks = "🟦" * count
                    btn_label = f"{h_name}\n{count}회 {blocks}"
                    is_disabled = False
                    
                if st.button(btn_label, key=f"do_{h_name}", disabled=is_disabled, use_container_width=True):
                    log_health(h_name, h_time)
                    st.rerun()
            
            # 두 번째 열 (홀수 번째 아이템이 있을 때만 렌더링)
            if i + 1 < len(items):
                h_name2, h_time2 = items[i + 1]
                count2 = today_health_counts.get(h_name2, 0)
                is_vitamin2 = "비타민" in h_name2 or "vitamin" in h_name2.lower()
                
                with cols[1]:
                    if is_vitamin2:
                        if count2 >= 1:
                            btn_label2 = f"✅ {h_name2}\n[ 완료됨 ]"
                            is_disabled2 = True
                        else:
                            btn_label2 = f"💊 {h_name2}\n(+{h_time2}분 획득)"
                            is_disabled2 = False
                    else:
                        blocks2 = "🟦" * count2
                        btn_label2 = f"{h_name2}\n{count2}회 {blocks2}"
                        is_disabled2 = False
                        
                    if st.button(btn_label2, key=f"do_{h_name2}", disabled=is_disabled2, use_container_width=True):
                        log_health(h_name2, h_time2)
                        st.rerun()

    with tab4:
        today_str = datetime.now().strftime("%Y-%m-%d")
        now = datetime.now()
        
        start_str = st.session_state.app_settings['work_start']
        end_str = st.session_state.app_settings['work_end']
        
        start_dt = datetime.strptime(f"{today_str} {start_str}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{today_str} {end_str}", "%Y-%m-%d %H:%M")
        total_window_mins = max(1, int((end_dt - start_dt).total_seconds() / 60))
        
        if now < start_dt: elapsed_mins = 0
        elif now > end_dt: elapsed_mins = total_window_mins
        else: elapsed_mins = int((now - start_dt).total_seconds() / 60)

        earned_time = 0
        spent_time = 0
        hdf_today = pd.DataFrame()
        tdf_today = pd.DataFrame()
        
        if os.path.exists(HEALTH_FILE_NAME):
            hdf = pd.read_excel(HEALTH_FILE_NAME)
            hdf_today = hdf[hdf['날짜'] == today_str]
            if not hdf_today.empty: earned_time = hdf_today['획득시간(분)'].sum()
                
        if os.path.exists(FILE_NAME):
            tdf = pd.read_excel(FILE_NAME)
            tdf_today = tdf[tdf['날짜'] == today_str]
            if not tdf_today.empty: spent_time = tdf_today['실제 일한 시간(분)'].sum()

        if spent_time > earned_time:
            st.error(f"🚨 시간 부족! 확보({earned_time}분) < 사용({spent_time}분)")
        else:
            st.success(f"✨ 밸런스 굿! 잔여 시간 **{earned_time - spent_time}분**")
        
        overview_df = pd.DataFrame({
            '지표': ['경과', '운동', '업무'],
            '시간(분)': [elapsed_mins, earned_time, spent_time]
        }).set_index('지표')
        st.bar_chart(overview_df, height=150)

        hours_list = [f"{h:02d}시" for h in range(7, 24)]
        hourly_df = pd.DataFrame(index=hours_list, columns=['운동', '업무']).fillna(0)
        
        if not hdf_today.empty:
            for _, row in hdf_today.iterrows():
                h_hour = int(str(row['시간']).split(':')[0])
                if 7 <= h_hour <= 23: hourly_df.at[f"{h_hour:02d}시", '운동'] += row['획득시간(분)']
                    
        if not tdf_today.empty:
            for _, row in tdf_today.iterrows():
                w_hour = int(str(row['끝시간']).split(':')[0])
                if 7 <= w_hour <= 23: hourly_df.at[f"{w_hour:02d}시", '업무'] += row['실제 일한 시간(분)']
        
        st.line_chart(hourly_df, height=150)

# ==========================================
# 3. 하단 관리자 모드 버튼
# ==========================================
st.markdown("---")
if st.button("⚙️ 관리자 모드 열기/닫기", use_container_width=True):
    st.session_state.admin_mode = not st.session_state.admin_mode
    st.rerun()
