import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="부대 창고", layout="wide")

if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=["물품명", "개수", "유통기한", "총 무게", "단위"])

today = datetime.now().date()

# --- 단위 환산 합산 함수 ---
def get_total_display(df_item):
    total_raw_ml_g = 0
    base_unit_type = "" 
    for _, row in df_item.iterrows():
        val, u = row['총 무게'], row['단위']
        if u == "L": total_raw_ml_g += val * 1000; base_unit_type = "L"
        elif u == "kg": total_raw_ml_g += val * 1000; base_unit_type = "kg"
        elif u == "mL": total_raw_ml_g += val; base_unit_type = "L"
        elif u == "g": total_raw_ml_g += val; base_unit_type = "kg"
    
    if total_raw_ml_g >= 1000:
        res = total_raw_ml_g / 1000
        final_unit = "L" if base_unit_type == "L" else "kg"
        return f"{res:.2f}{final_unit}".replace(".00", "")
    else:
        final_unit = "mL" if base_unit_type == "L" else "g"
        return f"{int(total_raw_ml_g)}{final_unit}"

# --- 사이드바: 입력 ---
with st.sidebar:
    st.header("➕ 신규 물자 등록")
    name = st.text_input("물품명", key="n")
    qty = st.number_input("개수", min_value=1, step=1, key="q")
    d6 = st.text_input("유통기한 6자리", placeholder="270917", key="d", max_chars=6)
    
    f_dt = ""
    if len(d6) == 6:
        try:
            yy = "20" + d6[:2] if int(d6[:2]) < 80 else "19" + d6[:2]
            f_dt = f"{yy}-{d6[2:4]}-{d6[4:]}"
            datetime.strptime(f_dt, "%Y-%m-%d")
            st.caption(f"✅ 날짜 확인: {f_dt}")
        except:
            st.caption("❌ 날짜 오류")
            f_dt = "error"

    wgt = st.number_input("단위당 무게/부피", min_value=0, step=1, key="w")
    unit = st.selectbox("단위", ["g", "mL", "kg", "L"], key="u")

    if st.button("🚀 등록하기", use_container_width=True):
        if name and len(d6) == 6 and f_dt != "error":
            row = pd.DataFrame([[name, int(qty), f_dt, int(wgt*qty), unit]], columns=st.session_state.inventory.columns)
            st.session_state.inventory = pd.concat([st.session_state.inventory, row], ignore_index=True)
            st.rerun()

# --- 메인 화면 ---
st.title("📋 창고 현황판")

# 1. 임박 알림
if not st.session_state.inventory.empty:
    df_u = st.session_state.inventory.copy()
    df_u['dt'] = pd.to_datetime(df_u['유통기한']).dt.date
    urg = df_u[df_u['dt'] <= today + timedelta(days=7)].sort_values('dt')
    if not urg.empty:
        st.error("🚨 유통기한 임박 (7일 이내)")
        for _, r in urg.iterrows():
            d = (r['dt'] - today).days
            txt = f"D-{d}" if d > 0 else ("오늘" if d == 0 else f"만료 D+{-d}")
            st.write(f"⚠️ **{r['물품명']}** - {txt} ({r['유통기한']})")

st.divider()

# 2. 검색창 추가
search = st.text_input("🔍 찾으시는 물품명을 입력하세요", placeholder="검색어 입력...")

# 3. 리스트 현황
if not st.session_state.inventory.empty:
    df_m = st.session_state.inventory.copy()
    df_m['dt'] = pd.to_datetime(df_m['유통기한']).dt.date
    
    # 검색 필터 적용
    target_items = df_m['물품명'].unique()
    if search:
        target_items = [i for i in target_items if search.lower() in i.lower()]

    if not target_items:
        st.warning(f"'{search}' 검색 결과가 없습니다.")
    else:
        for item in target_items:
            i_df = df_m[df_m['물품명'] == item].sort_values('dt')
            t_qty, min_d = int(i_df['개수'].sum()), i_df['dt'].min()
            display_total = get_total_display(i_df)
            d_v = (min_d - today).days
            d_l = f"D-{d_v}" if d_v > 0 else ("오늘" if d_v == 0 else f"만료 D+{-d_v}")
            
            with st.expander(f"📦 {item} | 총 {t_qty}개 | {min_d}({d_l}) | 총량: {display_total}"):
                st.table(i_df[["개수", "유통기한", "총 무게", "단위"]])
                if st.button(f"{item} 1개 불출", key=f"del_{item}"):
                    idx = i_df.index[0]
                    if st.session_state.inventory.at[idx, '개수'] > 1:
                        u_w = st.session_state.inventory.at[idx, '총 무게'] / st.session_state.inventory.at[idx, '개수']
                        st.session_state.inventory.at[idx, '개수'] -= 1
                        st.session_state.inventory.at[idx, '총 무게'] = int(st.session_state.inventory.at[idx, '개수'] * u_w)
                    else:
                        st.session_state.inventory = st.session_state.inventory.drop(idx).reset_index(drop=True)
                    st.rerun()
else:
    st.info("왼쪽 사이드바에서 물자를 등록해 주세요.")
