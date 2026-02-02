import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="부대 창고", layout="wide")

if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=["물품명", "개수", "유통기한", "총 무게", "단위"])

today = datetime.now().date()

# --- 왼쪽 사이드바: 입력창 ---
with st.sidebar:
    st.header("➕ 신규 물자 등록")
    name = st.text_input("물품명", key="n")
    qty = st.number_input("개수", min_value=1, step=1, key="q")
    d6 = st.text_input("유통기한 6자리", placeholder="예: 270917", key="d", max_chars=6)
    
    f_dt = ""
    if len(d6) == 6:
        try:
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

# --- 메인 화면 ---
st.title("📋 창고 현황판")

# 1. 유통기한 임박 알림 (7일 이내만 표시)
if not st.session_state.inventory.empty:
    df_urg = st.session_state.inventory.copy()
    df_urg['dt'] = pd.to_datetime(df_urg['유통기한']).dt.date
    # 오늘 포함 7일 이내인 물자 필터링
    urgent = df_urg[df_urg['dt'] <= today + timedelta(days=7)].sort_values('dt')
    
    if not urgent.empty:
        st.error("🚨 유통기한 임박 (7일 이내)")
        for _, r in urgent.iterrows():
            d = (r['dt'] - today).days
            txt = f"D-{d}" if d > 0 else ("오늘" if d == 0 else f"만료 D+{-d}")
            st.write(f"⚠️ **{r['물품명']}** - {txt} ({r['유통기한']})")
        st.divider()

# 2. 전체 현황판 (요약 정보 복구)
if not st.session_state.inventory.empty:
    df_m = st.session_state.inventory.copy()
    df_m['dt'] = pd.to_datetime(df_m['유통기한']).dt.date
    
    for item in df_m['물품명'].unique():
        i_df = df_m[df_m['물품명'] == item].sort_values('dt')
        
        # 요약 정보 계산
        total_qty = int(i_df['개수'].sum())
        total_wgt = int(i_df['총 무게'].sum())
        min_d = i_df['dt'].min()
        u_type = i_df['단위'].iloc[0]
        
        # D-Day 계산
        d_v = (min_d - today).days
        d_l = f"D-{d_v}" if d_v > 0 else ("오늘" if d_v == 0 else f"만료 D+{-d_v}")
        
        # 리스트 제목에 요약 정보 다시 표시
        with st.expander(f"📦 {item} | 총 {total_qty}개 | 가장 빠른: {min_d} ({d_l}) | 총 {total_wgt}{u_type}"):
            st.table(i_df[["개수", "유통기한", "총 무게", "단위"]])
            
            if st.button(f"{item} 1개 불출", key=f"del_{item}"):
                idx = i_df.index[0] # 가장 빠른 날짜부터 삭제
                if st.session_state.inventory.at[idx, '개수'] > 1:
                    st.session_state.inventory.at[idx, '개수'] -= 1
                    # 무게도 갱신
                    unit_w = st.session_state.inventory.at[idx, '총 무게'] / (st.session_state.inventory.at[idx, '개수'] + 1)
                    st.session_state.inventory.at[idx, '총 무게'] = int(st.session_state.inventory.at[idx, '개수'] * unit_w)
                else:
                    st.session_state.inventory = st.session_state.inventory.drop(idx).reset_index(drop=True)
                st.rerun()
else:
    st.info("왼쪽 사이드바에서 물자를 등록해 주세요.")
