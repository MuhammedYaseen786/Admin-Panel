import streamlit as st
from supabase import create_client
from datetime import datetime
import pytz
from postgrest.exceptions import APIError

st.set_page_config(
    page_title="Notice Board Admin",
    page_icon="tnc-logo-1.png",
    layout="wide"
)

# ------------------ ACCESS CONTROL ------------------
if "authorized" not in st.session_state:
    st.session_state.authorized = False

if not st.session_state.authorized:
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

st.title("📌 Notice Board Admin Panel")

# ------------------ TABS ------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📝 Add / Update Notice",
    "🗑️ Manage Days",
    "📢 Manage Announcements",
    "✏️ Edit Notice Board"
])

# ====================================================
# TAB 1 — ADD / UPDATE NOTICE
# ====================================================
with tab1:
    st.subheader("📌 Notice Board Entry", divider="rainbow")

    col1, col2 = st.columns(2)
    with col1:
        notice_date = st.date_input("📅 Date", value=default_date)

    # derive day dynamically from selected date
    dynamic_day = notice_date.strftime("%A")

    with col2:
        day_name = st.text_input("📆 Day", value=dynamic_day)


    day_order = st.selectbox("🔢 Day Order", ["I", "II", "III", "IV", "V", "VI", "--"])

    prev_count = 0
    try:
        prev = (
            supabase.table("notice_board_days")
            .select("day_count")
            .order("notice_date", desc=True)
            .limit(1)
            .execute()
        )
        if prev.data:
            prev_count = prev.data[0]["day_count"]
    except Exception:
        pass

    day_count = st.number_input(
        "📊 Day Count",
        min_value=1,
        value=prev_count + 1,
        step=1
    )

    st.divider()

    st.subheader("📢 Announcements")
    if "announcements" not in st.session_state:
        st.session_state.announcements = [{"title": "", "message": ""}]

    for i, ann in enumerate(st.session_state.announcements):
        with st.container(border=True):
            st.markdown(f"**Announcement {i + 1}**")
            ann["title"] = st.text_input("Title", ann["title"], key=f"title_{i}")
            ann["message"] = st.text_area("Message", ann["message"], key=f"msg_{i}")

    if st.button("➕ Add Another Announcement"):
        st.session_state.announcements.append({"title": "", "message": ""})

    st.divider()

    if st.button("💾 Save on Notice Board", use_container_width=True):
        try:
            day_row = (
                supabase.table("notice_board_days")
                .select("id")
                .eq("notice_date", str(notice_date))
                .execute()
            )

            if day_row.data:
                day_id = day_row.data[0]["id"]
                supabase.table("notice_board_days").update({
                    "day_name": day_name,
                    "day_order": day_order,
                    "day_count": day_count
                }).eq("id", day_id).execute()
            else:
                res = supabase.table("notice_board_days").insert({
                    "notice_date": str(notice_date),
                    "day_name": day_name,
                    "day_order": day_order,
                    "day_count": day_count
                }).execute()
                day_id = res.data[0]["id"]

            for ann in st.session_state.announcements:
                if ann["title"].strip() and ann["message"].strip():
                    supabase.table("announcements").insert({
                        "day_id": day_id,
                        "title": ann["title"],
                        "message": ann["message"]
                    }).execute()

            st.success("✅ Saved successfully")
            st.session_state.announcements = [{"title": "", "message": ""}]
        except APIError:
            st.error("❌ Error saving data")

# ====================================================
# TAB 2 — MANAGE DAYS (FILTER + CONFIRM DELETE)
# ====================================================
with tab2:
    st.subheader("🗑️ Manage Notice Board Days")

    filter_date = st.date_input("📅 Filter by Date", value=None)

    query = supabase.table("notice_board_days").select("*").order("notice_date", desc=True)
    if filter_date:
        query = query.eq("notice_date", str(filter_date))

    days = query.execute().data

    if not days:
        st.info("No records found.")
    else:
        for d in days:
            with st.container(border=True):
                col1, col2 = st.columns([5, 1])

                with col1:
                    st.markdown(
                        f"""
                        **📅 {d['notice_date']}**  
                        Day: {d['day_name']} | Order: {d['day_order']} | Count: {d['day_count']}
                        """
                    )

                with col2:
                    if st.button("❌ Delete", key=f"del_day_{d['id']}"):
                        st.session_state.confirm_day = d

    if "confirm_day" in st.session_state:
        d = st.session_state.confirm_day
        st.warning(f"⚠️ Are you sure you want to delete notice for **{d['notice_date']}**?")

        col1, col2 = st.columns(2)
        if col1.button("✅ Yes, Delete", key="confirm_day_yes"):
            supabase.table("announcements").delete().eq("day_id", d["id"]).execute()
            supabase.table("notice_board_days").delete().eq("id", d["id"]).execute()
            del st.session_state.confirm_day
            st.success("Deleted successfully")
            st.rerun()

        if col2.button("❌ Cancel", key="confirm_day_no"):
            del st.session_state.confirm_day
            st.info("Deletion cancelled")
            st.rerun()


