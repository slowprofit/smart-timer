import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import uuid
import time
import gspread
from google.oauth2.service_account import Credentials

# --- 한국 표준시(KST) 변환 함수 ---
def get_now():
    kst = timezone(timedelta(hours=9))
    return datetime.now(kst).replace(tzinfo=None)

# --- 모바일 최적화 및 커스텀 사각 버튼 CSS ---
st.markdown("""
    <style>
    /* 여백을 극한으로 줄여서 모바일 화면 낭비 최소화 */
    .block-container {
        padding-top: 3.5rem !important; 
        padding-bottom: 1rem !important;
        padding-left: 0.3rem !important;
        padding-right: 0.3rem !important;
        max-width: 100vw !important;
        overflow-x: hidden !important; 
    }
    .stTabs [data-baseweb="tab-list"] { gap: 3px; }
    .stTabs [data-baseweb="tab"] { padding: 8px 6px !important; font-size: 13px !important; }
    div[data-testid="stForm"] { padding: 10px !important; }
    h1, h2, h3 { margin-bottom: 0.2rem !important; }
    
    /* 버튼 초소형화 (텍스트 길이에 맞춰 찌그러지지 않게) */
    .stButton>button {
        height: 40px !important; 
        white-space: nowrap !important; 
        border-radius: 8px !important;
        font-weight: bold;
        font-size: 13px !important;
        padding: 0px 2px !important; 
        width: 100% !important;
        min-width: 0px !important;
    }
    
    /* 🔥 1번 탭: 컬럼 강제 가로 배치 및 가로 스크롤 절대 차단 */
    @media (max-width: 768px) {
        div[data-testid="stHorizontalBlock"] {
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            width: 100% !important;
            gap: 4px !important;
            overflow: hidden !important;
        }
        div[data-testid="column"] {
            width: auto !important;
            min-width: 0 !important;
        }
        /* 각 열의 너비 비율 강제 고정 (작업명 4.5 : 멈춤 3.5 : 저장 2) */
        div[data-testid="column"]:nth-child(1) { flex: 4.5 !important; }
        div[data-testid="column"]:nth-child(2) { flex: 3.5 !important; }
        div[data-testid="column"]:nth-child(3) { flex: 2 !important; }
    }
    </style>
""", unsafe_allow_html=True)

# --- 구글 스프레드시트 연결 함수 ---
@st.cache_resource
def init_google_sheets():
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds_dict = dict(st.secrets)
    if "private_key" in creds_dict:
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    gc = gspread.authorize(creds)
    sh = gc.open('time_management')
    return sh

sh = init_google_sheets()

def get_or_create_sheet(sheet_name, headers):
    try:
        return sh.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=sheet_name, rows="1000", cols="20")
        ws.append_row(headers)
        return ws

ws_tasks = get_or_create_sheet('Tasks', ['날짜', '연도', '월', '큰 분류', '업무분류', '업무세부분류', '작업량', '시작시간', '끝시간', '총 시간(분)', '실제 일한 시간(분)', '단위 소요시간(분/개)'])
ws_health = get_or_create_sheet('Health', ['날짜', '시간', '건강항목', '획득시간(분)'])
ws_config = get_or_create_sheet('Config', ['Category', 'Key', 'Value'])
# 🔥 진행 중인 작업을 영구 저장하는 시트 추가 (새로고침 방어용)
ws_running = get_or_create_sheet('RunningTasks', ['task_id', '큰 분류', '업무분류', '업무세부분류', '작업량', 'status', 'start_time', 'last_resume_time', 'actual_seconds'])

# --- 설정 관리 ---
def load_all_config():
    records = ws_config.get_all_records()
    cats = ['카페', '온라인', '개인', '집안일']
    h_set = {'pushup': 20, 'drink water': 4, 'take vitamins': 20}
    a_set = {'work_start': '10:00', 'work_end': '21:00'}
    if records:
        temp_cats = [str(r['Value']) for r in records if r['Category'] == 'Cats']
        if temp_cats: cats = temp_cats
        h_records = [r for r in records if r['Category'] == 'Health']
        if h_records: h_set = {str(r['Key']): int(r['Value']) for r in h_records}
        a_records = [r for r in records if r['Category'] == 'App']
        if a_records: a_set = {str(r['Key']): str(r['Value']) for r in a_records}
    return cats, h_set, a_set

