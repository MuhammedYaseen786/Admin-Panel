import streamlit as st
import io
import pytz

from datetime import datetime
from supabase import create_client
from postgrest.exceptions import APIError

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

from reportlab.platypus import Flowable
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm

from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Flowable,
    KeepInFrame,
    PageBreak,
    Table,
    TableStyle
)


from reportlab.lib.enums import TA_CENTER
from xml.sax.saxutils import escape

# ====================================================
# HEADER COLOUR PALETTE
# ====================================================

HEADER_COLORS = [
    colors.HexColor("#1764BB"),  # Blue
    colors.HexColor("#218838"),  # Green
    colors.HexColor("#E67E22"),  # Orange
    colors.HexColor("#F1C40F"),  # Yellow
    colors.HexColor("#7651A9")   # Violet
]


def get_header_color(index):
    return HEADER_COLORS[index % len(HEADER_COLORS)]


def get_header_text_color(index):
    if index % len(HEADER_COLORS) == 3:
        return colors.HexColor("#243447")

    return colors.white

# ====================================================
# NOTICE BOARD HEADER
# ====================================================

# ====================================================
# NOTICE BOARD HEADER
# ====================================================

class NoticeHeader(Flowable):

    def __init__(
        self,
        date,
        day,
        order,
        count,
        college="THE NEW COLLEGE",
        academic_year="2025–2026",
        header_color=None,
        text_color=None
    ):

        super().__init__()

        self.date = date
        self.day = day
        self.order = order
        self.count = count
        self.college = college
        self.academic_year = academic_year

        self.header_color = (
            header_color or HEADER_COLORS[0]
        )

        self.text_color = (
            text_color or colors.white
        )

        self.height = 40 * mm

    def wrap(self, availWidth, availHeight):

        self.width = availWidth

        return self.width, self.height

    def draw(self):

        c = self.canv
        w = self.width
        h = self.height

        # Header background

        c.setFillColor(self.header_color)

        c.roundRect(
            0, 0,
            w, h,
            4 * mm,
            fill=1,
            stroke=0
        )

        # --------------------------------
        # DATE - LEFT SIDE
        # --------------------------------

        c.setFillColor(self.text_color)
        c.setFont("Helvetica-Bold", 17)

        c.drawString(
            5 * mm,
            h - 14 * mm,
            self.date
        )

        # --------------------------------
        # COLLEGE DETAILS - RIGHT SIDE
        # --------------------------------

        c.setFillColor(self.text_color)
        c.setFont("Helvetica-Bold", 11)

        c.drawRightString(
            w - 5 * mm,
            h - 7 * mm,
            self.college
        )

        c.setFont("Helvetica-Bold", 8)

        c.drawRightString(
            w - 5 * mm,
            h - 13 * mm,
            "Day Order & Announcements · AY"
        )

        c.drawRightString(
            w - 5 * mm,
            h - 19 * mm,
            self.academic_year
        )

        # --------------------------------
        # DAY DETAILS - BOTTOM
        # --------------------------------

        if self.text_color == colors.white:

            day_color = colors.HexColor("#A9DFFF")

        else:

            day_color = colors.HexColor("#243447")

        c.setFillColor(day_color)
        c.setFont("Helvetica-Bold", 12)

        c.drawString(
            5 * mm,
            7 * mm,
            self.day
        )

        day_width = c.stringWidth(
            self.day,
            "Helvetica-Bold",
            12
        )

        c.setFillColor(self.text_color)
        c.setFont("Helvetica", 12)

        c.drawString(
            5 * mm + day_width + 5,
            7 * mm,
            f" |  Day Order: {self.order}  |  Day Count: {self.count}"
        )

# ====================================================
# ANNOUNCEMENT CARD
# ====================================================

