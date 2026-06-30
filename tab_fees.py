import streamlit as st
from datetime import date
import database as db
from utils import is_eligible, get_month_weeks, adj_month

_DAY_HDR = ["일", "월", "화", "수", "목", "금", "토"]
_DAY_COLOR = ["red", "#333", "#333", "#333", "#333", "#333", "blue"]


def _init():
    today = date.today()
    if "fee_year" not in st.session_state:
        st.session_state.fee_year = today.year
        st.session_state.fee_month = today.month
        st.session_state.fee_sel_date = None


def render():
    _init()
    year = st.session_state.fee_year
    month = st.session_state.fee_month
    members = db.get_members()

    # ── 모임 등록 ──────────────────────────────────────────────────────────────
    with st.expander("➕ 모임 등록"):
        with st.form("form_add_meeting", clear_on_submit=True):
            mc1, mc2 = st.columns(2)
            m_date = mc1.date_input("모임 날짜", value=date.today())
            m_name = mc2.text_input("모임명")
            if st.form_submit_button("등록"):
                if m_name.strip():
                    db.add_meeting(m_date, m_name.strip())
                    st.success("등록 완료")
                    st.rerun()
                else:
                    st.error("모임명을 입력하세요")

    # Load meetings for this month
    month_meetings = db.get_meetings_month(year, month)
    mtg_by_date: dict[str, list] = {}
    for m in month_meetings:
        mtg_by_date.setdefault(m["meeting_date"], []).append(m)

    # ── Navigation ─────────────────────────────────────────────────────────────
    n1, n2, n3 = st.columns([1, 4, 1])
    with n1:
        if st.button("◀ 이전", key="fee_prev"):
            st.session_state.fee_year, st.session_state.fee_month = adj_month(year, month, -1)
            st.session_state.fee_sel_date = None
            st.rerun()
    with n2:
        st.markdown(
            f"<h3 style='text-align:center;margin:4px 0'>{year}년 {month}월</h3>",
            unsafe_allow_html=True,
        )
    with n3:
        if st.button("다음 ▶", key="fee_next"):
            st.session_state.fee_year, st.session_state.fee_month = adj_month(year, month, 1)
            st.session_state.fee_sel_date = None
            st.rerun()

    # ── Header row ──────────────────────────────────────────────────────────────
    hcols = st.columns(7)
    for i, (lbl, clr) in enumerate(zip(_DAY_HDR, _DAY_COLOR)):
        hcols[i].markdown(
            f"<div style='text-align:center;font-weight:bold;color:{clr};padding:4px 0'>{lbl}</div>",
            unsafe_allow_html=True,
        )

    # ── Calendar body ───────────────────────────────────────────────────────────
    for week in get_month_weeks(year, month):
        wcols = st.columns(7)
        for i, day in enumerate(week):
            with wcols[i]:
                if day == 0:
                    st.write("")
                    continue
                d = date(year, month, day)
                d_str = d.isoformat()
                today_mtgs = mtg_by_date.get(d_str, [])
                if st.button(str(day), key=f"fee_btn_{d_str}", use_container_width=True):
                    st.session_state.fee_sel_date = d
                    st.rerun()
                for mtg in today_mtgs:
                    st.markdown(
                        f"<div style='text-align:center;font-size:10px;color:#1976D2;"
                        f"overflow:hidden;white-space:nowrap;text-overflow:ellipsis'>"
                        f"📌 {mtg['meeting_name']}</div>",
                        unsafe_allow_html=True,
                    )

    # ── Meeting detail ──────────────────────────────────────────────────────────
    sel_date = st.session_state.fee_sel_date
    if not sel_date:
        return

    d_str = sel_date.isoformat()
    meetings_today = mtg_by_date.get(d_str, [])

    st.divider()

    if not meetings_today:
        st.info(f"{sel_date}: 등록된 모임이 없습니다.")
        return

    # Select meeting if multiple on same day
    if len(meetings_today) > 1:
        opts = {m["meeting_name"]: m for m in meetings_today}
        sel_name = st.selectbox("모임 선택", list(opts.keys()), key="fee_mtg_sel")
        meeting = opts[sel_name]
    else:
        meeting = meetings_today[0]

    mid_mtg = meeting["id"]
    st.subheader(f"📋 {meeting['meeting_name']} ({meeting['meeting_date']})")

    eligible = [m for m in members if is_eligible(m, sel_date)]
    att_data = db.get_attendance_date(d_str)
    att_map = {a["member_id"]: a["is_present"] for a in att_data}
    wishes = db.get_wishes(mid_mtg)
    wish_map = {w["member_id"]: w["wishes_to_attend"] for w in wishes}
    fees = db.get_fees(mid_mtg)
    fee_map = {f["member_id"]: f for f in fees}

    # Compute groups
    wishers = [m for m in eligible if wish_map.get(m["id"], False)]
    wish_attended = [m for m in wishers if att_map.get(m["id"], False)]
    wish_absent = [m for m in wishers if not att_map.get(m["id"], False)]
    paid_list = [m for m in eligible if fee_map.get(m["id"], {}).get("is_paid", False)]
    unpaid_list = [m for m in eligible if not fee_map.get(m["id"], {}).get("is_paid", False)]

    total_exp = sum((fee_map.get(m["id"], {}).get("expected_amount") or 0) for m in eligible)
    total_act = sum((fee_map.get(m["id"], {}).get("actual_amount") or 0) for m in eligible)

    # Summary
    sm1, sm2, sm3, sm4 = st.columns(4)
    sm1.metric("출석 대상", f"{len(eligible)}명")
    sm2.metric("참여 희망", f"{len(wishers)}명")
    sm3.metric("납부 예정 합계", f"{total_exp:,}원")
    sm4.metric("실제 납부 합계", f"{total_act:,}원")

    # Status groups (2 rows of 4)
    g1, g2, g3, g4 = st.columns(4)
    with g1:
        st.markdown("**참여 희망자**")
        for m in wishers: st.write(f"- {m['name']}")
        if not wishers: st.write("없음")
    with g2:
        non_w = [m for m in eligible if not wish_map.get(m["id"], False)]
        st.markdown("**참여 희망 안 함**")
        for m in non_w: st.write(f"- {m['name']}")
        if not non_w: st.write("없음")
    with g3:
        st.markdown("**희망 후 참석**")
        for m in wish_attended: st.write(f"- {m['name']}")
        if not wish_attended: st.write("없음")
    with g4:
        st.markdown("**희망 후 미참석**")
        for m in wish_absent: st.write(f"- {m['name']}")
        if not wish_absent: st.write("없음")

    p1, p2 = st.columns(2)
    with p1:
        st.markdown("**납부자**")
        for m in paid_list: st.write(f"- {m['name']}")
        if not paid_list: st.write("없음")
    with p2:
        st.markdown("**미납자**")
        for m in unpaid_list: st.write(f"- {m['name']}")
        if not unpaid_list: st.write("없음")

    st.divider()
    st.markdown("**참여 희망 및 회비 입력 / 수정**")

    wish_updates: dict[str, bool] = {}
    fee_updates: dict[str, tuple] = {}

    for m in eligible:
        eid = m["id"]
        cur_wish = wish_map.get(eid, False)
        cur_fee = fee_map.get(eid, {})
        paid_icon = "✅" if cur_fee.get("is_paid") else "⬜"

        with st.expander(f"{paid_icon} {m['name']}"):
            new_wish = st.checkbox("참여 희망", value=cur_wish, key=f"w_{mid_mtg}_{eid}")
            fc1, fc2, fc3, fc4 = st.columns(4)
            new_exp = fc1.number_input(
                "납부 예정(원)", value=cur_fee.get("expected_amount") or 0,
                min_value=0, step=1000, key=f"exp_{mid_mtg}_{eid}",
            )
            new_act = fc2.number_input(
                "실제 납부(원)", value=cur_fee.get("actual_amount") or 0,
                min_value=0, step=1000, key=f"act_{mid_mtg}_{eid}",
            )
            new_paid = fc3.checkbox(
                "납부 완료", value=cur_fee.get("is_paid", False), key=f"paid_{mid_mtg}_{eid}",
            )
            pd_default = date.fromisoformat(cur_fee["paid_date"]) if cur_fee.get("paid_date") else None
            new_pd = fc4.date_input("납부일", value=pd_default, key=f"pd_{mid_mtg}_{eid}")

            wish_updates[eid] = new_wish
            fee_updates[eid] = (new_exp, new_act, new_paid, new_pd if new_paid else None)

    if st.button("저장", type="primary", key=f"fee_save_{mid_mtg}"):
        for eid, w in wish_updates.items():
            db.upsert_wish(mid_mtg, eid, w)
        for eid, (exp, act, paid, pd) in fee_updates.items():
            db.upsert_fee(mid_mtg, eid, exp, act, paid, pd)
        st.success("저장 완료")
        st.rerun()
