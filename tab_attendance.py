import streamlit as st
from datetime import date
import database as db
from utils import is_eligible, get_month_weeks, adj_month

_DAY_HDR = ["일", "월", "화", "수", "목", "금", "토"]
_DAY_COLOR = ["red", "#333", "#333", "#333", "#333", "#333", "blue"]


def _init():
    today = date.today()
    if "att_year" not in st.session_state:
        st.session_state.att_year = today.year
        st.session_state.att_month = today.month
        st.session_state.att_date = None


def render():
    _init()
    year = st.session_state.att_year
    month = st.session_state.att_month
    members = db.get_members()

    month_att = db.get_attendance_month(year, month)
    att_lookup: dict[str, dict[str, bool]] = {}
    for a in month_att:
        att_lookup.setdefault(a["date"], {})[a["member_id"]] = a["is_present"]

    # ── Navigation ────────────────────────────────────────────────────────────
    n1, n2, n3 = st.columns([1, 4, 1])
    with n1:
        if st.button("◀ 이전", key="att_prev"):
            st.session_state.att_year, st.session_state.att_month = adj_month(year, month, -1)
            st.session_state.att_date = None
            st.rerun()
    with n2:
        st.markdown(
            f"<h3 style='text-align:center;margin:4px 0'>{year}년 {month}월</h3>",
            unsafe_allow_html=True,
        )
    with n3:
        if st.button("다음 ▶", key="att_next"):
            st.session_state.att_year, st.session_state.att_month = adj_month(year, month, 1)
            st.session_state.att_date = None
            st.rerun()

    # ── Header row ───────────────────────────────────────────────────────────
    hcols = st.columns(7)
    for i, (lbl, clr) in enumerate(zip(_DAY_HDR, _DAY_COLOR)):
        hcols[i].markdown(
            f"<div style='text-align:center;font-weight:bold;color:{clr};padding:4px 0'>{lbl}</div>",
            unsafe_allow_html=True,
        )

    # ── Calendar body ─────────────────────────────────────────────────────────
    for week in get_month_weeks(year, month):
        wcols = st.columns(7)
        for i, day in enumerate(week):
            with wcols[i]:
                if day == 0:
                    st.write("")
                    continue
                d = date(year, month, day)
                d_str = d.isoformat()
                eligible = [m for m in members if is_eligible(m, d)]
                n_total = len(eligible)
                n_present = sum(
                    1 for m in eligible
                    if att_lookup.get(d_str, {}).get(m["id"], False)
                )
                if st.button(str(day), key=f"att_btn_{d_str}", use_container_width=True):
                    st.session_state.att_date = d
                    st.rerun()
                if n_total > 0:
                    rate = round(n_present / n_total * 100)
                    st.markdown(
                        f"<div style='text-align:center;font-size:10px;color:#555;margin-top:-8px'>"
                        f"{n_present}/{n_total} ({rate}%)</div>",
                        unsafe_allow_html=True,
                    )

    # ── Date detail ───────────────────────────────────────────────────────────
    sel = st.session_state.att_date
    if not sel:
        return

    st.divider()
    d_str = sel.isoformat()
    eligible = [m for m in members if is_eligible(m, sel)]
    att_data = db.get_attendance_date(d_str)
    att_map = {a["member_id"]: a["is_present"] for a in att_data}

    present = [m for m in eligible if att_map.get(m["id"], False)]
    absent = [m for m in eligible if not att_map.get(m["id"], False)]
    n_total = len(eligible)
    n_present = len(present)
    rate = round(n_present / n_total * 100) if n_total else 0

    st.subheader(f"📅 {sel} 출석 현황")
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("전체 대상", f"{n_total}명")
    mc2.metric("출석", f"{n_present}명")
    mc3.metric("미출석", f"{n_total - n_present}명")
    mc4.metric("출석률", f"{rate}%")

    lc, rc = st.columns(2)
    with lc:
        st.markdown("**✅ 출석자**")
        for m in present:
            st.write(f"- {m['name']}")
        if not present:
            st.write("없음")
    with rc:
        st.markdown("**❌ 미출석자**")
        for m in absent:
            st.write(f"- {m['name']}")
        if not absent:
            st.write("없음")

    if not eligible:
        return

    st.markdown("**출석 입력 / 수정**")
    updates: dict[str, bool] = {}
    cols_n = 4
    for chunk_start in range(0, len(eligible), cols_n):
        chunk = eligible[chunk_start: chunk_start + cols_n]
        ccols = st.columns(cols_n)
        for j, m in enumerate(chunk):
            updates[m["id"]] = ccols[j].checkbox(
                m["name"], value=att_map.get(m["id"], False),
                key=f"att_chk_{d_str}_{m['id']}",
            )

    if st.button("출석 저장", type="primary", key=f"att_save_{d_str}"):
        for mid, val in updates.items():
            db.upsert_attendance(mid, d_str, val)
        st.success("저장 완료")
        st.rerun()
