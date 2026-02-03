import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# ------------------------
# 앱 설정
# ------------------------
st.set_page_config(page_title="창고 재고 관리", layout="wide")

# ------------------------
# 세션 초기화 (빈 데이터프레임 포함)
# ------------------------
if "inventory" not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=[
        "warehouse","item_name","unit","weight_per_unit","quantity","expire_date","created_at"
    ])

if "logs" not in st.session_state:
    st.session_state.logs = pd.DataFrame(columns=[
        "timestamp","user","action","warehouse_from","warehouse_to","item_name","quantity","expire_date","note"
    ])

if "hidden_items" not in st.session_state:
    st.session_state.hidden_items = set()

# ------------------------
# 헤더
# ------------------------
st.title("📦 창고 재고 관리 시스템")
user = st.text_input("사용자 이름", value="미입력")
board_mode = st.toggle("📊 현황판 모드")

tab1, tab2, tab3 = st.tabs(["큰창고","작은창고","📜 기록"])

# ------------------------
# 공통 함수
# ------------------------
def log(action, w_from, w_to, name, qty, exp, note=""):
    st.session_state.logs.loc[len(st.session_state.logs)] = [
        datetime.now(), user, action, w_from, w_to, name, qty, exp, note
    ]

def compute_total_weight(df):
    total = 0
    unit_type = ""
    for _, r in df.iterrows():
        val, u = r['weight_per_unit'], r['unit']
        total += val * r['quantity']
        if u in ['L','mL']: unit_type='L'
        else: unit_type='kg'
    if unit_type=='L' and total>=1000: return f"{total/1000:.2f}L"
    if unit_type=='kg' and total>=1000: return f"{total/1000:.2f}kg"
    return f"{total}{'mL' if unit_type=='L' else 'g'}"

def color_expiry(exp):
    today = datetime.now().date()
    d = (pd.to_datetime(exp).date() - today).days
    if d<=3: return "background-color:#ffcccc"
    elif d<=7: return "background-color:#fff0cc"
    return ""

def show_inventory(df, warehouse):
    if df.empty:
        st.info("재고가 없습니다.")
        return
    for item in df["item_name"].unique():
        if item in st.session_state.hidden_items and board_mode:
            continue  # 숨긴 항목은 현황판 모드에서 안보임
        i_df = df[df["item_name"]==item]
        total_w = compute_total_weight(i_df)
        earliest_exp = i_df["expire_date"].min()
        with st.expander(f"{item} | 총 {i_df['quantity'].sum()}개 | {total_w} | 제일 빠른 유통기한: {earliest_exp}"):
            st.dataframe(i_df[["quantity","unit","weight_per_unit","expire_date"]].style.applymap(color_expiry, subset=["expire_date"]), use_container_width=True)
            if board_mode:
                hide = st.checkbox("현황판에서 숨기기", key=f"hide_{warehouse}_{item}")
                if hide: st.session_state.hidden_items.add(item)
                elif item in st.session_state.hidden_items:
                    st.session_state.hidden_items.remove(item)

# ------------------------
# 큰창고
# ------------------------
with tab1:
    st.subheader("🏭 큰창고")
    warehouse = "big"
    items = st.session_state.inventory[st.session_state.inventory["warehouse"]==warehouse]
    search = st.text_input("🔍 물품 검색 (큰창고)", key="search_big")
    if search: items = items[items["item_name"].str.contains(search, case=False)]

    # 정정
    st.divider(); st.subheader("✏️ 재고 정정 (큰창고)")
    if not items.empty:
        target_idx = st.selectbox("정정할 물품", items.index, format_func=lambda i: f"{items.loc[i,'item_name']} | {items.loc[i,'quantity']}개 | {items.loc[i,'expire_date']}")
        new_qty = st.number_input("정정 후 수량", min_value=0, value=int(items.loc[target_idx,"quantity"]))
        new_exp = st.date_input("정정 후 유통기한", value=pd.to_datetime(items.loc[target_idx,"expire_date"]))
        note = st.text_input("정정 사유 (선택)", key="note_big")
        if st.button("정정 실행 (큰창고)"):
            before = items.loc[target_idx]
            st.session_state.inventory.loc[target_idx,"quantity"]=new_qty
            st.session_state.inventory.loc[target_idx,"expire_date"]=new_exp
            log("정정", warehouse, warehouse, before["item_name"], f"{before['quantity']}→{new_qty}", f"{before['expire_date']}→{new_exp}", note)
            st.success("정정 완료")

    if not board_mode:
        st.divider(); st.subheader("📥 입고 / 📤 불출")
        with st.form("big_in"):
            name = st.text_input("물품명", key="big_in_name")
            qty = st.number_input("수량", 1, 1, key="big_in_qty")
            unit = st.selectbox("단위", ["g","kg","mL","L"], key="big_in_unit")
            wpu = st.number_input("단위당 무게", 0,1,key="big_in_w")
            exp = st.date_input("유통기한", key="big_in_exp")
            if st.form_submit_button("입고"):
                st.session_state.inventory.loc[len(st.session_state.inventory)] = [warehouse,name,unit,wpu,qty,exp,datetime.now()]
                log("입고", warehouse, warehouse, name, qty, exp)
                st.success(f"{name} 입고 완료")

        if not items.empty:
            with st.form("big_out"):
                out_name = st.selectbox("불출 물품", items["item_name"].unique(), key="big_out_name")
                out_qty = st.number_input("불출 수량",1,1,key="big_out_qty")
                if st.form_submit_button("불출 → 작은창고"):
                    idx = st.session_state.inventory[(st.session_state.inventory["warehouse"]==warehouse)&(st.session_state.inventory["item_name"]==out_name)].index[0]
                    out_exp = st.session_state.inventory.loc[idx,"expire_date"]
                    st.session_state.inventory.loc[idx,"quantity"] -= out_qty
                    if st.session_state.inventory.loc[idx,"quantity"]<=0: st.session_state.inventory = st.session_state.inventory.drop(idx)
                    st.session_state.inventory.loc[len(st.session_state.inventory)] = ["small", out_name, st.session_state.inventory.loc[idx,"unit"], st.session_state.inventory.loc[idx,"weight_per_unit"], out_qty, out_exp, datetime.now()]
                    log("불출", warehouse, "small", out_name, out_qty, out_exp, "작은창고 이동")
                    st.success(f"{out_name} 불출 완료")

    show_inventory(items)