def save_all_config(cats, h_set, a_set):
    data = [['Category', 'Key', 'Value']]
    for c in cats: data.append(['Cats', '', c])
    for k, v in h_set.items(): data.append(['Health', k, v])
    for k, v in a_set.items(): data.append(['App', k, v])
    ws_config.clear()
    ws_config.append_rows(data)

# 🔥 구글 시트에 진행 중인 작업 동기화 함수
def sync_running_tasks():
    data = [['task_id', '큰 분류', '업무분류', '업무세부분류', '작업량', 'status', 'start_time', 'last_resume_time', 'actual_seconds']]
    for tid, t in st.session_state.tasks.items():
        data.append([
            tid, t['큰 분류'], t['업무분류'], t['업무세부분류'], t['작업량'],
            t['status'], 
            t['start_time'].strftime("%Y-%m-%d %H:%M:%S"),
            t['last_resume_time'].strftime("%Y-%m-%d %H:%M:%S"),
            t['actual_seconds']
        ])
    ws_running.clear()
    ws_running.append_rows(data)

# --- 세션 초기화 및 진행 중인 작업 복구 ---
if 'config_loaded' not in st.session_state:
    c, h, a = load_all_config()
    st.session_state.categories = c
    st.session_state.health_settings = h
    st.session_state.app_settings = a
    st.session_state.config_loaded = True

if 'tasks' not in st.session_state:
    st.session_state.tasks = {}
    records = ws_running.get_all_records()
    for r in records:
        st_time = datetime.strptime(str(r['start_time']), "%Y-%m-%d %H:%M:%S")
        lr_time = datetime.strptime(str(r['last_resume_time']), "%Y-%m-%d %H:%M:%S")
        st.session_state.tasks[str(r['task_id'])] = {
            '큰 분류': str(r['큰 분류']), '업무분류': str(r['업무분류']), 
            '업무세부분류': str(r['업무세부분류']), '작업량': int(r['작업량']),
            'status': str(r['status']), 'start_time': st_time, 
            'last_resume_time': lr_time, 'actual_seconds': float(r['actual_seconds'])
        }

if 'intro_shown' not in st.session_state: st.session_state.intro_shown = False
if 'admin_mode' not in st.session_state: st.session_state.admin_mode = False

# --- 인트로 화면 ---
if not st.session_state.intro_shown:
    intro = st.empty()
    with intro.container():
        st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #4A4A4A;'>⏱️ 스마트 밸런스 타이머</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #888;'>Created by <b>Minu Minu</b></p>", unsafe_allow_html=True)
    time.sleep(1.5) 
    intro.empty() 
    st.session_state.intro_shown = True

# --- 타이머 제어 로직 (동기화 추가) ---
def create_task(main_cat, task, sub_task, amount):
    task_id = str(uuid.uuid4())[:8]
    now = get_now()
    st.session_state.tasks[task_id] = {
        '큰 분류': main_cat, '업무분류': task, '업무세부분류': sub_task, '작업량': amount, 
        'status': 'running', 'start_time': now, 'last_resume_time': now, 'actual_seconds': 0
    }
    sync_running_tasks()

def pause_task(task_id):
    now = get_now()
    t = st.session_state.tasks[task_id]
    if t['status'] == 'running':
        t['actual_seconds'] += (now - t['last_resume_time']).total_seconds()
        t['status'] = 'paused'
    sync_running_tasks()

def resume_task(task_id):
    t = st.session_state.tasks[task_id]
    if t['status'] == 'paused':
        t['last_resume_time'] = get_now()
        t['status'] = 'running'
    sync_running_tasks()

