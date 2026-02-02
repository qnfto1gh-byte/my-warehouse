import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import time

# 앱 설정 및 이름 변경
st.set_page_config(page_title="창고관리", layout="wide")

# 세션 데이터 초기화
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=["물품명", "개수", "유통기한", "총 무게", "단위"])
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["일시", "물품명", "유형", "수량", "상태"])

today = datetime.now().date()
now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 무게 표시 함수
def get_total_display(df_item):
    total_val = 0
    unit_type = "" 
    for _, row in df_item.iterrows():
        val, u = row['총 무게'], row['단위']
        total_val += val * 1000 if u in ["L", "kg"] else val
        unit_type = "L" if u in ["L", "mL"] else "kg"
    if total_val >= 1000:
        return f"{total_val/1000:.2f}{unit_type}".replace(".00", "")
    return f"{int(total_val)}{'mL' if unit_type == 'L' else 'g'}"

st.title("📦 창고관리 시스템")

# --- [1. 작업 로그: 찐빠 확인용] ---
with st.expander("🔍 작업 로그 (누가 언제 건드렸나?)", expanded=False):
    if not st.session_state.history.empty:
        st.dataframe(st.session_state.history.sort_values("일시", ascending=False), use_container_width=True)
    else:
        st.info("기록된 작업 내역이 없습니다.")

st.divider()

# --- [2. 기간별 정산 보고 (카톡)] ---
st.subheader("📅 기간별 정산 보고")
with st.container(border=True):
    # 사용자님이 원하시는 대로 기간을 직접 설정 (기본값은 최근 7일)
    date_range = st.date_input("정산 시작일과 종료일을 선택하세요", value=(today - timedelta(days=7), today))
    
    if len(date_range) == 2:
        start_d, end_d = date_range
        if st.button(f"🗓️ {start_d} ~ {end_d} 보고서 생성"):
            df_h = st.session_state.history.copy()
            if not df_h.empty:
                df_h['날짜'] = pd.to_datetime(df_h['일시']).dt.date
                period_data = df_h[(df_h['날짜'] >= start_d) & (df_h['날짜'] <= end_d)]
                
                if not period_data.empty:
                    stats = period_data.groupby(['물품명', '유형'])['수량'].sum().unstack(fill_value=0)
                    if '입고' not in stats: stats['입고'] = 0
                    if '불출' not in stats: stats['불출'] = 0
                    
                    report_msg = f"📦 [창고관리 정산 보고]\n📅 기간: {start_d} ~ {end_d}\n"
                    report_msg += "--------------------------\n"
                    for item in stats.index:
                        report_msg += f"🔹 {item}: 입고 {stats.loc[item, '입고']} / 불출 {stats.loc[item, '불출']}\n"
                    report_msg += "--------------------------\n✅ 이상 무."
                    st.code(report_msg, language="text")
                else: st.warning("해당 기간에 데이터가 없습니다.")
            else: st.warning("로그 데이터가 없습니다.")

st.divider()

# --- [3. 신규 물자 등록] ---
with st.expander("➕ 신규 물자 등록 (월/수/금 부식 수령)", expanded=True):
    with st.form("reg_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        name = col1.text_input("물품명")
        qty = col2.number_input("입고 수량", min_value=1, value=1)
        d6 = st.text_input("유통기한 (YYMMDD)")
        col3, col4 = st.columns(2)
        wgt = col3.number_input("단위당 무게/부피", min_value=0)
        unit = col4.selectbox("단위", ["g", "mL", "kg", "L"])
        
        if st.form_submit_button("🚀 창고 등록", use_container_width=True):
            if name and len(d6) == 6:
                f_dt = f"20{d6[:2]}-{d6[2:4]}-{d6[4:]}"
                # 재고 추가
                new_inv = pd.DataFrame([[name, int(qty), f_dt, int(wgt*qty), unit]], columns=st.session_state.inventory.columns)
                st.session_state.inventory = pd.concat([st.session_state.inventory, new_inv], ignore_index=True)
                # 로그 남기기
                new_log = pd.DataFrame([[now_time, name, "입고", int(qty), "정상"]], columns=st.session_state.history.columns)
                st.session_state.history = pd.concat([st.session_state.history, new_log], ignore_index=True)
                st.success(f"{name} 등록 완료!")
                st.rerun()

# --- [4. 현재 재고 및 불출] ---
st.subheader("📦 현재 창고 재고")
if not st.session_state.inventory.empty:
    df_m = st.session_state.inventory.copy()
    df_m['dt'] = pd.to_datetime(df_m['유통기한']).dt.date
    
    # 유통기한 임박 알림
    urg = df_m[df_m['dt'] <= today + timedelta(days=7)]
    if not urg.empty:
        st.error("🚨 유통기한 위험 (7일 이내)")
        for _, r in urg.iterrows():
            st.write(f"⚠️ {r['물품명']} ({r['유통기한']}) D-{(r['dt']-today).days}")

    # 재고 목록
    items = df_m['물품명'].unique()
    for item in items:
        i_df = df_m[df_m['물품명'] == item].sort_values('dt')
        t_qty = int(i_df['개수'].sum())
        min_d = i_df['dt'].min()
        total_w = get_total_display(i_df)
        
        with st.expander(f"📦 {item} | 총 {t_qty}개 | {min_d} (D-{(min_d-today).days}) | {total_w}"):
            st.table(i_df[["개수", "유통기한"]])
            c1, c2 = st.columns([2, 1])
            rem_qty = c1.number_input(f"불출 개수", min_value=1, max_value=t_qty, key=f"q_{item}")
            if c2.button("불출 확정", key=f"b_{item}"):
                # 로그 기록
                new_log = pd.DataFrame([[now_time, item, "불출", int(rem_qty), "정상"]], columns=st.session_state.history.columns)
                st.session_state.history = pd.concat([st.session_state.history, new_log], ignore_index=True)
                # 재고 차감 (선입선출 로직 생략 없이 포함)
                rem = rem_qty
                temp_inv = st.session_state.inventory.copy()
                for idx in i_df.index:
                    if rem <= 0: break
                    curr = temp_inv.at[idx, '개수']
                    u_w = temp_inv.at[idx, '총 무게'] / curr
                    if curr <= rem:
                        rem -= curr
                        temp_inv = temp_inv.drop(idx)
                    else:
                        temp_inv.at[idx, '개수'] -= rem
                        temp_inv.at[idx, '총 무게'] = int(temp_inv.at[idx, '개수'] * u_w)
                        rem = 0
                st.session_state.inventory = temp_inv.reset_index(drop=True)
                st.rerun()
else:
    st.info("창고가 비어있습니다.")
