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
    urgent = df[df['dt'] <= today + timedelta(days=7)].sort_values('dt')
    if not urgent.empty:
        st.error("🚨 유통기한 임박!")
        for _, r in urgent.iterrows():
            d = (r['dt'] - today).days
            txt = f"D-{d}" if d > 0 else ("오늘" if d == 0 else f"만료 D+{-d}")
            st.write(f"⚠️ {r['물품명']} ({int(r['개수'])}{r['단위']}) - {txt} ({r['유통기한']})")

# 2. 물자 등록
with st.expander("➕ 신규 물자 등록", expanded=False):
    c1, c2, c3 = st.columns([2, 1, 1])
    name = c1.text_input("물품명")
    qty = c2.number_input("개수", min_value=1, step=1, value=1)
    edate = c3.date_input("유통기한")
    c4, c5 = st.columns(2)
    wgt = c4.number_input("단위당 무게", min_value=0, step=1)
    unit = c5.selectbox("단위", ["g", "kg", "L", "mL"])
    if st.button("🚀 등록하기", use_container_width=True):
        if name:
            row = pd.DataFrame([[name, int(qty), edate.strftime('%Y-%m-%d'), int(wgt*qty), unit]], columns=st.session_state.inventory.columns)
            st.session_state.inventory = pd.concat([st.session_state.inventory, row], ignore_index=True)
            st.rerun()

st.divider()

# 3. 현황 리스트 (접기/펴기)
if not st.session_state.inventory.empty:
    df_m = st.session_state.inventory.copy()
    df_m['dt'] = pd.to_datetime(df_m['유통기한']).dt.date
    search = st.text_input("🔍 물품명 검색")
    if search: df_m = df_m[df_m['물품명'].str.contains(search, case=False)]
    
    for item in df_m['물품명'].unique():
        item_df = df_m[df_m['물품명'] == item].sort_values('dt')
        t_qty, t_wgt = item_df['개수'].sum(), item_df['총 무게'].sum()
        min_d = item_df['dt'].min()
        d_val = (min_d - today).days
        d_lab = f"D-{d_val}" if d_val > 0 else ("오늘" if d_val == 0 else f"만료 D+{-d_val}")
        
        with st.expander(f"📦 {item} | 총 {int(t_qty)}개 | 가장 빠른: {min_d} ({d_lab}) | {int(t_wgt)}{item_df['단위'].iloc[0]}"):
            sub = item_df[["개수", "유통기한", "총 무게", "단위"]].copy()
            sub['D-Day'] = item_df['dt'].apply(lambda x: f"D-{(x-today).days}" if (x-today).days > 0 else ("오늘" if (x-today).days==0 else "만료"))
            st.table(sub.style.format({"개수": "{:.0f}", "총 무게": "{:.0f}"}))
            
            st.caption(f"📍 {item} 불출")
            sel_e = st.selectbox("불출할 유통기한", item_df['유통기한'].unique(), key=f"s_{item}")
            m_qty = st.number_input("불출 개수", min_value=1, step=1, key=f"q_{item}")
            if st.button(f"{item} 불출 실행", key=f"b_{item}"):
                idx = item_df[item_df['유통기한'] == sel_e].index[0]
                cur = st.session_state.inventory.at[idx, '개수']
                uw = st.session_state.inventory.at[idx, '총 무게'] / cur
                if m_qty >= cur: st.session_state.inventory = st.session_state.inventory.drop(idx).reset_index(drop=True)
                else:
                    st.session_state.inventory.at[idx, '개수'] -= m_qty
                    st.session_state.inventory.at[idx, '총 무게'] = int(st.session_state.inventory.at[idx, '개수'] * uw)
                st.rerun()
else:
    st.info("물자가 없습니다.")
