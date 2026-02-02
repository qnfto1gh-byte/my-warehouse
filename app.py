import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="부대 창고", layout="wide")

if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=["물품명", "개수", "유통기한", "총 무게", "단위"])

today = datetime.now().date()

# --- 왼쪽 사이드바: 입력창 고정 ---
with st.sidebar:
    st.header("➕ 신규 물자 등록")
    name = st.text_input("물품명", key="n")
    qty = st.number_input("개수", min_value=1, step=1, key="q")
    d6 = st.text_input("유통기한 6자리", placeholder="예: 270917", key="d", max_chars=6)
    
    # 키보드 튕김 방지를 위해 미리보기를 버튼 바로 위로 이동
    f_dt = ""
    if len(d6) == 6:
        try:
            # 80 미만은 2000년대, 80 이상은 1900년대로 인식
            yy = "20" + d6[:2] if int(d6[:2]) < 80 else "19" + d6[:2]
            f_dt = f"{yy}-{d6[2:4]}-{d6[4:]}"
            datetime.strptime(f_dt, "%Y-%m-%d")
            st.caption(f"✅ 날짜 확인: {f_dt.replace('-', '/')}")
        except:
            st.caption("❌ 날짜를 다시 확인하세요")
            f_dt = "error"

    wgt = st.number_input("단위당 무게", min_value=0, key="w")
    unit = st.selectbox("단위", ["g", "kg", "L", "mL"], key="u")

    if st.button("🚀 창고에 등록하기", use_container_width=True):
        if name and len(d6) == 6 and f_dt != "error":
            row = pd.DataFrame([[name, int(qty), f_dt, int(wgt*qty), unit]], 
                               columns=st.session_state.inventory.columns)
            st.session_state.inventory = pd.concat([st.session_state.inventory, row], ignore_index=True)
            st.rerun()

# --- 메인 화면: 현황판 ---
st.title("📋 창고 현황판")

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

st.divider()

if not st.session_state.inventory.empty:
    df_m = st.session_state.inventory.copy()
    df_m['dt'] = pd.to_datetime(df_m['유통기한']).dt.date
    for item in df_m['물품명'].unique():
        i_df = df_m[df_m['물품명'] == item].sort_values('dt')
        min_d = i_df['dt'].min()
        d_v = (min_d - today).days
        d_l = f"D-{d_v}" if d_v > 0 else ("오늘" if d_v == 0 else f"만료 D+{-d_v}")
        
        with st.expander(f"📦 {item} ({d_l})"):
            st.table(i_df[["개수", "유통기한", "총 무게", "단위"]])
            if st.button(f"{item} 1개 불출", key=f"del_{item}"):
                idx = i_df.index[0]
                if st.session_state.inventory.at[idx, '개수'] > 1:
                    st.session_state.inventory.at[idx, '개수'] -= 1
                else:
                    st.session_state.inventory = st.session_state.inventory.drop(idx).reset_index(drop=True)
                st.rerun()
else:
    st.info("왼쪽 사이드바에서 물자를 등록해 주세요.")