class AnnouncementCard(Flowable):

    def __init__(
        self,
        number,
        title,
        message,
        bg,
        title_color
    ):

        super().__init__()

        self.number = number
        self.title = title
        self.message = message
        self.bg = bg
        self.title_color = title_color

        self.padding = 6 * mm
        self.badge_width = 10 * mm

        self.title_style = ParagraphStyle(
            "AnnouncementTitle",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=15,
            textColor=title_color
        )

        self.message_style = ParagraphStyle(
            "AnnouncementMessage",
            fontName="Helvetica",
            fontSize=9,
            leading=15,
            textColor=colors.HexColor("#354451")
        )

    def wrap(self, availWidth, availHeight):

        self.width = availWidth

        content_width = (
            availWidth
            - self.padding * 2
            - self.badge_width
        )

        self.title_para = Paragraph(
            escape(str(self.title)),
            self.title_style
        )

        self.message_para = Paragraph(
            escape(str(self.message)).replace(
                "\n", "<br/>"
            ),
            self.message_style
        )

        _, self.title_height = self.title_para.wrap(
            content_width,
            availHeight
        )

        _, self.message_height = self.message_para.wrap(
            content_width,
            availHeight
        )

        self.height = (
            self.padding
            + self.title_height
            + 5 * mm
            + self.message_height
            + 10 * mm
        )

        return availWidth, self.height

    def draw(self):

        c = self.canv

        w = self.width
        h = self.height

        # Background

        c.setFillColor(self.bg)

        c.roundRect(
            0, 0,
            w, h,
            3 * mm,
            fill=1,
            stroke=0
        )

        # Number badge

        c.setFillColor(HEADER_COLORS[0])

        c.rect(
            0,
            h - 11 * mm,
            self.badge_width,
            11 * mm,
            fill=1,
            stroke=0
        )

        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)

        c.drawCentredString(
            self.badge_width / 2,
            h - 7.5 * mm,
            str(self.number)
        )

        # Title

        content_x = (
            self.padding + self.badge_width
        )

        title_y = (
            h - self.padding - self.title_height
        )

        self.title_para.drawOn(
            c,
            content_x,
            title_y
        )

        # Message

        message_y = (
            title_y
            - 5 * mm
            - self.message_height
        )

        self.message_para.drawOn(
            c,
            content_x,
            message_y
        )

        # Bottom blue strip

        c.setFillColor(HEADER_COLORS[0])

        c.rect(
            0, 0,
            w, 5 * mm,
            fill=1,
            stroke=0
        )


# ====================================================
# AUTOMATIC DAY COUNT PERIOD DETECTION
# ====================================================

def detect_notice_periods(days_data):

    periods = []
    current_period = []

    def save_period(records, status):

        if not records:
            return

        first = records[0]
        last = records[-1]

        periods.append({
            "records": records,
            "start_date": first["notice_date"],
            "end_date": last["notice_date"],
            "start_count": first["day_count"],
            "last_count": last["day_count"],
            "status": status
        })

    # Sort chronologically
    days_data = sorted(
        days_data,
        key=lambda x: x["notice_date"]
    )

    for day in days_data:

        count = int(day["day_count"])

        # A new cycle begins
        if count == 1:

            # Close previous unfinished period
            if current_period:

                previous_count = int(
                    current_period[-1]["day_count"]
                )

                if previous_count == 90:
                    status = "Completed"
                else:
                    status = "Closed - New Cycle Started"

                save_period(current_period, status)

                current_period = []

            current_period.append(day)

        else:

            # Include records even if the database
            # begins with a count other than 1
            if not current_period:
                current_period.append(day)
            else:
                current_period.append(day)

        # A cycle is complete at day 90
        if current_period and count == 90:

            save_period(
                current_period,
                "Completed"
            )

            current_period = []

    # Save the currently running period
    if current_period:

        save_period(
            current_period,
            "In Progress"
        )

    return periods


# ====================================================
# NOTICE BOARD HEADER
# ====================================================


# ====================================================
# NOTICE BOARD HEADER
# ====================================================

