import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="부대 창고", layout="wide")

if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=["물품명", "개수", "유통기한", "총 무게", "단위"])

today = datetime.now().date()

# --- 단위 변환 함수 (1000 이상일 때 kg/L로 변환) ---
def format_weight(value, unit):
    if value >= 1000:
        new_value = value / 1000
        new_unit = "kg" if unit in ["g", "kg"] else "L"
        # 소수점이 있으면 1.4L, 없으면 1L로 깔끔하게 표시
        return f"{new_value:.1f}{new_unit}".replace(".0", "")
    return f"{int(value)}{unit}"

# --- 왼쪽 사이드바: 입력창 ---
with st.sidebar:
    st.header("➕ 신규 물자 등록")
    name = st.text_input("물품명", key="n")
    # 등록 시에는 소수점 없이 정수로 입력
    qty = st.number_input("개수", min_value=1, step=1, key="q")
    d6 = st.text_input("유통기한 6자리", placeholder="270917", key="d", max_chars=6)
    
    f_dt = ""
    if len(d6) == 6:
        try:
            yy = "20" + d6[:2] if int(d6[:2]) < 80 else "19" + d6[:2]
            f_dt = f"{yy}-{d6[2:4]}-{d6[4:]}"
            datetime.strptime(f_dt, "%Y-%m-%d")
            st.caption(f"✅ 날짜 확인: {f_dt.replace('-', '/')}")
        except:
            st.caption("❌ 날짜 오류")
            f_dt = "error"

    wgt = st.number_input("단위당 무게 (정수)", min_value=0, step=1, key="w")
    unit = st.selectbox("단위", ["g", "mL", "kg", "L"], key="u")

    if st.button("🚀 창고에 등록하기", use_container_width=True):
        if name and len(d6) == 6 and f_dt != "error":
            # 등록할 때 총 무게는 정수로 저장 (나중에 보여줄 때만 변환)
            row = pd.DataFrame([[name, int(qty), f_dt, int(wgt*qty), unit]], 
                               columns=st.session_state.inventory.columns)
            st.session_state.inventory = pd.concat([st.session_state.inventory, row], ignore_index=True)
            st.rerun()

# --- 메인 화면 ---
st.title("📋 창고 현황판")

# 1. 유통기한 임박 알림 (7일 이내)
if not st.session_state.inventory.empty:
    df_urg = st.session_state.inventory.copy()
    df_urg['dt'] = pd.to_datetime(df_urg['유통기한']).dt.date
    urgent = df_urg[df_urg['dt'] <= today + timedelta(days=7)].sort_values('dt')
    if not urgent.empty:
        st.error("🚨 유통기한 임박 (7일 이내)")
        for _, r in urgent.iterrows():
            d = (r['dt'] - today).days
            txt = f"D-{d}" if d > 0 else ("오늘" if d == 0 else f"만료 D+{-d}")
            st.write(f"⚠️ **{r['물품명']}** - {txt} ({r['유통기한']})")
        st.divider()

# 2. 전체 현황판 (단위 변환 적용)
if not st.session_state.inventory.empty:
    df_m = st.session_state.inventory.copy()
    df_m['dt'] = pd.to_datetime(df_m['유통기한']).dt.date
    
    for item in df_m['물품명'].unique():
        i_df = df_m[df_m['물품명'] == item].sort_values('dt')
        
        t_qty = int(i_df['개수'].sum())
        t_wgt_raw = i_df['총 무게'].sum() # 계산용 원본 숫자
        min_d = i_df['dt'].min()
        u_type = i_df['단위'].iloc[0]
        
        # 단위 변환 함수 적용 (예: 1400mL -> 1.4L)
        display_wgt = format_weight(t_wgt_raw, u_type)
        
        d_v = (min_d - today).days
        d_l = f"D-{d_v}" if d_v > 0 else ("오늘" if d_v == 0 else f"만료 D+{-d_v}")
        
        # 제목에 변환된 무게 표시
        with st.expander(f"📦 {item} | 총 {t_qty}개 | {min_d} ({d_l}) | 무게 합: {display_wgt}"):
            # 테이블 안에서도 보기 좋게 변환
            sub_df = i_df[["개수", "유통기한", "총 무게", "단위"]].copy()
            st.table(sub_df)
            
            if st.button(f"{item} 1개 불출", key=f"del_{item}"):
                idx = i_df.index[0]
                if st.session_state.inventory.at[idx, '개수'] > 1:
                    unit_w = st.session_state.inventory.at[idx, '총 무게'] / st.session_state.inventory.at[idx, '개수']
                    st.session_state.inventory.at[idx, '개수'] -= 1
                    st.session_state.inventory.at[idx, '총 무게'] = int(st.session_state.inventory.at[idx, '개수'] * unit_w)
                else:
                    st.session_state.inventory = st.session_state.inventory.drop(idx).reset_index(drop=True)
                st.rerun()
else:
    st.info("왼쪽 사이드바에서 물자를 등록해 주세요.")