# ------------------------
# 작은창고
# ------------------------
with tab2:
    st.subheader("📦 작은창고")
    warehouse="small"
    items = st.session_state.inventory[st.session_state.inventory["warehouse"]==warehouse]
    search = st.text_input("🔍 물품 검색 (작은창고)", key="search_small")
    if search: items = items[items["item_name"].str.contains(search, case=False)]

    # 정정
    st.divider(); st.subheader("✏️ 재고 정정 (작은창고)")
    if not items.empty:
        target_idx = st.selectbox("정정할 물품", items.index, format_func=lambda i: f"{items.loc[i,'item_name']} | {items.loc[i,'quantity']}개 | {items.loc[i,'expire_date']}", key="small_select")
        new_qty = st.number_input("정정 후 수량", min_value=0, value=int(items.loc[target_idx,"quantity"]), key="small_qty")
        new_exp = st.date_input("정정 후 유통기한", value=pd.to_datetime(items.loc[target_idx,"expire_date"]), key="small_exp")
        note = st.text_input("정정 사유 (선택)", key="small_note")
        if st.button("정정 실행 (작은창고)", key="small_btn"):
            before = items.loc[target_idx]
            st.session_state.inventory.loc[target_idx,"quantity"]=new_qty
            st.session_state.inventory.loc[target_idx,"expire_date"]=new_exp
            log("정정", warehouse, warehouse, before["item_name"], f"{before['quantity']}→{new_qty}", f"{before['expire_date']}→{new_exp}", note)
            st.success("정정 완료")

    if not board_mode:
        st.divider(); st.subheader("📥 신규 추가 / 📤 소비")
        with st.form("small_add"):
            name = st.text_input("물품명(소)", key="small_add_name")
            qty = st.number_input("수량(소)",1,1,key="small_add_qty")
            unit = st.selectbox("단위(소)", ["g","kg","mL","L"], key="small_add_unit")
            wpu = st.number_input("단위당 무게(소)",0,1,key="small_add_w")
            exp = st.date_input("유통기한(소)", key="small_add_exp")
            if st.form_submit_button("신규 추가(작은창고)"):
                st.session_state.inventory.loc[len(st.session_state.inventory)] = [warehouse,name,unit,wpu,qty,exp,datetime.now()]
                log("추가", warehouse, warehouse, name, qty, exp)
                st.success(f"{name} 추가 완료")

        if not items.empty:
            with st.form("small_use"):
                use_name = st.selectbox("소비 물품", items["item_name"].unique(), key="small_use_name")
                use_qty = st.number_input("소비 수량",1,1,key="small_use_qty")
                if st.form_submit_button("소비(작은창고)"):
                    idx = st.session_state.inventory[(st.session_state.inventory["warehouse"]==warehouse)&(st.session_state.inventory["item_name"]==use_name)].index[0]
                    exp = st.session_state.inventory.loc[idx,"expire_date"]
                    st.session_state.inventory.loc[idx,"quantity"] -= use_qty
                    if st.session_state.inventory.loc[idx,"quantity"]<=0: st.session_state.inventory = st.session_state.inventory.drop(idx)
                    log("소비", warehouse, warehouse, use_name, use_qty, exp)
                    st.success(f"{use_name} 소비 완료")

    show_inventory(items)

# ------------------------
# 기록 탭
# ------------------------
with tab3:
    st.subheader("📜 입출 기록")
    start = st.date_input("시작일", datetime.now().date()-timedelta(days=7))
    end = st.date_input("종료일", datetime.now().date())
    df = st.session_state.logs
    if len(df):
        mask = (df["timestamp"].dt.date>=start) & (df["timestamp"].dt.date<=end)
        st.dataframe(df[mask], use_container_width=True)

    if board_mode:
        if st.button("🔄 현황판 숨김 초기화"):
            st.session_state.hidden_items = set()