class NoticeHeader(Flowable):

    def __init__(
        self,
        date,
        day,
        order,
        count,
        college="THE NEW COLLEGE",
        academic_year=None,
        header_color=None,
        text_color=None
    ):

        super().__init__()

        self.date = str(date or "")
        self.day = str(day or "")
        self.order = str(order or "")
        self.count = str(count or "")

        self.college = college or "THE NEW COLLEGE"
        self.academic_year = str(academic_year or "")

        self.header_color = header_color or HEADER_COLORS[0]
        self.text_color = text_color or colors.white

        # REDUCED HEADER HEIGHT
        self.height = 35 * mm

    def wrap(self, availWidth, availHeight):

        self.width = availWidth

        return self.width, self.height

    def draw(self):

        c = self.canv

        w = self.width
        h = self.height

        # --------------------------------
        # HEADER BACKGROUND
        # --------------------------------

        c.setFillColor(self.header_color)

        c.roundRect(
            0, 0,
            w, h,
            3 * mm,
            fill=1,
            stroke=0
        )

        c.setFillColor(self.text_color)

        # --------------------------------
        # DATE - LEFT
        # COLLEGE NAME - RIGHT
        # SAME HORIZONTAL LINE
        # --------------------------------

        c.setFont("Helvetica-Bold", 17)

        c.drawString(
            5 * mm,
            h - 14 * mm,
            self.date
        )

        c.setFont("Helvetica-Bold", 11)

        c.drawRightString(
            w - 5 * mm,
            h - 14 * mm,
            self.college
        )

        # --------------------------------
        # DAY ORDER & ANNOUNCEMENTS
        # --------------------------------

        c.setFont("Helvetica-Bold", 9)

        c.drawRightString(
            w - 5 * mm,
            h - 21 * mm,
            "Day Order & Announcements · AY"
        )

        # --------------------------------
        # ACADEMIC YEAR
        # --------------------------------

        if self.academic_year:

            c.setFont("Helvetica-Bold", 9)

            c.drawRightString(
                w - 5 * mm,
                h - 27 * mm,
                self.academic_year
            )

        # --------------------------------
        # DAY DETAILS - BOTTOM LEFT
        # --------------------------------

        day_color = (
            colors.HexColor("#A9DFFF")
            if self.text_color == colors.white
            else colors.HexColor("#243447")
        )

        c.setFillColor(day_color)

        c.setFont("Helvetica-Bold", 12)

        c.drawString(
            5 * mm,
            6 * mm,
            self.day
        )

        day_width = c.stringWidth(
            self.day,
            "Helvetica-Bold",
            12
        )

        # --------------------------------
        # DAY ORDER AND DAY COUNT
        # --------------------------------

        c.setFillColor(self.text_color)

        c.setFont("Helvetica", 12)

        c.drawString(
            5 * mm + day_width + 5,
            6 * mm,
            f" | Day Order: {self.order} | Day Count: {self.count}"
        )


# ====================================================
# REPORT 1 — DAY SUMMARY PDF
# FIVE DATES PER PAGE
# ====================================================

def create_summary_pdf(
    days_data,
    from_date,
    to_date,
    academic_year=None,
    college="THE NEW COLLEGE"
):

    output = io.BytesIO()

    pdf = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm
    )

    elements = []

    for index, day in enumerate(days_data):

        date_obj = datetime.strptime(
            str(day["notice_date"]),
            "%Y-%m-%d"
        )

        formatted_date = date_obj.strftime(
            "%d %B %Y"
        )

        # Same colour for five dates per page

        page_color_index = index // 5

        header = NoticeHeader(
            date=formatted_date,
            day=day["day_name"],
            order=day["day_order"],
            count=day["day_count"],
            college=college,
            academic_year=academic_year,
            header_color=get_header_color(
                page_color_index
            ),
            text_color=get_header_text_color(
                page_color_index
            )
        )

        elements.append(header)

        if (index + 1) % 5 != 0:

            elements.append(
                Spacer(1, 5 * mm)
            )

        if (
            (index + 1) % 5 == 0
            and index + 1 < len(days_data)
        ):

            elements.append(PageBreak())

    pdf.build(elements)

    output.seek(0)

    return output

