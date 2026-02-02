import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="부대 창고", layout="wide")

# 데이터 유지 확인
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

# --- 메인 화면 시작 ---
st.title("📋 창고 현황판")

# 1. 물자 등록 창 (입력창 초기화 옵션 해제하여 안전성 강화)
with st.expander("➕ 신규 물자 등록", expanded=False):
    # clear_on_submit을 False로 바꿔서 실수로 엔터 쳐도 내용이 남게 함
    with st.form("input_form", clear_on_submit=False):
        name = st.text_input("1. 물품명")
        qty = st.number_input("2. 입고 개수", min_value=1, step=1)
        d6 = st.text_input("3. 유통기한 6자리 (YYMMDD)", max_chars=6)
        wgt = st.number_input("4. 단위당 무게/부피 (정수)", min_value=0, step=1)
        unit = st.selectbox("5. 단위", ["g", "mL", "kg", "L"])
        
        submit_button = st.form_submit_button("🚀 창고에 등록하기", use_container_width=True)
        
        if submit_button:
            if name and len(d6) == check_len := 6:
                try:
                    yy = "20" + d6[:2] if int(d6[:2]) < 80 else "19" + d6[:2]
                    f_dt = f"{yy}-{d6[2:4]}-{d6[4:]}"
                    datetime.strptime(f_dt, "%Y-%m-%d")
                    
                    new_data = pd.DataFrame([[name, int(qty), f_dt, int(wgt*qty), unit]], 
                                       columns=st.session_state.inventory.columns)
                    st.session_state.inventory = pd.concat([st.session_state.inventory, new_data], ignore_index=True)
                    st.success(f"✅ {name} 등록 완료!")
                    st.rerun()
                except:
                    st.error("❌ 날짜 형식이 틀렸습니다 (예: 251332 등)")
            else:
                st.warning("⚠️ 항목을 모두 채워주세요.")

st.divider()

# 2. 검색창
search = st.text_input("🔍 검색어 입력", placeholder="물품명을 입력하세요...")

# 3. 임박 알림
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

# 4. 리스트 현황
if not st.session_state.inventory.empty:
    df_m = st.session_state.inventory.copy()
    df_m['dt'] = pd.to_datetime(df_m['유통기한']).dt.date
    
    all_items = df_m['물품명'].unique()
    target_items = [i for i in all_items if search.lower() in i.lower()] if search else all_items

    for item in target_items:
        i_df = df_m[df_m['물품명'] == item].sort_values('dt')
        t_qty = int(i_df['개수'].sum())
        min_d = i_df['dt'].min()
        display_total = get_total_display(i_df)
        d_v = (min_d - today).days
        d_l = f"D-{d_v}" if d_v > 0 else ("오늘" if d_v == 0 else f"만료 D+{-d_v}")
        
        with st.expander(f"📦 {item} | 총 {t_qty}개 | {min_d}({d_l}) | 총량: {display_total}"):
            st.table(i_df[["개수", "유통기한", "총 무게", "단위"]])
            
            # 불출 기능 (form 밖으로 빼서 엔터 오작동 방지)
            c1, c2 = st.columns([2, 1])
            rem_qty = c1.number_input(f"불출 개수", min_value=1, max_value=t_qty, step=1, key=f"q_{item}")
            if c2.button(f"확인 후 불출", key=f"b_{item}", use_container_width=True):
                to_remove = rem_qty
                # 실제 삭제 로직
                temp_inv = st.session_state.inventory.copy()
                item_indices = i_df.index
                for idx in item_indices:
                    if to_remove <= 0: break
                    current_stock = temp_inv.at[idx, '개수']
                    unit_w = temp_inv.at[idx, '총 무게'] / current_stock
                    
                    if current_stock <= to_remove:
                        to_remove -= current_stock
                        temp_inv = temp_inv.drop(idx)
                    else:
                        temp_inv.at[idx, '개수'] -= to_remove
                        temp_inv.at[idx, '총 무게'] = int(temp_inv.at[idx, '개수'] * unit_w)
                        to_remove = 0
                st.session_state.inventory = temp_inv.reset_index(drop=True)
                st.rerun()
else:
    st.info("물자를 등록해 주세요.")
