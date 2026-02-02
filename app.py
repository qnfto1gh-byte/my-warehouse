import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="부대 창고", layout="wide")
st.title("📋 창고 현황판")

if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=["물품명", "개수", "유통기한", "총 무게", "단위"])

today = datetime.now().date()

# 1. 임박 알림 (D-Day)
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

# 2. 물자 등록 (달력 없이 숫자 8자리 입력)
with st.expander("➕ 신규 물자 등록", expanded=False):
    c1, c2, c3 = st.columns([2, 1, 1])
    name = c1.text_input("물품명", key="n")
    qty = c2.number_input("개수", min_value=1, step=1, value=1, key="q")
    d_str = c3.text_input("유통기한 (8자리)", placeholder="예: 20260210", key="d")
    
    c4, c5 = st.columns(2)
    wgt = c4.number_input("단위당 무게", min_value=0, step=1, key="w")
    unit = c5.selectbox("단위", ["g", "kg", "L", "mL"], key="u")
    
    if st.button("🚀 등록하기", use_container_width=True):
        if name and len(d_str) == 8:
            try:
                valid_d = datetime.strptime(d_str, "%Y%m%d").strftime("%Y-%m-%d")
                row = pd.DataFrame([[name, int(qty), valid_d, int(wgt*qty), unit]], columns=st.session_state.inventory.columns)
                st.session_state.inventory = pd.concat([st.session_state.inventory, row], ignore_index=True)
                st.rerun()
            except:
                st.error("❌ 날짜를 확인하세요 (예: 20260210)")
        else:
            st.warning("이름과 날짜 8자리를 확인하세요.")

st.divider()

# 3. 현황 리스트 (접기/펴기)
if not st.session_state.inventory.empty:
    df_m = st.session_state.inventory.copy()
    df_m['dt'] = pd.to_datetime(df_m['유통기한']).dt.date
    
    for item in df_m['물품명'].unique():
        i_df = df_m[df_m['물품명'] == item].sort_values('dt')
        min_d = i_df['dt'].min()
        d_v = (min_d - today).days
        d_l = f"D-{d_v}" if d_v > 0 else ("오늘" if d_v == 0 else f"만료 D+{-d_v}")
        
        with st.expander(f"📦 {item} | 총 {int(i_df['개수'].sum())}개 | 가장 빠른: {min_d} ({d_l})"):
            sub = i_df[["개수", "유통기한", "총 무게", "단위"]].copy()
            st.table(sub.style.format({"개수": "{:.0f}", "총 무게": "{:.0f}"}))
            
            st.caption(f"📍 {item} 불출")
            sel_e = st.selectbox("불출 유통기한 선택", i_df['유통기한'].unique(), key=f"s_{item}")
            m_qty = st.number_input("불출 개수", min_value=1, step=1, key=f"mq_{item}")
            if st.button(f"{item} 불출 실행", key=f"b_{item}"):
                idx = i_df[i_df['유통기한'] == sel_e].index[0]
                cur = st.session_state.inventory.at[idx, '개수']
                uw = st.session_state.inventory.at[idx, '총 무게'] / cur
                if m_qty >= cur:
                    st.session_state.inventory = st.session_state.inventory.drop(idx).reset_index(drop=True)
                else:
                    st.session_state.inventory.at[idx, '개수'] -= m_qty
                    st.session_state.inventory.at[idx, '총 무게'] = int(st.session_state.inventory.at[idx, '개수'] * uw)
                st.rerun()
else:
    st.info("물자가 없습니다.")
