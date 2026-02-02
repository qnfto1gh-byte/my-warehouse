import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="창고 현황", layout="wide")
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
        st.error("🚨 유통기한 임박 물자!")
        for _, r in urg.iterrows():
            d = (r['dt'] - today).days
            txt = f"D-{d}" if d > 0 else ("오늘" if d == 0 else f"만료 D+{-d}")
            st.write(f"⚠️ {r['물품명']} - {txt} ({r['유통기한']})")

# 2. 등록 (6자리 입력 -> 2000년대로 고정)
with st.expander("➕ 물자 등록", expanded=False):
    n = st.text_input("물품명")
    q = st.number_input("개수", min_value=1, step=1)
    d6 = st.text_input("유통기한 6자리 (예: 270917)", max_chars=6)
    
    # 미리보기 기능 (사용자님 확인용)
    f_dt = ""
    if len(d6) == 6:
        f_dt = f"20{d6[:2]}-{d6[2:4]}-{d6[4:]}"
        st.info(f"입력 날짜: {f_dt}")

    c1, c2 = st.columns(2)
    w = c1.number_input("단위당 무게", min_value=0)
    u = c2.selectbox("단위", ["g", "kg", "L", "mL"])
    
    if st.button("🚀 등록", use_container_width=True):
        if n and len(d6) == 6:
            try:
                datetime.strptime(f_dt, "%Y-%m-%d") # 날짜 유효성 체크
                row = pd.DataFrame([[n, int(q), f_dt, int(w*q), u]], columns=st.session_state.inventory.columns)
                st.session_state.inventory = pd.concat([st.session_state.inventory, row], ignore_index=True)
                st.rerun()
            except:
                st.error("❌ 날짜가 이상해요 (예: 2월 30일)")
        else:
            st.warning("이름과 6자리 숫자를 채워주세요.")

st.divider()

# 3. 리스트 (접기 기능)
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
            
            # 불출
            if st.button(f"{item} 1개 불출", key=f"del_{item}"):
                idx = i_df.index[0] # 가장 빠른 날짜부터 삭제
                if st.session_state.inventory.at[idx, '개수'] > 1:
                    st.session_state.inventory.at[idx, '개수'] -= 1
                else:
                    st.session_state.inventory = st.session_state.inventory.drop(idx).reset_index(drop=True)
                st.rerun()
else:
    st.info("물자가 없습니다.")
