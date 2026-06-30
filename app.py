import streamlit as st
import tab_members
import tab_attendance
import tab_fees

st.set_page_config(page_title="모임 관리", page_icon="📋", layout="wide")

# Remove button focus ring (no black box on click)
st.markdown("""
<style>
button:focus, button:focus-visible {
    outline: none !important;
    box-shadow: none !important;
}
</style>
""", unsafe_allow_html=True)

t1, t2, t3 = st.tabs(["👥 인원 관리", "✅ 출석 체크", "💰 회비 관리"])

with t1:
    tab_members.render()
with t2:
    tab_attendance.render()
with t3:
    tab_fees.render()
