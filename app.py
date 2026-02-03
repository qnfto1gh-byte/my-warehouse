import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="창고 재고 관리", layout="wide")

inventory_columns = [
    "warehouse",        # big / small
    "item_name",
    "unit",
    "weight_per_unit",
    "quantity",
    "expire_date",
    "created_at"
]log_columns = [
    "timestamp",
    "user",
    "action",          # 입고 / 출고 / 이동 / 정정
    "warehouse_from",
    "warehouse_to",
    "item_name",
    "quantity",
    "expire_date",
    "note"
]if "inventory" not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=inventory_columns)

if "logs" not in st.session_state:
    st.session_state.logs = pd.DataFrame(columns=log_columns)
# ------------------------
# 세션 초기화
# ------------------------
if "big" not in st.session_state:
    st.session_state.big = pd.DataFrame(
        columns=["물품명", "수량", "유통기한"]
    )

if "small" not in st.session_state:
    st.session_state.small = pd.DataFrame(
        columns=["물품명", "수량", "유통기한"]
    )

if "log" not in st.session_state:
    st.session_state.log = pd.DataFrame(
        columns=["시간", "사용자", "창고", "행동", "물품명", "수량", "유통기한", "비고"]
    )

# ------------------------
# 헤더
# ------------------------
st.title("📦 창고 재고 관리 시스템")

user = st.text_input("사용자 이름", value="미입력")

board_mode = st.toggle("📊 현황판 모드")

tab1, tab2, tab3 = st.tabs(["큰창고", "작은창고", "📜 기록"])

# ------------------------
# 공통 함수
# ------------------------
def log(action, warehouse, name, qty, exp, note=""):
    st.session_state.log.loc[len(st.session_state.log)] = [
        datetime.now(), user, warehouse, action, name, qty, exp, note
    ]

def show_table(df):
    today = datetime.now().date()

    def color(exp):
        d = (pd.to_datetime(exp).date() - today).days
        if d <= 3:
            return "background-color:#ffcccc"
        elif d <= 7:
            return "background-color:#fff0cc"
        return ""

    st.dataframe(
        df.style.applymap(color, subset=["유통기한"]),
        use_container_width=True
    )

# ------------------------
# 큰창고
# ------------------------
with tab1:
    st.subheader("🏭 큰창고")

items = st.session_state.inventory[
    st.session_state.inventory["warehouse"] == "big"
]

if items.empty:
    st.info("정정할 재고가 없습니다.")
else:
    target_idx = st.selectbox(
        "정정할 물품",
        items.index,
        format_func=lambda i: f"{items.loc[i,'item_name']} | {items.loc[i,'quantity']}개 | {items.loc[i,'expire_date']}"
    )
current_qty = items.loc[target_idx, "quantity"]
current_exp = items.loc[target_idx, "expire_date"]

new_qty = st.number_input(
    "정정 후 수량",
    min_value=0,
    value=int(current_qty),
    step=1
)

new_exp = st.date_input(
    "정정 후 유통기한", value=current_exp
)

note = st.text_input("정정 사유 (선택)")
if st.button("정정 실행"):
    before_qty = current_qty
    before_exp = current_exp

    st.session_state.inventory.loc[target_idx, "quantity"] = new_qty
    st.session_state.inventory.loc[target_idx, "expire_date"] = new_exp

    st.session_state.logs = pd.concat([
        st.session_state.logs,
        pd.DataFrame([{
            "timestamp": datetime.now(),
            "user": user,
            "action": "정정",
            "warehouse_from": "big",
            "warehouse_to": "big",
            "item_name": items.loc[target_idx, "item_name"],
            "quantity": f"{before_qty} → {new_qty}",
            "expire_date": f"{before_exp} → {new_exp}",
            "note": note
        }])
    ], ignore_index=True)

    st.success("정정 완료 (기록 남김)")
    if not board_mode:
        with st.form("big_in"):
            name = st.text_input("물품명")
            qty = st.number_input("수량", 1)
            exp = st.date_input("유통기한")
            if st.form_submit_button("입고"):
                st.session_state.big.loc[len(st.session_state.big)] = [name, qty, exp]
                log("입고", "큰창고", name, qty, exp)

        with st.form("big_out"):
            name = st.selectbox("불출 물품", st.session_state.big["물품명"].unique() if len(st.session_state.big) else [])
            qty = st.number_input("불출 수량", 1)
            if st.form_submit_button("불출 → 작은창고"):
                idx = st.session_state.big[st.session_state.big["물품명"] == name].index[0]
                exp = st.session_state.big.loc[idx, "유통기한"]

                st.session_state.big.loc[idx, "수량"] -= qty
                if st.session_state.big.loc[idx, "수량"] <= 0:
                    st.session_state.big = st.session_state.big.drop(idx)

                st.session_state.small.loc[len(st.session_state.small)] = [name, qty, exp]
                log("불출", "큰창고", name, qty, exp, "작은창고 이동")

    show_table(st.session_state.big)

