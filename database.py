import calendar as _cal
import streamlit as st
from supabase import create_client


@st.cache_resource
def get_client():
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])


def _db():
    return get_client()


# ── Members ───────────────────────────────────────────────────────────────────

def get_members():
    return _db().table("members").select("*").order("created_at").execute().data


def add_member(name, birth_date, start_date, end_date, include_weekends):
    _db().table("members").insert({
        "name": name,
        "birth_date": str(birth_date) if birth_date else None,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "include_weekends": include_weekends,
    }).execute()


def update_member(mid, name, birth_date, start_date, end_date, include_weekends):
    _db().table("members").update({
        "name": name,
        "birth_date": str(birth_date) if birth_date else None,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "include_weekends": include_weekends,
    }).eq("id", mid).execute()


# ── Attendance ────────────────────────────────────────────────────────────────

def get_all_attendance():
    return _db().table("attendance").select("*").execute().data


def get_attendance_month(year, month):
    last = _cal.monthrange(year, month)[1]
    return (_db().table("attendance").select("*")
            .gte("date", f"{year}-{month:02d}-01")
            .lte("date", f"{year}-{month:02d}-{last}")
            .execute().data)


def get_attendance_date(date_str):
    return _db().table("attendance").select("*").eq("date", date_str).execute().data


def upsert_attendance(member_id, date_str, is_present):
    _db().table("attendance").upsert(
        {"member_id": member_id, "date": date_str, "is_present": is_present},
        on_conflict="member_id,date",
    ).execute()


# ── Meetings ──────────────────────────────────────────────────────────────────

def get_meetings_month(year, month):
    last = _cal.monthrange(year, month)[1]
    return (_db().table("meetings").select("*")
            .gte("meeting_date", f"{year}-{month:02d}-01")
            .lte("meeting_date", f"{year}-{month:02d}-{last}")
            .execute().data)


def add_meeting(meeting_date, meeting_name):
    _db().table("meetings").insert({
        "meeting_date": str(meeting_date),
        "meeting_name": meeting_name,
    }).execute()


# ── Participation wish ────────────────────────────────────────────────────────

def get_wishes(meeting_id):
    return _db().table("participation_wish").select("*").eq("meeting_id", meeting_id).execute().data


def upsert_wish(meeting_id, member_id, wishes):
    _db().table("participation_wish").upsert(
        {"meeting_id": meeting_id, "member_id": member_id, "wishes_to_attend": wishes},
        on_conflict="meeting_id,member_id",
    ).execute()


# ── Fees ──────────────────────────────────────────────────────────────────────

def get_fees(meeting_id):
    return _db().table("fees").select("*").eq("meeting_id", meeting_id).execute().data


def get_all_fees():
    return (_db().table("fees")
            .select("*, meetings(meeting_date, meeting_name)")
            .execute().data)


def upsert_fee(meeting_id, member_id, expected, actual, is_paid, paid_date):
    _db().table("fees").upsert(
        {"meeting_id": meeting_id, "member_id": member_id,
         "expected_amount": expected, "actual_amount": actual,
         "is_paid": is_paid,
         "paid_date": str(paid_date) if paid_date else None},
        on_conflict="meeting_id,member_id",
    ).execute()
