import streamlit as st
from database import get_members, get_schedules, get_attendance, get_fees

st.set_page_config(page_title="모임 관리", page_icon="📋", layout="wide")
st.title("📋 모임 관리 대시보드")

members = get_members()
schedules = get_schedules()
total_members = len(members)

st.subheader("날짜 선택")
if not schedules:
    st.info("등록된 모임 날짜가 없습니다. 출석 관리 페이지에서 날짜를 추가하세요.")
    st.stop()

date_options = {s["meeting_date"]: s["id"] for s in schedules}
selected_date = st.selectbox("모임 날짜", list(date_options.keys()))
schedule_id = date_options[selected_date]

attendance = get_attendance(schedule_id)
fees = get_fees(schedule_id)

att_map = {a["member_id"]: a["is_present"] for a in attendance}
fee_map = {f["member_id"]: f["is_paid"] for f in fees}

present_count = sum(1 for m in members if att_map.get(m["id"], False))
paid_count = sum(1 for m in members if fee_map.get(m["id"], False))
absent_count = total_members - present_count
unpaid_count = total_members - paid_count
att_rate = round(present_count / total_members * 100) if total_members else 0

st.divider()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("전체 참석자 수", f"{total_members}명")
with col2:
    st.metric("출석자 수", f"{present_count} / {total_members}명")
with col3:
    st.metric("출석률", f"{att_rate}%")

col4, col5, col6 = st.columns(3)
with col4:
    st.metric("회비 납부자 수", f"{paid_count} / {total_members}명")
with col5:
    st.metric("미출석자 수", f"{absent_count}명")
with col6:
    st.metric("미납자 수", f"{unpaid_count}명")

st.divider()
st.subheader("미출석 / 미납 현황")

col_a, col_b = st.columns(2)
with col_a:
    st.markdown("**미출석자**")
    absent = [m["name"] for m in members if not att_map.get(m["id"], False)]
    if absent:
        for name in absent:
            st.write(f"- {name}")
    else:
        st.write("없음")

with col_b:
    st.markdown("**미납자**")
    unpaid = [m["name"] for m in members if not fee_map.get(m["id"], False)]
    if unpaid:
        for name in unpaid:
            st.write(f"- {name}")
    else:
        st.write("없음")

st.divider()
col_n1, col_n2, col_n3 = st.columns(3)
with col_n1:
    st.page_link("pages/1_출석관리.py", label="출석 관리 →", icon="✅")
with col_n2:
    st.page_link("pages/2_회비관리.py", label="회비 관리 →", icon="💰")
with col_n3:
    st.page_link("pages/3_참석자관리.py", label="참석자 관리 →", icon="👥")