# ====================================================
# TAB 3 — MANAGE ANNOUNCEMENTS
# ====================================================
with tab3:
    st.subheader("📢 Manage Announcements")

    filter_date = st.date_input("📅 Filter by Date", key="ann_date", value=None)

    ann_query = supabase.table("announcements").select(
        "id, title, message, notice_board_days(notice_date)"
    )

    anns = ann_query.execute().data

    if filter_date:
        anns = [
            a for a in anns
            if a["notice_board_days"]
            and a["notice_board_days"]["notice_date"] == str(filter_date)
        ]

    if not anns:
        st.info("No announcements found.")
    else:
        for a in anns:
            with st.container(border=True):
                col1, col2 = st.columns([5, 1])

                with col1:
                    st.markdown(
                        f"""
                        **📅 {a['notice_board_days']['notice_date']}**  
                        **{a['title']}**  
                        {a['message']}
                        """
                    )

                with col2:
                    if st.button("❌ Delete", key=f"del_ann_{a['id']}"):
                        st.session_state.confirm_ann = a

    if "confirm_ann" in st.session_state:
        a = st.session_state.confirm_ann
        st.warning(f"⚠️ Are you sure you want to delete announcement **{a['title']}**?")

        col1, col2 = st.columns(2)
        if col1.button("✅ Yes, Delete", key="confirm_ann_yes"):
            supabase.table("announcements").delete().eq("id", a["id"]).execute()
            del st.session_state.confirm_ann
            st.success("Deleted successfully")
            st.rerun()

        if col2.button("❌ Cancel", key="confirm_ann_no"):
            del st.session_state.confirm_ann
            st.info("Deletion cancelled")
            st.rerun()

# ====================================================
# TAB 4 — EDIT NOTICE BOARD (DAY + ANNOUNCEMENTS)
# ====================================================
with tab4:
    st.subheader("✏️ Edit Notice Board")

    edit_date = st.date_input(
        "📅 Select Date to Edit",
        key="edit_notice_date",
        value=None
    )

    if not edit_date:
        st.info("Select a date to edit.")
        st.stop()

    # ------------------ FETCH DAY ------------------
    day_res = (
        supabase.table("notice_board_days")
        .select("*")
        .eq("notice_date", str(edit_date))
        .execute()
    )

    if not day_res.data:
        st.warning("No notice found for this date.")
        st.stop()

    day = day_res.data[0]

    # ------------------ EDIT DAY DETAILS ------------------
    st.subheader("📅 Day Details")

    col1, col2, col3 = st.columns(3)

    with col1:
        edit_day_name = st.text_input(
            "Day Name",
            value=day["day_name"]
        )

    with col2:
        edit_day_order = st.selectbox(
            "Day Order",
            ["I", "II", "III", "IV", "V", "VI", "--"],
            index=["I", "II", "III", "IV", "V", "VI", "--"].index(day["day_order"])
        )

    with col3:
        edit_day_count = st.number_input(
            "Day Count",
            min_value=1,
            value=day["day_count"],
            step=1
        )

    st.divider()

    # ------------------ FETCH ANNOUNCEMENTS ------------------
    anns = (
        supabase.table("announcements")
        .select("*")
        .eq("day_id", day["id"])
        .execute()
        .data
    )

    st.subheader("📢 Announcements")

    if not anns:
        st.info("No announcements for this day.")

    if "edit_announcements" not in st.session_state:
        st.session_state.edit_announcements = anns.copy()

    for i, ann in enumerate(st.session_state.edit_announcements):
        with st.container(border=True):
            st.markdown(f"**Announcement {i + 1}**")

            ann["title"] = st.text_input(
                "Title",
                ann["title"],
                key=f"edit_title_{i}"
            )

            ann["message"] = st.text_area(
                "Message",
                ann["message"],
                key=f"edit_msg_{i}"
            )

    col1, col2 = st.columns(2)

    if col1.button("➕ Add New Announcement"):
        st.session_state.edit_announcements.append({
            "id": None,
            "day_id": day["id"],
            "title": "",
            "message": ""
        })

    st.divider()

    # ------------------ SAVE ALL ------------------
    if st.button("💾 Save All Changes", use_container_width=True):
        try:
            # Update day
            supabase.table("notice_board_days").update({
                "day_name": edit_day_name,
                "day_order": edit_day_order,
                "day_count": edit_day_count
            }).eq("id", day["id"]).execute()

            # Update / Insert announcements
            for ann in st.session_state.edit_announcements:
                if not ann["title"].strip() or not ann["message"].strip():
                    continue

                if ann.get("id"):
                    supabase.table("announcements").update({
                        "title": ann["title"],
                        "message": ann["message"]
                    }).eq("id", ann["id"]).execute()
                else:
                    supabase.table("announcements").insert({
                        "day_id": day["id"],
                        "title": ann["title"],
                        "message": ann["message"]
                    }).execute()

            del st.session_state.edit_announcements
            st.success("✅ Notice board updated successfully")
            st.rerun()

        except APIError:
            st.error("❌ Failed to update notice board")

