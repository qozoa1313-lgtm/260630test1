import streamlit as st
from datetime import date
from database import get_members, get_schedules, add_schedule, get_attendance, upsert_attendance

st.set_page_config(page_title="출석 관리", page_icon="✅", layout="wide")
st.title("✅ 출석 관리")

# 날짜 추가
st.subheader("모임 날짜 추가")
new_date = st.date_input("날짜 선택", value=date.today(), key="new_date")
if st.button("날짜 추가"):
    add_schedule(str(new_date))
    st.success(f"{new_date} 추가 완료")
    st.rerun()

st.divider()

schedules = get_schedules()
if not schedules:
    st.info("등록된 모임 날짜가 없습니다.")
    st.stop()

members = get_members()
if not members:
    st.info("등록된 참석자가 없습니다. 참석자 관리 페이지에서 추가하세요.")
    st.stop()

# 날짜 선택
st.subheader("날짜별 출석 입력")
date_options = {s["meeting_date"]: s["id"] for s in schedules}
selected_date = st.selectbox("모임 날짜", list(date_options.keys()))
schedule_id = date_options[selected_date]

attendance = get_attendance(schedule_id)
att_map = {a["member_id"]: a["is_present"] for a in attendance}

present_count = sum(1 for m in members if att_map.get(m["id"], False))
att_rate = round(present_count / len(members) * 100) if members else 0

col1, col2, col3 = st.columns(3)
col1.metric("전체 인원", f"{len(members)}명")
col2.metric("출석자 수", f"{present_count}명")
col3.metric("출석률", f"{att_rate}%")

st.divider()
st.markdown("**출석 여부 입력** (변경 후 저장 버튼을 누르세요)")

updated = {}
for m in members:
    current = att_map.get(m["id"], False)
    label = f"{'✅' if current else '❌'} {m['name']}"
    updated[m["id"]] = st.checkbox(label, value=current, key=f"att_{m['id']}")

if st.button("출석 저장", type="primary"):
    for member_id, is_present in updated.items():
        upsert_attendance(schedule_id, member_id, is_present)
    st.success("출석 정보 저장 완료")
    st.rerun()