def end_task(task_id):
    now = get_now()
    t = st.session_state.tasks[task_id]
    if t['status'] == 'running':
        t['actual_seconds'] += (now - t['last_resume_time']).total_seconds()

    total_minutes = max(1, int((now - t['start_time']).total_seconds() / 60))
    actual_minutes = max(1, int(t['actual_seconds'] / 60))
    unit_time = round(actual_minutes / t['작업량'], 1) if t['작업량'] > 0 else 0

    ws_tasks.append_row([
        now.strftime("%Y-%m-%d"), now.year, now.month,
        t['큰 분류'], t['업무분류'], t['업무세부분류'], t['작업량'],
        t['start_time'].strftime("%H:%M"), now.strftime("%H:%M"),
        total_minutes, actual_minutes, unit_time
    ])
    del st.session_state.tasks[task_id]
    sync_running_tasks()

def log_health(item_name, earned_minutes):
    now = get_now()
    ws_health.append_row([
        now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"),
        item_name, earned_minutes
    ])

# ==========================================
# 1. 관리자 화면 
# ==========================================
if st.session_state.admin_mode:
    st.subheader("⚙️ 관리자 메뉴")
    admin_tab1, admin_tab2, admin_tab3, admin_tab4 = st.tabs(["📂 데이터", "🏷️ 분류", "💪 건강", "⏰ 시간"])
    
    with admin_tab1:
        st.write("**📊 단위 작업 평균 소요시간**")
        records = ws_tasks.get_all_records()
        if records:
            df_all = pd.DataFrame(records)
            unit_df = df_all.groupby(['큰 분류', '업무분류', '업무세부분류']).agg({'작업량': 'sum', '실제 일한 시간(분)': 'sum'}).reset_index()
            unit_df = unit_df[unit_df['작업량'] > 0]
            unit_df['1개당 평균(분)'] = (unit_df['실제 일한 시간(분)'] / unit_df['작업량']).round(1)
            st.dataframe(unit_df[['큰 분류', '업무분류', '업무세부분류', '작업량', '1개당 평균(분)']], use_container_width=True)
            st.markdown("---")
            st.write("**전체 원본 데이터 (Tasks 시트)**")
            st.dataframe(df_all, use_container_width=True, height=200)
            
    with admin_tab2:
        new_cat = st.text_input("새로운 업무 분류 추가")
        if st.button("➕ 추가") and new_cat not in st.session_state.categories:
            st.session_state.categories.append(new_cat)
            save_all_config(st.session_state.categories, st.session_state.health_settings, st.session_state.app_settings)
            st.rerun()
        for cat in st.session_state.categories:
            c1, c2 = st.columns([8, 2])
            c1.write(f"- {cat}")
            if c2.button("❌", key=f"del_cat_{cat}"):
                st.session_state.categories.remove(cat)
                save_all_config(st.session_state.categories, st.session_state.health_settings, st.session_state.app_settings)
                st.rerun()

    with admin_tab3:
        hc1, hc2, hc3 = st.columns([4, 4, 2])
        new_h_name = hc1.text_input("항목명")
        new_h_time = hc2.number_input("시간(분)", min_value=1, value=10)
        if hc3.button("➕") and new_h_name:
            st.session_state.health_settings[new_h_name] = new_h_time
            save_all_config(st.session_state.categories, st.session_state.health_settings, st.session_state.app_settings)
            st.rerun()
        for h_name, h_time in st.session_state.health_settings.items():
            cc1, cc2 = st.columns([8, 2])
            cc1.write(f"**{h_name}** / **{h_time}분**")
            if cc2.button("❌", key=f"del_h_{h_name}"):
                del st.session_state.health_settings[h_name]
                save_all_config(st.session_state.categories, st.session_state.health_settings, st.session_state.app_settings)
                st.rerun()
                
    with admin_tab4:
        w_start = st.text_input("시작 (HH:MM)", value=st.session_state.app_settings['work_start'])
        w_end = st.text_input("종료 (HH:MM)", value=st.session_state.app_settings['work_end'])
        if st.button("💾 구글 클라우드에 저장"):
            st.session_state.app_settings['work_start'] = w_start
            st.session_state.app_settings['work_end'] = w_end
            save_all_config(st.session_state.categories, st.session_state.health_settings, st.session_state.app_settings)
            st.success("클라우드 설정 동기화 완료!")

