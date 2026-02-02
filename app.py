import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import streamlit.components.v1 as components
import time

# ===============================
# 앱 설정
# ===============================
st.set_page_config(page_title="부대 창고관리", layout="wide")
st.title("📦 부대 창고관리 시스템")

# ===============================
# JS 기능 (엔터 이동 / 0 자동삭제 / 전체 선택)
# ===============================
components.html("""
<script>
const doc = window.parent.document;

// 숫자칸 포커스 시 0 삭제 + 전체선택
doc.addEventListener('focusin', function(e) {
  if (e.target.tagName === 'INPUT' && e.target.type === 'number') {
    if (e.target.value === "0") e.target.value = "";
    setTimeout(() => e.target.select(), 50);
  }
});

// 입력 중에도 0 자동 삭제
doc.addEventListener('input', function(e) {
  if (e.target.tagName === 'INPUT' && e.target.type === 'number') {
    if (e.target.value === "0") e.target.value = "";
  }
});

// 엔터 → 다음 입력칸 이동
doc.addEventListener('keydown', function(e) {
  if (e.key === 'Enter') {
    const inputs = Array.from(doc.querySelectorAll('input'));
    const idx = inputs.indexOf(doc.activeElement);
    if (idx > -1 && idx < inputs.length - 1) {
      e.preventDefault();
      inputs[idx + 1].focus();
    }
  }
}, true);
</script>
""", height=0)

# ===============================
# Google Sheets 연결
# ===============================
RAW_URL = "https://docs.google.com/spreadsheets/d/1lKMH5BjjXWaqib_pqeqp_5UXpbc3M1PSDb4nEAoxw-A/edit"
from streamlit_gsheets import GSheetsConnection
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        inv = conn.read(spreadsheet=RAW_URL, worksheet="Inventory", ttl=0)
        hist = conn.read(spreadsheet=RAW_URL, worksheet="History", ttl=0)
        return inv.dropna(how="all"), hist.dropna(how="all")
    except:
        return (
            pd.DataFrame(columns=["물품명", "개수", "유통기한", "총 무게", "단위"]),
            pd.DataFrame(columns=["일시", "물품명", "유형", "수량"])
        )

inventory, history = load_data()
today = datetime.now().date()

# ===============================
# 총 무게 계산 함수
# ===============================
def get_total_display(df):
    total = 0
    unit_type = ""
    for _, r in df.iterrows():
        v, u = r["총 무게"], r["단위"]
        total += v * 1000 if u in ["kg", "L"] else v
        unit_type = "L" if u in ["L", "mL"] else "kg"
    if total >= 1000:
        return f"{total/1000:.2f}{unit_type}".replace(".00", "")
    return f"{int(total)}{'mL' if unit_type=='L' else 'g'}"

# ===============================
# 🚨 유통기한 7일 이내 알림
# ===============================
if not inventory.empty:
    inventory["유통기한"] = pd.to_datetime(inventory["유통기한"]).dt.date
    warn = inventory[inventory["유통기한"] <= today + timedelta(days=7)]
    if not warn.empty:
        st.error("🚨 유통기한 7일 이내 물품 있음")
        st.table(warn[["물품명", "개수", "유통기한"]].sort_values("유통기한"))

# ===============================
# 📜 작업 로그 (날짜별)
# ===============================
with st.expander("📜 작업 로그 (날짜별)"):
    if not history.empty:
        history["날짜"] = pd.to_datetime(history["일시"]).dt.date
        for d, df in history.sort_values("일시", ascending=False).groupby("날짜"):
            with st.expander(f"📅 {d}"):
                st.table(df[["일시", "물품명", "유형", "수량"]])

# ===============================
# ➕ 신규 입고
# ===============================
with st.expander("➕ 신규 물자 등록", expanded=True):
    with st.form("in_form", clear_on_submit=True):
        name = st.text_input("물품명")
        qty = st.number_input("입고 수량", min_value=0, value=0)
        d_raw = st.text_input("유통기한 (YYMMDD)", max_chars=6)
        wgt = st.number_input("단위당 무게", min_value=0, value=0)
        unit = st.selectbox("단위", ["g", "mL", "kg", "L"])

        if st.form_submit_button("🚀 등록"):
            d_clean = "".join(filter(str.isdigit, d_raw))
            try:
                exp = datetime.strptime(d_clean, "%y%m%d").date()
                total_w = int(wgt) * int(qty)

                new_inv = pd.DataFrame([[name, qty, exp, total_w, unit]],
                    columns=["물품명", "개수", "유통기한", "총 무게", "단위"])

                new_log = pd.DataFrame([[datetime.now(), name, "입고", qty]],
                    columns=["일시", "물품명", "유형", "수량"])

                conn.update(RAW_URL, "Inventory",
                    pd.concat([inventory, new_inv], ignore_index=True))
                conn.update(RAW_URL, "History",
                    pd.concat([history, new_log], ignore_index=True))

                st.success("✅ 입고 완료")
                time.sleep(0.5)
                st.rerun()
            except:
                st.error("❌ 날짜 형식 오류")

# ===============================
# 📦 재고 현황 + 검색
# ===============================
st.subheader("📦 재고 현황")
search = st.text_input("🔍 물품 검색")

if not inventory.empty:
    items = [i for i in inventory["물품명"].unique()
             if search.lower() in str(i).lower()]
    for item in items:
        df = inventory[inventory["물품명"] == item]
        with st.expander(f"{item} | {df['개수'].sum()}개 | {get_total_display(df)}"):
            st.table(df[["개수", "유통기한"]])

# ===============================
# 📤 출고 (자동 FEFO)
# ===============================
st.subheader("📤 출고")

with st.form("out_form"):
    out_name = st.selectbox("출고 물품", inventory["물품명"].unique())
    out_qty = st.number_input("출고 수량", min_value=1, value=1)

    if st.form_submit_button("📤 출고 처리"):
        df = inventory[inventory["물품명"] == out_name].copy()
        df = df.sort_values("유통기한")
        remain = out_qty
        drop_idx = []

        for idx, row in df.iterrows():
            if remain <= 0:
                break
            if row["개수"] <= remain:
                remain -= row["개수"]
                drop_idx.append(idx)
            else:
                inventory.loc[idx, "개수"] -= remain
                remain = 0

        if remain > 0:
            st.error("❌ 재고 부족")
            st.stop()

        inventory = inventory.drop(index=drop_idx)

        new_log = pd.DataFrame([[datetime.now(), out_name, "출고", out_qty]],
            columns=["일시", "물품명", "유형", "수량"])

        conn.update(RAW_URL, "Inventory", inventory)
        conn.update(RAW_URL, "History",
            pd.concat([history, new_log], ignore_index=True))

        st.success("✅ 출고 완료 (유통기한 빠른 순)")
        time.sleep(0.5)
        st.rerun()