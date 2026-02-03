import streamlit as st
import datetime

st.set_page_config(page_title="창고 재고 관리", layout="centered")

st.title("📦 창고 재고 관리 시스템")

# -----------------------
# 데이터 저장소
# -----------------------
if "items" not in st.session_state:
    st.session_state.items = []

today = datetime.date.today()

# -----------------------
# 📊 현황판 (항상 표시)
# -----------------------
st.subheader("📊 창고 현황판")

big_items = [i for i in st.session_state.items if i["warehouse"] == "큰창고"]
small_items = [i for i in st.session_state.items if i["warehouse"] == "작은창고"]

def total_count(items):
    return sum(i["count"] for i in items)

danger_days = 7
danger_items = [
    i for i in st.session_state.items
    if (i["expire"] - today).days <= danger_days
]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("큰창고 품목 수", len(big_items))
    st.metric("큰창고 총 개수", total_count(big_items))

with col2:
    st.metric("작은창고 품목 수", len(small_items))
    st.metric("작은창고 총 개수", total_count(small_items))

with col3:
    st.metric("임박 위험 품목", len(danger_items))

st.divider()

# -----------------------
# 재고 등록
# -----------------------
st.subheader("➕ 재고 등록")

name = st.text_input("품목명")
warehouse = st.selectbox("창고 선택", ["큰창고", "작은창고"])
count = st.number_input("개수", min_value=1, step=1)
expire_date = st.date_input("유통기한", min_value=today)

if st.button("재고 추가"):
    st.session_state.items.append({
        "name": name,
        "warehouse": warehouse,
        "count": count,
        "expire": expire_date
    })
    st.success("재고가 추가되었습니다")

# -----------------------
# 임박 기준
# -----------------------
st.subheader("⏰ 유통기한 임박 기준")
danger_days = st.number_input("임박 기준 (일)", min_value=1, value=7)

# -----------------------
# 재고 목록
# -----------------------
st.subheader("📋 재고 현황")

if not st.session_state.items:
    st.info("등록된 재고가 없습니다")
else:
    for idx, item in enumerate(st.session_state.items):
        remain_days = (item["expire"] - today).days

        if remain_days <= danger_days:
            st.markdown(
                f"""
                <div style="border:2px solid red; padding:10px; border-radius:8px; background-color:#ffe6e6;">
                <b>⚠️ 임박 위험</b><br>
                창고: {item['warehouse']}<br>
                품목: {item['name']}<br>
                개수: {item['count']}<br>
                유통기한: {item['expire']} ({remain_days}일 남음)
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.write(
                f"[{item['warehouse']}] {item['name']} | 개수 {item['count']} | 유통기한 {item['expire']} ({remain_days}일)"
            )

        # -----------------------
        # 출고 (개수만 차감)
        # -----------------------
        out_count = st.number_input(
            f"{item['name']} 출고 개수",
            min_value=0,
            max_value=item["count"],
            step=1,
            key=f"out_{idx}"
        )

        if st.button(f"{item['name']} 출고", key=f"btn_{idx}"):
            item["count"] -= out_count
            if item["count"] == 0:
                st.session_state.items.pop(idx)
            st.experimental_rerun()