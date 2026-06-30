import streamlit as st
from supabase import create_client

@st.cache_resource
def get_client():
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

def get_members():
    res = get_client().table("members").select("*").order("created_at").execute()
    return res.data

def add_member(name: str):
    get_client().table("members").insert({"name": name}).execute()

def update_member(member_id: str, name: str):
    get_client().table("members").update({"name": name}).eq("id", member_id).execute()

def get_schedules():
    res = get_client().table("schedules").select("*").order("meeting_date", desc=True).execute()
    return res.data

def add_schedule(meeting_date: str):
    get_client().table("schedules").upsert({"meeting_date": meeting_date}).execute()

def get_attendance(schedule_id: str):
    res = (get_client().table("attendance")
           .select("*, members(name)")
           .eq("schedule_id", schedule_id)
           .execute())
    return res.data

def upsert_attendance(schedule_id: str, member_id: str, is_present: bool):
    get_client().table("attendance").upsert(
        {"schedule_id": schedule_id, "member_id": member_id,
         "is_present": is_present, "updated_at": "now()"},
        on_conflict="schedule_id,member_id"
    ).execute()

def get_fees(schedule_id: str):
    res = (get_client().table("fees")
           .select("*, members(name)")
           .eq("schedule_id", schedule_id)
           .execute())
    return res.data

def upsert_fee(schedule_id: str, member_id: str, is_paid: bool, amount: int, paid_date):
    get_client().table("fees").upsert(
        {"schedule_id": schedule_id, "member_id": member_id,
         "is_paid": is_paid, "amount": amount,
         "paid_date": str(paid_date) if paid_date else None,
         "updated_at": "now()"},
        on_conflict="schedule_id,member_id"
    ).execute()

def get_member_detail(member_id: str):
    att = (get_client().table("attendance")
           .select("is_present, schedules(meeting_date)")
           .eq("member_id", member_id)
           .execute())
    fee = (get_client().table("fees")
           .select("is_paid, amount, paid_date, schedules(meeting_date)")
           .eq("member_id", member_id)
           .execute())
    return att.data, fee.data

def get_all_attendance_summary():
    res = get_client().table("attendance").select("member_id, is_present").execute()
    return res.data

def get_all_fees_summary():
    res = get_client().table("fees").select("member_id, is_paid").execute()
    return res.data
