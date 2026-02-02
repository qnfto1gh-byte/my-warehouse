import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="부대 창고", layout="wide")
st.title("📋 창고 현황판")

if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=["물품명", "개수", "유통기한", "총 무게", "단위"])

today = datetime.now().date()

# 1. 임박 알림
if not st.session_state.inventory.empty:
    df = st.session_state.inventory.copy()
    df['dt'] = pd.to_datetime(df['유통기한']).dt.date
    urg = df[df['dt'] <= today + timedelta(days=7)].sort_values('dt')
    if not urg.empty:
        st.error("🚨 유통기한 임박!")
        for _, r in urg.iterrows():
            d = (r['dt'] - today).days
            txt = f"D-{d}" if d > 0 else ("오늘" if d == 0 else f"만료 D+{-d}")
            st.write(f"⚠️ {r['물품명']} - {txt} ({r['유통기한']})")

# 2. 물자 등록 (연도 로직 수정)
with st.expander("➕ 신규 물자 등록", expanded=False):
    c1, c2, c3 = st.columns([2, 1, 1])
    name = c1.text_input("물품명", key="n")
    qty = c2.number_input("개수", min_value=1, step=1, key="q")
    raw_d = c3.text_input("6자리(YYMMDD)", placeholder="270917", key="d", max_chars=6)
    
    c4, c5 = st.columns(2)
    wgt = c4.number_input("단위당 무게", min_value=0, step=1, key="w")
    unit = c5.selectbox("단위", ["g", "kg", "L", "mL"], key="u")
    
    if st.button("🚀 등록하기", use_container_width=True):
        if name and len(raw_d) == 6:
            try:
                # 80보다 작으면 2000년대, 크면 1900년대로 자동 설정
                yy = "20" + raw_d[:2] if int(raw_d[:2]) < 80 else "19" + raw_d[:2]
                f_dt = f"{yy}-{raw_d[2:4]}-{raw_d[4:]}"
                
                # 날짜가 실제로 존재하는지 검사 (예: 2월 30일 방지)
                datetime.strptime(f_dt, "%Y-%m-%d")
                
                row = pd.DataFrame([[name, int(qty), f_dt, int(wgt*qty), unit]], columns=st.session_state.inventory.columns)
                st.session_state.inventory = pd.concat([st.session_state.inventory, row], ignore_index=True)
                st.rerun()
            except:
                st.error("❌ 존재하지 않는 날짜입니다 (예: 02월 30일)")
        else:
            st.warning("물품명과 숫자 6자리를 확인하세요.")

st.divider()

# 3. 리스트 표시
if not st.session_state.inventory.empty:
    df_m = st.session_state.inventory.copy()
    df_m['dt'] = pd.to_datetime(df_m['유통기한']).dt.date
    for item in df_m['물품명'].unique():
        i_df = df_m[df_m['물품명'] == item].sort_values('dt')
        min_d = i_df['dt'].min()
        d_v = (min_d - today).days
        d_l = f"D-{d_v}" if d_v > 0 else ("오늘" if d_v == 0 else f"만료 D+{-d_v}")
        
        with st.expander(f"📦 {item} | 총 {int(i_df['개수'].sum())}개 | 가장 빠른: {min_d} ({d_l})"):
            st.table(i_df[["개수", "유통기한", "총 무게", "단위"]].style.format({"개수": "{:.0f}", "총 무게": "{:.0f}"}))
            
            # 불출 기능
            sel_e = st.selectbox("불출 날짜 선택", i_df['유통기한'].unique(), key=f"s_{item}")
            m_qty = st.number_input("불출 개수", min_value=1, step=1, key=f"mq_{item}")
            if st.button(f"{item} 불출", key=f"