# ------------------------
# 작은창고
# ------------------------
with tab2:
    st.subheader("📦 작은창고")

items = st.session_state.inventory[
    st.session_state.inventory["warehouse"] == "small"
]

if items.empty:
    st.info("정정할 재고가 없습니다.")
else:
    target_idx = st.selectbox(
        "정정할 물품",
        items.index,
        format_func=lambda i: f"{items.loc[i,'item_name']} | {items.loc[i,'quantity']}개 | {items.loc[i,'expire_date']}"
    )
current_qty = items.loc[target_idx, "quantity"]
current_exp = items.loc[target_idx, "expire_date"]

new_qty = st.number_input(
    "정정 후 수량",
    min_value=0,
    value=int(current_qty),
    step=1
)

new_exp = st.date_input(
    "정정 후 유통기한", value=current_exp
)

note = st.text_input("정정 사유 (선택)")
if st.button("정정 실행"):
    before_qty = current_qty
    before_exp = current_exp

    st.session_state.inventory.loc[target_idx, "quantity"] = new_qty
    st.session_state.inventory.loc[target_idx, "expire_date"] = new_exp

    st.session_state.logs = pd.concat([
        st.session_state.logs,
        pd.DataFrame([{
            "timestamp": datetime.now(),
            "user": user,
            "action": "정정",
            "warehouse_from": "big",
            "warehouse_to": "big",
            "item_name": items.loc[target_idx, "item_name"],
            "quantity": f"{before_qty} → {new_qty}",
            "expire_date": f"{before_exp} → {new_exp}",
            "note": note
        }])
    ], ignore_index=True)

    st.success("정정 완료 (기록 남김)")
    if not board_mode:
        with st.form("small_add"):
            name = st.text_input("물품명(소)")
            qty = st.number_input("수량(소)", 1)
            exp = st.date_input("유통기한(소)")
            if st.form_submit_button("신규 추가"):
                st.session_state.small.loc[len(st.session_state.small)] = [name, qty, exp]
                log("추가", "작은창고", name, qty, exp)

        with st.form("small_use"):
            name = st.selectbox("소비 물품", st.session_state.small["물품명"].unique() if len(st.session_state.small) else [])
            qty = st.number_input("소비 수량", 1)
            if st.form_submit_button("소비"):
                idx = st.session_state.small[st.session_state.small["물품명"] == name].index[0]
                exp = st.session_state.small.loc[idx, "유통기한"]

                st.session_state.small.loc[idx, "수량"] -= qty
                if st.session_state.small.loc[idx, "수량"] <= 0:
                    st.session_state.small = st.session_state.small.drop(idx)

                log("소비", "작은창고", name, qty, exp)

    show_table(st.session_state.small)

# ------------------------
# 기록
# ------------------------
with tab3:
    st.subheader("📜 입출 기록")

    start = st.date_input("시작일", datetime.now().date() - timedelta(days=7))
    end = st.date_input("종료일", datetime.now().date())

    df = st.session_state.log
    if len(df):
        mask = (df["시간"].dt.date >= start) & (df["시간"].dt.date <= end)
        st.dataframe(df[mask], use_container_width=True)