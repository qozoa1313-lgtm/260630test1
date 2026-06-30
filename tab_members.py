import streamlit as st
import pandas as pd
from datetime import date
import database as db
from utils import count_eligible_days


def render():
    # ── 인원 등록 ────────────────────────────────────────────────────────────
    if "show_add_member" not in st.session_state:
        st.session_state.show_add_member = False

    if st.button("인원 등록", type="primary", key="btn_open_add"):
        st.session_state.show_add_member = not st.session_state.show_add_member

    if st.session_state.show_add_member:
        with st.form("form_add_member", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("이름 *")
            birth = c2.date_input("생년월일", value=None, min_value=date(1900, 1, 1))
            c3, c4 = st.columns(2)
            start = c3.date_input("출석 시작일", value=date.today())
            end = c4.date_input("출석 종료일", value=date.today())
            wk = st.radio("주말 포함 여부", ["주말 포함", "주말 제외"], horizontal=True)
            submitted = st.form_submit_button("등록")
            if submitted:
                if not name.strip():
                    st.error("이름을 입력하세요")
                elif start > end:
                    st.error("시작일이 종료일보다 늦습니다")
                else:
                    db.add_member(name.strip(), birth, start, end, wk == "주말 포함")
                    st.session_state.show_add_member = False
                    st.success("등록 완료")
                    st.rerun()

    st.divider()

    members = db.get_members()
    all_att = db.get_all_attendance()
    all_fees = db.get_all_fees()

    # Precompute per-member stats
    att_cnt_by: dict[str, int] = {}
    for a in all_att:
        if a["is_present"]:
            att_cnt_by[a["member_id"]] = att_cnt_by.get(a["member_id"], 0) + 1

    unpaid_by: dict[str, list] = {}
    for f in all_fees:
        diff = (f.get("expected_amount") or 0) - (f.get("actual_amount") or 0)
        if diff > 0:
            mid = f["member_id"]
            unpaid_by.setdefault(mid, []).append(f)

    rows = []
    for m in members:
        cnt = att_cnt_by.get(m["id"], 0)
        eligible = count_eligible_days(m)
        rate = f"{round(cnt / eligible * 100)}%" if eligible else "0%"
        unpaid = unpaid_by.get(m["id"], [])
        rows.append({
            "_id": m["id"],
            "이름": m["name"],
            "생년월일": m.get("birth_date") or "-",
            "출석 시작일": m["start_date"],
            "출석 종료일": m["end_date"],
            "주말": "포함" if m["include_weekends"] else "제외",
            "출석 횟수": cnt,
            "출석률": rate,
            "회비 미납": f"{len(unpaid)}건" if unpaid else "완납",
            "_unpaid": unpaid,
        })

    # ── 검색 ─────────────────────────────────────────────────────────────────
    search = st.text_input("이름 검색", placeholder="이름을 입력하세요", key="member_search")
    display = [r for r in rows if search in r["이름"]] if search else rows

    if not display:
        st.info("참석자가 없습니다.")
        return

    # ── 표 (컬럼 클릭 정렬 내장) ──────────────────────────────────────────────
    display_keys = ["이름", "생년월일", "출석 시작일", "출석 종료일", "주말", "출석 횟수", "출석률", "회비 미납"]
    df = pd.DataFrame([{k: r[k] for k in display_keys} for r in display])
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()
    col_edit, col_detail = st.columns(2)

    # ── 정보 수정 ─────────────────────────────────────────────────────────────
    with col_edit:
        st.subheader("정보 수정")
        edit_sel = st.selectbox("수정할 참석자", [r["이름"] for r in display], key="edit_sel")
        target = next((r for r in rows if r["이름"] == edit_sel), None)
        if target:
            orig = next(m for m in members if m["id"] == target["_id"])
            with st.form("form_edit_member"):
                ec1, ec2 = st.columns(2)
                new_name = ec1.text_input("이름", value=orig["name"])
                new_birth = ec2.date_input(
                    "생년월일",
                    value=date.fromisoformat(orig["birth_date"]) if orig.get("birth_date") else None,
                    min_value=date(1900, 1, 1),
                )
                ec3, ec4 = st.columns(2)
                new_start = ec3.date_input("출석 시작일", value=date.fromisoformat(orig["start_date"]))
                new_end = ec4.date_input("출석 종료일", value=date.fromisoformat(orig["end_date"]))
                new_wk = st.radio(
                    "주말", ["주말 포함", "주말 제외"],
                    index=0 if orig["include_weekends"] else 1,
                    horizontal=True, key="edit_wk",
                )
                if st.form_submit_button("저장"):
                    db.update_member(orig["id"], new_name, new_birth, new_start, new_end, new_wk == "주말 포함")
                    st.success("수정 완료")
                    st.rerun()

    # ── 회비 미납 상세 ────────────────────────────────────────────────────────
    with col_detail:
        st.subheader("회비 미납 상세")
        detail_sel = st.selectbox("조회할 참석자", [r["이름"] for r in display], key="detail_sel")
        target_d = next((r for r in rows if r["이름"] == detail_sel), None)
        if target_d:
            if target_d["_unpaid"]:
                for f in target_d["_unpaid"]:
                    mtg = f.get("meetings") or {}
                    m_date = mtg.get("meeting_date", "")
                    m_name = mtg.get("meeting_name", "")
                    amt = (f.get("expected_amount") or 0) - (f.get("actual_amount") or 0)
                    st.write(f"- **{m_date}** {m_name}: **{amt:,}원** 미납")
            else:
                st.success("미납 없음")
