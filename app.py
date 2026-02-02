import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import streamlit.components.v1 as components
import time

# 앱 설정
st.set_page_config(page_title="창고관리", layout="wide")

# 1. 엔터 이동 & 숫자패드 자동 활성화 (기억!)
components.html("""
    <script>
    const doc = window.parent.document;
    doc.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.keyCode === 13) {
            const active = doc.activeElement;
            const inputs = Array.from(doc.querySelectorAll('input'));
            const index = inputs.indexOf(active);
            if (index > -1 && index < inputs.length - 1) {
                e.preventDefault(); inputs[index + 1].focus();
            }
        }
    }, true);
    setInterval(() => {
        doc.querySelectorAll('input').forEach(input => {
            const label = input.getAttribute('aria-label');
            if (label && (label.includes('유통기한') || label.includes('수량') || label.includes('무게'))) {
                input.setAttribute('inputmode', 'numeric');
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

# [복구] 무게 표시 변환 함수
def get_total_display(df_item):
    total_val = 0
    unit_type = "" 
    for _, row in df_item.iterrows():
        val, u = row['총 무게'], row['단위']
        # 단위를 표준화하여 계산 (kg/L는 1000배)
        total_val += val * 1000 if u in ["L", "kg"] else val
        unit_type = "L" if u in ["L", "mL"] else "kg"
    
    if total_val >= 1000:
        res = total_val / 1000
        return f"{res:.2f}{unit_type}".replace(".00", "")
    else:
        final_u = "mL" if unit_type == "L" else "g"
        return f"{int(total_val)}{final_u}"

st.title("📦 창고관리 시스템")

# --- [1. 작업로그: 접이식 + 날짜별 그룹] ---
with st.expander("🔍 작업로그", expanded=False):
    if not st.session_state.history.empty:
        log_df = st.session_state.history.copy()
        log_df['날짜'] = pd.to_datetime(log_df['일시']).dt.date
        for day in sorted(log_df['날짜'].unique(), reverse=True):
            st.markdown(f"**📅 {day}**")
            st.table(log_df[log_df['날짜'] == day].sort_values("일시", ascending=False)[["일시", "물품명", "유형", "수량"]])
    else: st.info("로그가 없습니다.")

st.divider()

# --- [2. 유통기한 7일 이내 모아보기] ---
st.subheader("⚠️ 유통기한 임박 리스트 (7일 이내)")
if not st.session_state.inventory.empty:
    df_alert = st.session_state.inventory.copy()
    df_alert['dt'] = pd.to_datetime(df_alert['유통기한'], errors='coerce').dt.date
    urg_items = df_alert[df_alert['dt'] <= today + timedelta(days=7)].sort_values('dt')
    if not urg_items.empty:
        for _, r in urg_items.iterrows():
            d_day = (r['dt'] - today).days
            st.error(f"**[D-{d_day if d_day >=0 else '만료'}]** {r['물품명']} | {r['개수']}개 | 기한: {r['유통기한']}")
    else: st.success("임박 물자 없음")

st.divider()

# --- [3. 기간별 정산 보고] ---
with st.expander("📅 기간별 정산 보고"):
    d_range = st.date_input("정산 기간", value=(today - timedelta(days=7), today))
    if len(d_range) == 2:
        s_d, e_d = d_range
        if st.button("📊 보고서 생성"):
            df_h = st.session_state.history.copy()
            if not df_h.empty:
                df_h['날짜'] = pd.to_datetime(df_h['일시']).dt.date
                p_data = df_h[(df_h['날짜'] >= s_d) & (df_h['날짜'] <= e_d)]
                if not p_data.empty:
                    stats = p_data.groupby(['물품명', '유형'])['수량'].sum().unstack(fill_value=0)
                    for c in ['입고', '불출']: 
                        if c not in stats: stats[c] = 0
                    st.table(stats[['입고', '불출']])
                    msg = f"📦 [정산 보고] {s_d}~{e_d}\n"
                    for i in stats.index: msg += f"🔹 {i}: +{stats.loc[i, '입고']}/-{stats.loc[i, '불출']}\n"
                    st.code(msg)

st.divider()

# --- [4. 신규 물자 등록] ---
with st.expander("➕ 신규 물자 등록", expanded=True):
    with st.form("reg_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("물품명")
        qty = c2.number_input("입고 수량", min_value=1)
        c3, c4 = st.columns(2)
        d6 = c3.text_input("유통기한 (YYMMDD)")
        wgt = c4.number_input("단위당 무게/부피", min_value=0)
        unit = st.selectbox("단위", ["g", "mL", "kg", "L"])
        if st.form_submit_button("🚀 등록하기", use_container_width=True):
            if name and len(d6) == 6:
                try:
                    f_dt = f"20{d6[:2]}-{d6[2:4]}-{d6[4:]}"
                    datetime.strptime(f_dt, "%Y-%m-%d")
                    new_inv = pd.DataFrame([[name, int(qty), f_dt, int(wgt*qty), unit]], columns=st.session_state.inventory.columns)
                    st.session_state.inventory = pd.concat([st.session_state.inventory, new_inv], ignore_index=True)
                    new_log = pd.DataFrame([[now_time, name, "입고", int(qty), "정상"]], columns=st.session_state.history.columns)
                    st.session_state.history = pd.concat([st.session_state.history, new_log], ignore_index=True)
                    st.success(f"✅ {name} 등록 완료!")
                    time.sleep(0.5); st.rerun()
                except: st.error("❌ 날짜 확인 (예: 260228)")

st.divider()

# --- [5. 현재고 현황 및 검색] ---
st.subheader("📦 현재 창고 재고 현황")
search = st.text_input("🔍 물품 검색")
if not st.session_state.inventory.empty:
    df_m = st.session_state.inventory.copy()
    items = [i for i in df_m['물품명'].unique() if search.lower() in i.lower()]
    for item in items:
        i_df = df_m[df_m['물품명'] == item].copy()
        i_df['dt'] = pd.to_datetime(i_df['유통기한']).dt.date
        i_df = i_df.sort_values('dt')
        t_qty = int(i_df['개수'].sum())
        min_d = i_df['dt'].min()
        # [복구 확인] 제목에 총 무게 표시
        with st.expander(f"📦 {item} | 총 {t_qty}개 | {min_d} (D-{(min_d-today).days}) | {get_total_display(i_df)}"):
            st.table(i_df[["개수", "유통기한"]])
            c1, c2 = st.columns([2, 1])
            rem_qty = c1.number_input(f"불출 개수", min_value=1, max_value=t_qty, key=f"del_{item}")
            if c2.button("불출 확정", key=f"btn_{item}"):
                new_log = pd.DataFrame([[now_time, item, "불출", int(rem_qty), "정상"]], columns=st.session_state.history.columns)
                st.session_state.history = pd.concat([st.session_state.history, new_log], ignore_index=True)
                # 차감 로직
                rem = rem_qty
                temp_inv = st.session_state.inventory.copy()
                for idx in i_df.index:
                    if rem <= 0: break
                    curr = temp_inv.at[idx, '개수']
                    u_w = temp_inv.at[idx, '총 무게'] / curr
                    if curr <= rem: rem -= curr; temp_inv = temp_inv.drop(idx)
                    else:
                        temp_inv.at[idx, '개수'] -= rem
                        temp_inv.at[idx, '총 무게'] = int(temp_inv.at[idx, '개수'] * u_w)
                        rem = 0
                st.session_state.inventory = temp_inv.reset_index(drop=True)
                st.rerun()
