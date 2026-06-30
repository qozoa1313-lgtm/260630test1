import streamlit as st
from datetime import date
from database import get_members, get_schedules, get_fees, upsert_fee

st.set_page_config(page_title="회비 관리", page_icon="💰", layout="wide")
st.title("💰 회비 관리")

schedules = get_schedules()
if not schedules:
    st.info("등록된 모임 날짜가 없습니다. 출석 관리 페이지에서 날짜를 추가하세요.")
    st.stop()

members = get_members()
if not members:
    st.info("등록된 참석자가 없습니다. 참석자 관리 페이지에서 추가하세요.")
    st.stop()

date_options = {s["meeting_date"]: s["id"] for s in schedules}
selected_date = st.selectbox("모임 날짜", list(date_options.keys()))
schedule_id = date_options[selected_date]

fees = get_fees(schedule_id)
fee_map = {f["member_id"]: f for f in fees}

paid_count = sum(1 for m in members if fee_map.get(m["id"], {}).get("is_paid", False))
total_amount = sum(fee_map.get(m["id"], {}).get("amount", 0) or 0 for m in members)

col1, col2, col3 = st.columns(3)
col1.metric("납부자 수", f"{paid_count} / {len(members)}명")
col2.metric("미납자 수", f"{len(members) - paid_count}명")
col3.metric("총 납부 금액", f"{total_amount:,}원")

st.divider()
st.markdown("**회비 납부 정보 입력** (변경 후 저장 버튼을 누르세요)")

updated = {}
for m in members:
    rec = fee_map.get(m["id"], {})
    is_paid = rec.get("is_paid", False)
    amount = rec.get("amount", 0) or 0
    paid_date_val = rec.get("paid_date")

    with st.expander(f"{'✅' if is_paid else '❌'} {m['name']}", expanded=not is_paid):
        c1, c2, c3 = st.columns(3)
        new_paid = c1.checkbox("납부 완료", value=is_paid, key=f"paid_{m['id']}")
        new_amount = c2.number_input("납부 금액(원)", value=amount, min_value=0, step=1000, key=f"amt_{m['id']}")
        default_date = date.fromisoformat(paid_date_val) if paid_date_val else date.today()
        new_date = c3.date_input("납부일", value=default_date if new_paid else None,
                                  disabled=not new_paid, key=f"date_{m['id']}")
        updated[m["id"]] = (new_paid, new_amount, new_date if new_paid else None)

if st.button("회비 저장", type="primary"):
    for member_id, (is_paid, amount, paid_date) in updated.items():
        upsert_fee(schedule_id, member_id, is_paid, amount, paid_date)
    st.success("회비 정보 저장 완료")
    st.rerun()