# ==========================================
# 2. 메인 화면 
# ==========================================
else:
    tab1, tab2, tab3, tab4 = st.tabs(["▶️ 1작업중", "📝 2작업", "💪 3건강", "📊 4통계"])
    
    with tab1:
        if not st.session_state.tasks: st.info("실행 중인 작업이 없습니다.")
        for task_id, t_info in list(st.session_state.tasks.items()):
            total_seconds = t_info['actual_seconds']
            if t_info['status'] == 'running':
                total_seconds += (get_now() - t_info['last_resume_time']).total_seconds()
            
            m, s = divmod(int(total_seconds), 60)
            time_display = f"{m:02d}:{s:02d}"

            c1, c2, c3 = st.columns([4.5, 3.5, 2])
            
            with c1:
                st.markdown(f"<div style='line-height:40px; font-size:14px; font-weight:bold; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{t_info['업무세부분류']}</div>", unsafe_allow_html=True)
            with c2:
                if t_info['status'] == 'running':
                    if st.button(f"⏸️ {time_display}", key=f"p_{task_id}", use_container_width=True): 
                        pause_task(task_id)
                        st.rerun()
                else:
                    if st.button(f"▶️ {time_display}", key=f"r_{task_id}", use_container_width=True): 
                        resume_task(task_id)
                        st.rerun()
            with c3:
                if st.button("⏹️ 저장", key=f"e_{task_id}", use_container_width=True): 
                    end_task(task_id)
                    st.rerun()
            
            st.markdown("---")

    with tab2:
        if st.session_state.get('task_started', False):
            st.success("✅ 타이머가 시작되었습니다! '1작업중' 탭에서 확인하세요.")
            st.session_state.task_started = False
            
        with st.form("start_form"):
            main_cat = st.selectbox("큰 분류", st.session_state.categories)
            task = st.text_input("업무분류 (예: 독서, 기획)")
            sub_task = st.text_input("업무세부분류 (예: 1장 읽기)")
            amount = st.number_input("목표량(개)", min_value=1, value=1, step=1)
            
            if st.form_submit_button("🚀 타이머 시작", use_container_width=True):
                if task and sub_task:
                    create_task(main_cat, task, sub_task, amount)
                    st.session_state.task_started = True 
                    st.rerun() 
                else:
                    st.warning("업무분류와 업무세부분류를 모두 입력해주세요.")

    with tab3:
        health_records = ws_health.get_all_records()
        hdf = pd.DataFrame(health_records) if health_records else pd.DataFrame(columns=['날짜', '시간', '건강항목', '획득시간(분)'])
        
        today_str = get_now().strftime("%Y-%m-%d")
        today_health_counts = {}
        if not hdf.empty:
            hdf_today = hdf[hdf['날짜'] == today_str]
            today_health_counts = hdf_today.groupby('건강항목').size().to_dict()

        items = list(st.session_state.health_settings.items())
        
        for i in range(0, len(items), 2):
            cols = st.columns(2)
            h_name, h_time = items[i]
            count = today_health_counts.get(h_name, 0)
            is_vitamin = "비타민" in h_name or "vitamin" in h_name.lower()
            
            with cols[0]:
                if is_vitamin:
                    if count >= 1: btn_label, is_disabled = f"✅ {h_name}\n[ 완료됨 ]", True
                    else: btn_label, is_disabled = f"💊 {h_name}\n(+{h_time}분)", False
                else:
                    btn_label, is_disabled = f"{h_name}\n{count}회 " + ("🟦" * count), False
                    
                if st.button(btn_label, key=f"do_{h_name}", disabled=is_disabled, use_container_width=True):
                    log_health(h_name, h_time)
                    st.rerun()
            
            if i + 1 < len(items):
                h_name2, h_time2 = items[i + 1]
                count2 = today_health_counts.get(h_name2, 0)
                is_vitamin2 = "비타민" in h_name2 or "vitamin" in h_name2.lower()
                
                with cols[1]:
                    if is_vitamin2:
                        if count2 >= 1: btn_label2, is_disabled2 = f"✅ {h_name2}\n[ 완료됨 ]", True
                        else: btn_label2, is_disabled2 = f"💊 {h_name2}\n(+{h_time2}분)", False
                    else:
                        btn_label2, is_disabled2 = f"{h_name2}\n{count2}회 " + ("🟦" * count2), False
                        
                    if st.button(btn_label2, key=f"do_{h_name2}", disabled=is_disabled2, use_container_width=True):
                        log_health(h_name2, h_time2)
                        st.rerun()

    with tab4:
        now = get_now()
        today_str = now.strftime("%Y-%m-%d")
        start_str, end_str = st.session_state.app_settings['work_start'], st.session_state.app_settings['work_end']
        start_dt = datetime.strptime(f"{today_str} {start_str}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{today_str} {end_str}", "%Y-%m-%d %H:%M")
        total_window_mins = max(1, int((end_dt - start_dt).total_seconds() / 60))
        
        if now < start_dt: elapsed_mins = 0
        elif now > end_dt: elapsed_mins = total_window_mins
        else: elapsed_mins = int((now - start_dt).total_seconds() / 60)

        health_records = ws_health.get_all_records()
        hdf = pd.DataFrame(health_records) if health_records else pd.DataFrame(columns=['날짜', '시간', '건강항목', '획득시간(분)'])
        earned_time = 0
        if not hdf.empty:
            hdf_today = hdf[hdf['날짜'] == today_str]
            if not hdf_today.empty: earned_time = int(hdf_today['획득시간(분)'].sum())

        task_records = ws_tasks.get_all_records()
        tdf = pd.DataFrame(task_records) if task_records else pd.DataFrame(columns=['날짜', '끝시간', '실제 일한 시간(분)'])
        spent_work_time = 0
        if not tdf.empty:
            tdf_today = tdf[tdf['날짜'] == today_str]
            if not tdf_today.empty: spent_work_time = int(tdf_today['실제 일한 시간(분)'].sum())

        balance_mins = earned_time - elapsed_mins
        
        if balance_mins < 0:
            st.error(f"🚨 **시간 부족 경고!** 아침부터 흐른 시간({elapsed_mins}분)보다 운동으로 번 시간({earned_time}분)이 적습니다. (부족: {abs(balance_mins)}분)")
        else:
            st.success(f"✨ **밸런스 굿!** 여유 시간 **{balance_mins}분** 남았습니다. (오늘 총 업무 노동 시간: {spent_work_time}분)")
        
        overview_df = pd.DataFrame({
            '지표': ['1. 경과 시간', '2. 운동 확보', '3. 업무 노동'],
            '시간(분)': [elapsed_mins, earned_time, spent_work_time]
        }).set_index('지표')
        st.bar_chart(overview_df, height=150)

        hours_list = [f"{h:02d}시" for h in range(7, 24)]
        hourly_df = pd.DataFrame(index=hours_list, columns=['운동', '업무']).fillna(0)
        
        if not hdf.empty and not hdf_today.empty:
            for _, row in hdf_today.iterrows():
                h_hour = int(str(row['시간']).split(':')[0])
                if 7 <= h_hour <= 23: hourly_df.at[f"{h_hour:02d}시", '운동'] += int(row['획득시간(분)'])
                    
        if not tdf.empty and not tdf_today.empty:
            for _, row in tdf_today.iterrows():
                w_hour = int(str(row['끝시간']).split(':')[0])
                if 7 <= w_hour <= 23: hourly_df.at[f"{w_hour:02d}시", '업무'] += int(row['실제 일한 시간(분)'])
        
        st.line_chart(hourly_df, height=150)

st.markdown("---")
if st.button("⚙️ 관리자 모드 열기/닫기", use_container_width=True):
    st.session_state.admin_mode = not st.session_state.admin_mode
    st.rerun()
