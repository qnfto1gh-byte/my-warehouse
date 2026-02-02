import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import streamlit.components.v1 as components
import urllib.parse
import time

# 앱 설정
st.set_page_config(page_title="창고관리", layout="wide")

# 1. 포커스 이동 및 숫자패드 최적화 (유지)
components.html("""
    <script>
    const doc = window.parent.document;
    doc.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.keyCode === 13) {
            const active = doc.activeElement;
            const inputs = Array.from(doc.querySelectorAll('input'));
            const index = inputs.indexOf(active);
            if (index > -1 && index < inputs.length - 1) {
                e.preventDefault();
                inputs[index + 1].focus();
            }
        }
    }, true);
    setInterval(() => {
        doc.querySelectorAll('input').forEach(input => {
            const label = input.getAttribute('aria-label');
            if (label && (label.includes('유통기한') || label.includes('수량') || label.includes('무게'))) {
                input.setAttribute('inputmode', 'numeric');
                input.setAttribute('pattern', '[0-9]*');
            }
        });
    }, 500);
    </script>
""", height=0)

# 데이터 초기화
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=["물품명", "개수", "유통기한", "총 무게", "단위"])
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["일시", "물품명", "유형", "수량", "상태"])

today = datetime.now().date()
now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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

# --- [1. 작업로그] ---
with st.expander("🔍 작업로그", expanded=False):
    if not st.session_state.history.empty:
        st.dataframe(st.session_state.history.sort_values("일시", ascending=False), use_container_width=True)
    else:
        st.info("기록된 로그가 없습니다.")

st.divider()

# --- [2. 🚨 유통기한 위험 물자 (7일 이내 모아보기)] ---
st.subheader("⚠️ 유통기한 임박 리스트 (7일 이내)")
if not st.session_state.inventory.empty:
    df_alert = st.session_state.inventory.copy()
    df_alert['dt'] = pd.to_datetime(df_alert['유통기한']).dt.date
    # 오늘 기준 7일 이내인 것들 필터링
    urg_items = df_alert[df_alert['dt'] <= today + timedelta(days=7)].sort_values('dt')
    
    if not urg_items.empty:
        with st.container(border=True):
            for _, r in urg_items.iterrows():
                d_day = (r['dt'] - today).days
                d_txt = f"D-{d_day}" if d_day > 0 else ("오늘만료" if d_day == 0 else f"만료 D+{-d_day}")
                st.error(f"**[{d_txt}]** {r['물품명']} | {r['개수']}개 남음 | 기한: {r['유통기한']}")
    else:
        st.success("✅ 7일 이내 만료되는 물자가 없습니다.")
else:
    st.info("창고에 등록된 물자가 없습니다.")

st.divider()

# --- [3. 기간별 정산 보고] ---
# (기간 설정 및 카톡 보고 기능 유지)
with st.container(border=True):
    st.subheader("📅 기간별 정산 보고")
    date_range = st.date_input("정산 기간 선택", value=(today - timedelta(days=7), today))
    if len(date_range) == 2:
        start_d, end_d = date_range
        if st.button(f"📊 {start_d} ~ {end_d} 결과 생성"):
            df_h = st.session_state.history.copy()
            if not df_h.empty:
                df_h['날짜'] = pd.to_datetime(df_h['일시']).dt.date
                period_data = df_h[(df_h['날짜'] >= start_d) & (df_h['날짜'] <= end_d)]
                if not period_data.empty:
                    stats = period_data.groupby(['물품명', '유형'])['수량'].sum().unstack(fill_value=0)
                    if '입고' not in stats: stats['입고'] = 0
                    if '불출' not in stats: stats['불출'] = 0
                    st.table(stats[['입고', '불출']])
                    report_msg = f"📦 [창고관리 정산 보고]\n📅 기간: {start_d} ~ {end_d}\n"
                    for item in stats.index:
                        report_msg += f"🔹 {item}: 입고 {stats.loc[item, '입고']} / 불출 {stats.loc[item, '불출']}\n"
                    st.code(report_msg, language="text")

st.divider()

# --- [4. 신규 물자 등록] ---
with st.expander("➕ 신규 물자 등록", expanded=True):
    with st.form("inventory_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        name = col1.text_input("물품명")
        qty = col2.number_input("입고 수량", min_value=1, value=1)
        col3, col4 = st.columns(2)
        d6 = col3.text_input("유통기한 (YYMMDD)", max_chars=6)
        wgt = col4.number_input("단위당 무게/부피", min_value=0)
        unit = st.selectbox("단위", ["g", "mL", "kg", "L"])
        if st.form_submit_button("🚀 창고에 등록하기", use_container_width=True):
            if name and len(d6) == 6:
                try:
                    f_dt = f"20{d6[:2]}-{d6[2:4]}-{d6[4:]}"
                    new_inv = pd.DataFrame([[name, int(qty), f_dt, int(wgt*qty), unit]], columns=st.session_state.inventory.columns)
                    st.session_state.inventory = pd.concat([st.session_state.inventory, new_inv], ignore_index=True)
                    new_log = pd.DataFrame([[now_time, name, "입고", int(qty), "정상"]], columns=st.session_state.history.columns)
                    st.session_state.history = pd.concat([st.session_state.history, new_log], ignore_index=True)
                    st.success(f"✅ {name} 등록 완료!")
                    time.sleep(0.5)
                    st.rerun()
                except: st.error("날짜 입력 오류!")

# --- [5. 현재고 현황 및 불출] ---
st.subheader("📦 현재 창고 재고 현황")
if not st.session_state.inventory.empty:
    df_m = st.session_state.inventory.copy()
    df_m['dt'] = pd.to_datetime(df_m['유통기한']).dt.date
    for item in df_m['물품명'].unique():
        i_df = df_m[df_m['물품명'] == item].sort_values('dt')
        t_qty = int(i_df['개수'].sum())
        min_d = i_df['dt'].min()
        with st.expander(f"📦 {item} | 총 {t_qty}개 | {min_d} | {get_total_display(i_df)}"):
            st.table(i_df[["개수", "유통기한"]])
            c1, c2 = st.columns([2, 1])
            rem_qty = c1.number_input(f"불출 개수", min_value=1, max_value=t_qty, key=f"del_{item}")
            if c2.button("불출 확정", key=f"btn_{item}"):
                new_log = pd.DataFrame([[now_time, item, "불출", int(rem_qty), "정상"]], columns=st.session_state.history.columns)
                st.session_state.history = pd.concat([st.session_state.history, new_log], ignore_index=True)
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
