import streamlit as st
from database import (get_members, add_member, update_member,
                      get_schedules, get_member_detail,
                      get_all_attendance_summary, get_all_fees_summary)

st.set_page_config(page_title="참석자 관리", page_icon="👥", layout="wide")
st.title("👥 참석자 관리")

# 참석자 추가
st.subheader("참석자 추가")
new_name = st.text_input("이름", key="new_member_name")
if st.button("추가") and new_name.strip():
    add_member(new_name.strip())
    st.success(f"{new_name} 추가 완료")
    st.rerun()

st.divider()

members = get_members()
if not members:
    st.info("등록된 참석자가 없습니다.")
    st.stop()

schedules = get_schedules()
total_schedules = len(schedules)

att_summary = get_all_attendance_summary()
fee_summary = get_all_fees_summary()

att_count = {}
for a in att_summary:
    if a["is_present"]:
        att_count[a["member_id"]] = att_count.get(a["member_id"], 0) + 1

fee_count = {}
for f in fee_summary:
    if f["is_paid"]:
        fee_count[f["member_id"]] = fee_count.get(f["member_id"], 0) + 1

st.subheader("참석자 목록")

for m in members:
    mid = m["id"]
    ac = att_count.get(mid, 0)
    fc = fee_count.get(mid, 0)
    rate = round(ac / total_schedules * 100) if total_schedules else 0
    has_unpaid = (total_schedules - fc) > 0

    col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 2])
    col1.write(f"**{m['name']}**")
    col2.write(f"출석 {ac}/{total_schedules}회")
    col3.write(f"출석률 {rate}%")
    col4.write(f"납부 {fc}회")
    col5.write(f"{'🔴 미납 있음' if has_unpaid else '✅ 완납'}")

    with st.expander(f"{m['name']} 상세 보기"):
        # 이름 수정
        with st.form(key=f"edit_{mid}"):
            edit_name = st.text_input("이름 수정", value=m["name"])
            if st.form_submit_button("수정"):
                update_member(mid, edit_name.strip())
                st.success("수정 완료")
                st.rerun()

        att_data, fee_data = get_member_detail(mid)

        att_by_date = {a["schedules"]["meeting_date"]: a["is_present"] for a in att_data}
        fee_by_date = {f["schedules"]["meeting_date"]: f for f in fee_data}

        all_dates = sorted({s["meeting_date"] for s in schedules}, reverse=True)

        if all_dates:
            st.markdown("**날짜별 출석 및 납부 현황**")
            header = st.columns([2, 2, 2, 2])
            header[0].markdown("날짜")
            header[1].markdown("출석")
            header[2].markdown("납부")
            header[3].markdown("납부금액")

            for d in all_dates:
                present = att_by_date.get(d, False)
                fee_rec = fee_by_date.get(d, {})
                paid = fee_rec.get("is_paid", False)
                amount = fee_rec.get("amount", 0) or 0
                row = st.columns([2, 2, 2, 2])
                row[0].write(d)
                row[1].write("✅ 출석" if present else "❌ 미출석")
                row[2].write("✅ 납부" if paid else "❌ 미납")
                row[3].write(f"{amount:,}원" if paid else "-")

    st.divider()
