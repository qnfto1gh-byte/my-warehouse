import streamlit as st
import datetime

st.set_page_config(page_title="창고 재고 관리", layout="centered")

# -----------------------
# 세션 안전 초기화 (최중요)
# -----------------------
if "items" not in st.session_state or st.session_state.items is None:
    st.session_state.items = []

items = st.session_state.items
today = datetime.date.today()

st.title("창고 재고 관리 시스템")

# -----------------------
# 현황판 (항상 표시)
# -----------------------
st.subheader("창고 현황판")

big_items = [i for i in items if i.get("warehouse") == "큰창고"]
small_items = [i for i in items if i.get("warehouse") == "작은창고"]

def total_count(data):
    return sum(i.get("count", 0) for i in data)

danger_days = 7
danger_items = [
    i for i in items
    if (i.get("expire") - today).days <= danger_days
]

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("큰창고 품목 수", len(big_items))
    st.metric("큰창고 총 개수", total_count(big_items))
with c2:
    st.metric("작은창고 품목 수", len(small_items))
    st.metric("작은창고 총 개수", total_count(small_items))
with c3:
    st.metric("임박 품목", len(danger_items))

st.divider()

# -----------------------
# 재고 추가
# -----------------------
st.subheader("재고 등록")

name = st.text_input("품목명")
warehouse = st.selectbox("창고 선택", ["큰창고", "작은창고"])
count = st.number_input("개수", min_value=1, step=1)
expire = st.date_input("유통기한", min_value=today)

if st.button("추가"):
    items.append({
        "name": name,
        "warehouse": warehouse,
        "count": int(count),
        "expire": expire
    })
    st.success("등록 완료")
    st.experimental_rerun()

# -----------------------
# 재고 목록
# -----------------------
st.subheader("재고 현황")

if not items:
    st.info("재고 없음")
else:
    for idx in range(len(items)):
        item = items[idx]
        remain = (item["expire"] - today).days

        # 임박 강조 (빨간색)
        if remain <= danger_days:
            st.markdown(
                f"""
                <div style="border:2px solid red;
                            padding:10px;
                            border-radius:6px;
                            background-color:#ffe6e6;">
                <b>유통기한 임박</b><br>
                창고: {item['warehouse']}<br>
                품목: {item['name']}<br>
                개수: {item['count']}<br>
                유통기한: {item['expire']} ({remain}일)
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.write(
                f"[{item['warehouse']}] {item['name']} | "
                f"{item['count']}개 | {item['expire']} ({remain}일)"
            )

        # -----------------------
        # 출고 (개수 차감만)
        # -----------------------
        out_cnt = st.number_input(
            f"{item['name']} 출고 개수",
            min_value=0,
            max_value=item["count"],
            step=1,
            key=f"out_{idx}"
        )

        if st.button("출고", key=f"btn_{idx}"):
            item["count"] -= out_cnt
            if item["count"] <= 0:
                items.pop(idx)
            st.experimental_rerun()