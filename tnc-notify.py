import streamlit as st
from supabase import create_client
from datetime import datetime
import pytz
from postgrest.exceptions import APIError

# ------------------ ACCESS CONTROL ------------------
if "authorized" not in st.session_state:
    st.session_state.authorized = False

if not st.session_state.authorized:
    st.set_page_config(page_title="Notice Board Access", layout="centered")
    access_code = st.text_input("Access Code", type="password")
    if st.button("Unlock"):
        if access_code == st.secrets["notice_board"]["access_code"]:
            st.session_state.authorized = True
            st.rerun()
        else:
            st.error("❌ Invalid access code")
    st.stop()

# ------------------ SUPABASE CLIENT ------------------
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------ TIMEZONE ------------------
ist = pytz.timezone("Asia/Kolkata")
now_ist = datetime.now(ist)
default_date = now_ist.date()
default_day = now_ist.strftime("%A")

st.set_page_config(page_title="Notice Board", layout="centered")
st.subheader("📌 Notice Board Entry", divider="rainbow")
st.divider()

# ------------------ DATE & DAY ------------------
col1, col2 = st.columns(2)
with col1:
    notice_date = st.date_input("📅 Date", value=default_date)
with col2:
    day_name = st.text_input("📆 Day", value=default_day)

# ------------------ DAY ORDER ------------------
day_order = st.selectbox("🔢 Day Order", ["I", "II", "III", "IV", "V", "VI"])

# ------------------ PREVIOUS DAY COUNT ------------------
prev_count = 0
try:
    prev_data = (
        supabase.table("notice_board_days")
        .select("day_count")
        .order("notice_date", desc=True)
        .limit(1)
        .execute()
    )
    if prev_data.data:
        prev_count = prev_data.data[0]["day_count"]
except Exception:
    prev_count = 0

day_count = st.number_input(
    "📊 Day Count",
    min_value=1,
    value=prev_count + 1,
    step=1
)

st.divider()

# ------------------ ANNOUNCEMENTS ------------------
st.subheader("📢 Announcements")
if "announcements" not in st.session_state:
    st.session_state.announcements = [{"title": "", "message": ""}]

for idx, ann in enumerate(st.session_state.announcements):
    with st.container(border=True):
        st.markdown(f"**Announcement {idx + 1}**")
        ann["title"] = st.text_input("Title", value=ann["title"], key=f"title_{idx}")
        ann["message"] = st.text_area("Message", value=ann["message"], key=f"msg_{idx}")

if st.button("➕ Add Another Announcement"):
    st.session_state.announcements.append({"title": "", "message": ""})

st.divider()

# ------------------ SAVE BUTTON ------------------
if st.button("💾 Save on Notice Board", use_container_width=True):
    try:
        # -------- Check if day exists --------
        day_row = (
            supabase.table("notice_board_days")
            .select("id")
            .eq("notice_date", str(notice_date))
            .single()
            .execute()
        )

        if day_row.data:
            # Exists → update
            day_id = day_row.data["id"]
            supabase.table("notice_board_days").update({
                "day_name": day_name,
                "day_order": day_order,
                "day_count": day_count
            }).eq("id", day_id).execute()
        else:
            # Does not exist → insert
            insert_res = supabase.table("notice_board_days").insert({
                "notice_date": str(notice_date),
                "day_name": day_name,
                "day_order": day_order,
                "day_count": day_count
            }).execute()
            day_id = insert_res.data[0]["id"]

        # -------- Insert announcements --------
        for ann in st.session_state.announcements:
            if ann["title"].strip() and ann["message"].strip():
                supabase.table("announcements").insert({
                    "day_id": day_id,
                    "title": ann["title"],
                    "message": ann["message"]
                }).execute()

        st.success("✅ Notice Board saved successfully")
        st.session_state.announcements = [{"title": "", "message": ""}]

    except APIError as e:
        st.error("❌ Could not save notice board. Duplicate date or network issue.")