# ====================================================
# REPORT 2 — DETAILED NOTICE BOARD PDF
# ONE DATE PER PAGE
# AUTOMATIC FITTING
# ====================================================

def create_notice_board_pdf(
    days_data,
    announcements_map,
    from_date,
    to_date,
    academic_year,
    college="THE NEW COLLEGE"
):

    output = io.BytesIO()

    page_width, page_height = A4

    left_margin = 12 * mm
    right_margin = 12 * mm
    top_margin = 10 * mm
    bottom_margin = 10 * mm

    available_width = (
        page_width
        - left_margin
        - right_margin
    )

    available_height = (
        page_height
        - top_margin
        - bottom_margin
    )

    pdf = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin
    )

    elements = []

    # Announcement card colours

    card_colors = [

        (
            colors.HexColor("#E2F2FC"),
            colors.HexColor("#172B78")
        ),

        (
            colors.HexColor("#E8F4E8"),
            colors.HexColor("#176126")
        ),

        (
            colors.HexColor("#FFF2DF"),
            colors.HexColor("#E65100")
        ),

        (
            colors.HexColor("#F0E8FA"),
            colors.HexColor("#653A91")
        ),

        (
            colors.HexColor("#FCE8E8"),
            colors.HexColor("#B32626")
        )
    ]

    # ----------------------------------------
    # LOOP THROUGH EACH DATE
    # ----------------------------------------

    for day_index, day in enumerate(days_data):

        date_elements = []

        # ------------------------------------
        # DATE FORMATTING
        # ------------------------------------

        date_obj = datetime.strptime(
            str(day["notice_date"]),
            "%Y-%m-%d"
        )

        formatted_date = date_obj.strftime(
            "%d %B %Y"
        )

        # ------------------------------------
        # HEADER WITH CHANGING COLOUR
        # ------------------------------------

        date_color = get_header_color(day_index)

        date_text_color = get_header_text_color(
            day_index
        )

        date_elements.append(
            NoticeHeader(
                date=formatted_date,
                day=day["day_name"],
                order=day["day_order"],
                count=day["day_count"],
                college=college,
                academic_year=academic_year,
                header_color=date_color,
                text_color=date_text_color
            )
        )

        date_elements.append(
            Spacer(1, 4 * mm)
        )

        # ------------------------------------
        # GET ANNOUNCEMENTS
        # ------------------------------------

        announcements = announcements_map.get(
            day["id"], []
        )

        if not announcements:

            date_elements.append(
                AnnouncementCard(
                    number=1,
                    title="No Announcements",
                    message="No announcements available for this date.",
                    bg=card_colors[0][0],
                    title_color=card_colors[0][1]
                )
            )

        else:

            for index, ann in enumerate(announcements):

                bg, title_color = card_colors[
                    index % len(card_colors)
                ]

                title = ann.get("title") or ""
                message = ann.get("message") or ""

                date_elements.append(
                    AnnouncementCard(
                        number=index + 1,
                        title=title,
                        message=message,
                        bg=bg,
                        title_color=title_color
                    )
                )

                date_elements.append(
                    Spacer(1, 3 * mm)
                )

        # ------------------------------------
        # FIT EVERYTHING WITHIN ONE PAGE
        # ------------------------------------

        fitted_page = KeepInFrame(
            maxWidth=available_width,
            maxHeight=available_height,
            content=date_elements,
            mode="shrink",
            hAlign="LEFT",
            vAlign="TOP"
        )

        elements.append(fitted_page)

        # ------------------------------------
        # FORCE NEW PAGE FOR NEXT DATE
        # ------------------------------------

        if day_index < len(days_data) - 1:

            elements.append(PageBreak())

    pdf.build(elements)

    output.seek(0)

    return output




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
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 Add / Update Notice",
    "🗑️ Manage Days",
    "📢 Manage Announcements",
    "✏️ Edit Notice Board",
    "📄 Generate Reports"
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
                if ann["title"].strip() or ann["message"].strip():
                    supabase.table("announcements").insert({
                        "day_id": day_id,
                        "title": ann["title"].strip(),
                        "message": ann["message"].strip()
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

    else:

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
                    # Skip ONLY if both are empty
                    if not ann["title"].strip() and not ann["message"].strip():
                        continue

                    if ann.get("id"):
                        supabase.table("announcements").update({
                            "title": ann["title"].strip(),
                            "message": ann["message"].strip()
                        }).eq("id", ann["id"]).execute()
                    else:
                        supabase.table("announcements").insert({
                            "day_id": day["id"],
                            "title": ann["title"].strip(),
                            "message": ann["message"].strip()
                        }).execute()


                del st.session_state.edit_announcements
                st.success("✅ Notice board updated successfully")
                st.rerun()

            except APIError:
                st.error("❌ Failed to update notice board")


# ====================================================
# TAB 5 — SESSION-WISE REPORT GENERATION
# ====================================================

with tab5:

    st.subheader("📄 Generate Notice Board Reports")

    # ============================================
    # OPTIONAL ACADEMIC YEAR
    # ============================================

    academic_year = st.text_input(
        "🎓 Academic Year (Optional)",
        value="",
        placeholder="Example: 2026–2027",
        key="report_academic_year"
    ).strip() or None

    st.divider()

    # ============================================
    # FETCH NOTICE BOARD DAYS
    # ============================================

    try:

        all_days = (
            supabase.table("notice_board_days")
            .select("*")
            .order("notice_date", desc=False)
            .execute()
            .data
        )

    except Exception as e:

        st.error(f"Error fetching records: {e}")
        all_days = []

    # ============================================
    # DETECT SESSIONS
    # ============================================

    sessions = detect_notice_periods(all_days)

    if not sessions:

        st.info("No notice board records found.")

    else:

        st.subheader("📅 Session Summary")

        session_table = []

        for i, session in enumerate(sessions):

            session_table.append({

                "Session": f"Session {i + 1}",
                "Start Date": session["start_date"],
                "End Date": session["end_date"],
                "Starting Count": session["start_count"],
                "Last Day Count": session["last_count"],
                "Status": session["status"]

            })

        st.dataframe(
            session_table,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        # ========================================
        # INDIVIDUAL SESSION CONTAINERS
        # ========================================

        for i, session in enumerate(sessions):

            session_number = i + 1

            session_key = f"session_reports_{i}"

            with st.container(border=True):

                # =================================
                # SESSION HEADER
                # =================================

                col1, col2 = st.columns([3, 1])

                with col1:

                    st.subheader(
                        f"📘 Session {session_number}"
                    )

                with col2:

                    if session["status"] == "Completed":
                        st.success("Completed")

                    elif session["status"] == "In Progress":
                        st.info("In Progress")

                    else:
                        st.warning("Closed")

                # =================================
                # DATE DETAILS
                # =================================

                col1, col2 = st.columns(2)

                with col1:

                    st.markdown("**📅 Start Date**")

                    st.write(
                        datetime.strptime(
                            str(session["start_date"]),
                            "%Y-%m-%d"
                        ).strftime("%d %B %Y")
                    )

                with col2:

                    st.markdown("**📅 End Date**")

                    st.write(
                        datetime.strptime(
                            str(session["end_date"]),
                            "%Y-%m-%d"
                        ).strftime("%d %B %Y")
                    )

                # =================================
                # DAY COUNT
                # =================================

                col1, col2 = st.columns(2)

                with col1:

                    st.metric(
                        "Starting Day Count",
                        session["start_count"]
                    )

                with col2:

                    st.metric(
                        "Last Day Count",
                        f'{session["last_count"]} / 90'
                    )

                st.caption(
                    f"Total Notice Board Dates: "
                    f"{len(session['records'])}"
                )

                if academic_year:

                    st.caption(
                        f"Academic Year: {academic_year}"
                    )

                st.divider()

                # =================================
                # GENERATE BUTTON
                # =================================

                if st.button(
                    f"📄 Generate Reports – Session {session_number}",
                    key=f"generate_session_{i}",
                    use_container_width=True
                ):

                    try:

                        days_data = session["records"]

                        # ----------------------------
                        # FETCH ANNOUNCEMENTS
                        # ----------------------------

                        day_ids = [
                            d["id"] for d in days_data
                        ]

                        announcements_data = []

                        if day_ids:

                            announcements_data = (
                                supabase.table("announcements")
                                .select("*")
                                .in_("day_id", day_ids)
                                .execute()
                                .data
                            )

                        # ----------------------------
                        # GROUP ANNOUNCEMENTS
                        # ----------------------------

                        announcements_map = {}

                        for ann in announcements_data:

                            announcements_map.setdefault(
                                ann["day_id"], []
                            ).append(ann)

                        # ----------------------------
                        # GENERATE BOTH REPORTS
                        # ----------------------------

                        with st.spinner(
                            f"Generating Session {session_number} reports..."
                        ):

                            summary_pdf = create_summary_pdf(

                                days_data=days_data,

                                from_date=session["start_date"],

                                to_date=session["end_date"],

                                academic_year=academic_year,

                                college="THE NEW COLLEGE"

                            )

                            detailed_pdf = create_notice_board_pdf(

                                days_data=days_data,

                                announcements_map=announcements_map,

                                from_date=session["start_date"],

                                to_date=session["end_date"],

                                academic_year=academic_year,

                                college="THE NEW COLLEGE"

                            )

                            # Store PDF bytes in session state
                            st.session_state[session_key] = {

                                "summary": summary_pdf.getvalue(),

                                "detailed": detailed_pdf.getvalue(),

                                "total_days": len(days_data),

                                "total_announcements": len(
                                    announcements_data
                                )

                            }

                        st.success(
                            f"✅ Reports generated for Session "
                            f"{session_number}!"
                        )

                    except Exception as e:

                        import traceback

                        st.error(
                            f"❌ Error generating reports: {e}"
                        )

                        st.code(
                            traceback.format_exc(),
                            language="python"
                        )

                # =================================
                # SHOW GENERATED REPORTS
                # =================================

                reports = st.session_state.get(session_key)

                if reports:

                    st.divider()

                    st.success(
                        f"✅ Reports Ready | "
                        f"{reports['total_days']} Dates | "
                        f"{reports['total_announcements']} Announcements"
                    )

                    # =================================
                    # REPORT 1
                    # =================================

                    st.subheader(
                        "📘 Report 1 – Day Summary"
                    )

                    st.write(
                        "Contains Date, Day, Day Order and "
                        "Day Count. Five entries per page."
                    )

                    st.download_button(

                        label="⬇️ Download Report 1 – Day Summary",

                        data=reports["summary"],

                        file_name=(
                            f"Notice_Board_Summary_"
                            f"Session_{session_number}.pdf"
                        ),

                        mime="application/pdf",

                        key=f"download_summary_{i}",

                        use_container_width=True

                    )

                    st.divider()

                    # =================================
                    # REPORT 2
                    # =================================

                    st.subheader(
                        "📗 Report 2 – Detailed Notice Board"
                    )

                    st.write(
                        "Contains Date, Day, Day Order, "
                        "Day Count and all announcements. "
                        "One date per page."
                    )

                    st.download_button(

                        label="⬇️ Download Report 2 – Detailed Notice Board",

                        data=reports["detailed"],

                        file_name=(
                            f"Notice_Board_Detailed_"
                            f"Session_{session_number}.pdf"
                        ),

                        mime="application/pdf",

                        key=f"download_detailed_{i}",

                        use_container_width=True

                    )

                else:

                    st.info(
                        "Click Generate Reports to generate "
                        "both reports for this Session."
                    )
