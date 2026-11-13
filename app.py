import os
import re
import streamlit as st
import pandas as pd
import datetime
from dotenv import load_dotenv, set_key

import db

# Cấu hình trang giao diện
st.set_page_config(
    page_title="Phòng Khám Đa Khoa - Quản Lý & Báo Cáo",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Tải cấu hình từ .env
load_dotenv()


def fmt_vnd(amount):
    try:
        val = float(amount or 0)
        return f"{val:,.0f} đ".replace(",", ".")
    except Exception:
        return f"{amount} đ"


# Helper kiểm tra định dạng CMT/CCCD (đúng 12 chữ số)
def validate_cmt(cmt: str) -> tuple[bool, str]:
    s = (cmt or "").strip()
    if not s:
        return False, "Số CMT/CCCD không được để trống."
    if not re.fullmatch(r"\d{12}", s):
        return False, "Số CMT/CCCD phải gồm đúng 12 chữ số (ví dụ: 001080012345)."
    return True, ""


# Helper kiểm tra định dạng SĐT (chỉ gồm chữ số, 10-11 số)
def validate_sdt(sdt: str, allow_empty: bool = True) -> tuple[bool, str]:
    s = (sdt or "").strip()
    if not s:
        if allow_empty:
            return True, ""
        return False, "Số điện thoại không được để trống."
    if not re.fullmatch(r"\d{10,11}", s):
        return False, "Số điện thoại chỉ gồm chữ số và phải có từ 10 đến 11 số (ví dụ: 0901234567)."
    return True, ""


def inject_css():
    st.markdown(
        """
        <style>
        /* =============================================================
           BỘ NHẬN DIỆN PHÒNG KHÁM AN TÂM (THEO GIAO DIỆN THAM CHIẾU)
           Màu chủ đạo:
           - Ink: #183b42
           - Muted: #5c7377
           - Teal (chính): #087e78
           - Teal Dark (hover, số lớn, tiêu đề): #06635f
           - Line (viền): #d5e5e4
           - Background: #f4f8f7
           - White: #ffffff
           - Input border: #a8c5c2
           - Focus outline: #e39d48
           - Error: nền #fce9e7 chữ #9a2a27
           - Success: nền #d9f3e6 chữ #20563c
           ============================================================= */

        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
            font-family: Arial, "Segoe UI", sans-serif !important;
            color: #183b42 !important;
            background-color: #f4f8f7 !important;
        }

        /* 3. Thanh trên cùng Header */
        .top-header-banner {
            background: transparent !important;
            border: none !important;
            padding: 8px 0 !important;
            margin: 0 !important;
            box-shadow: none !important;
        }
        .top-header-brand {
            color: #06635f;
            font-size: 22px;
            font-weight: 800;
            line-height: 1.25;
            letter-spacing: -0.01em;
        }
        .top-header-sub {
            color: #5c7377;
            font-size: 13px;
            font-weight: 500;
            margin-top: 3px;
        }

        /* 4. Dòng mô tả ngắn dưới st.header */
        .page-desc {
            color: #5c7377 !important;
            font-size: 14.5px !important;
            margin-top: -6px !important;
            margin-bottom: 16px !important;
            line-height: 1.5 !important;
        }

        /* 5. Chân trang */
        footer.custom-footer {
            display: block;
            text-align: center;
            font-size: 13px !important;
            color: #5c7377 !important;
            padding: 24px 0 32px 0 !important;
        }

        /* 2a. Nút chính nền #087e78, chữ trắng, bo 8px, cao tối thiểu 44px, hover #06635f */
        .stButton > button,
        .stFormSubmitButton > button,
        button[kind="primary"],
        [data-testid="baseButton-primary"],
        [data-testid="stBaseButton-primary"] {
            background-color: #087e78 !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            min-height: 44px !important;
            padding: 9px 18px !important;
            font-weight: 700 !important;
            border: none !important;
            box-shadow: none !important;
            transition: background-color 0.18s ease !important;
        }
        .stButton > button:hover,
        .stFormSubmitButton > button:hover,
        button[kind="primary"]:hover,
        [data-testid="baseButton-primary"]:hover,
        [data-testid="stBaseButton-primary"]:hover {
            background-color: #06635f !important;
            color: #ffffff !important;
        }
        .stButton > button p,
        .stFormSubmitButton > button p,
        button[kind="primary"] p {
            color: #ffffff !important;
            font-weight: 700 !important;
        }

        /* Nút phụ / secondary */
        button[kind="secondary"],
        [data-testid="baseButton-secondary"],
        [data-testid="stBaseButton-secondary"] {
            border-radius: 8px !important;
            min-height: 44px !important;
            font-weight: 600 !important;
            border: 1px solid #d5e5e4 !important;
            background-color: #ffffff !important;
            color: #06635f !important;
        }
        button[kind="secondary"]:hover,
        [data-testid="baseButton-secondary"]:hover,
        [data-testid="stBaseButton-secondary"]:hover {
            background-color: #e6f5f2 !important;
            color: #06635f !important;
        }

        /* 2b. st.metric hiện như thẻ: nền trắng, viền 1px #d5e5e4, bo 15px, đổ bóng nhẹ, số lớn màu #06635f */
        [data-testid="stMetric"] {
            background-color: #ffffff !important;
            border: 1px solid #d5e5e4 !important;
            border-radius: 15px !important;
            padding: 14px 16px !important;
            box-shadow: 0 3px 15px rgba(23, 59, 66, 0.04) !important;
        }
        [data-testid="stMetricLabel"],
        [data-testid="stMetricLabel"] * {
            color: #5c7377 !important;
            font-size: 14px !important;
            font-weight: 600 !important;
        }
        [data-testid="stMetricValue"],
        [data-testid="stMetricValue"] * {
            color: #06635f !important;
            font-size: 24px !important;
            font-weight: 800 !important;
            white-space: normal !important;
            word-break: break-word !important;
        }

        /* 2c. st.container(border=True) / expander / tab: nền trắng, viền #d5e5e4, bo 15px */
        [data-testid="stVerticalBlockBorderWrapper"],
        [data-testid="stVerticalBlockBorderWrapper"] > div {
            background-color: #ffffff !important;
            border: 1px solid #d5e5e4 !important;
            border-radius: 15px !important;
            box-shadow: 0 3px 15px rgba(23, 59, 66, 0.04) !important;
        }
        [data-testid="stExpander"] {
            background-color: #ffffff !important;
            border: 1px solid #d5e5e4 !important;
            border-radius: 15px !important;
            overflow: hidden !important;
            box-shadow: 0 3px 15px rgba(23, 59, 66, 0.04) !important;
        }
        [data-testid="stExpander"] details {
            border: none !important;
        }
        [data-testid="stExpanderSummary"] {
            background-color: #ffffff !important;
            border-radius: 15px 15px 0 0 !important;
            color: #183b42 !important;
            font-weight: 600 !important;
        }
        [data-testid="stExpanderDetails"] {
            border-top: 1px solid #d5e5e4 !important;
        }
        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            background-color: transparent !important;
            border-bottom: 1px solid #d5e5e4 !important;
            gap: 8px !important;
        }
        [data-testid="stTabs"] [data-baseweb="tab"] {
            border-radius: 10px 10px 0 0 !important;
            color: #5c7377 !important;
            font-weight: 600 !important;
            padding: 10px 16px !important;
            border: none !important;
            background-color: transparent !important;
        }
        [data-testid="stTabs"] [aria-selected="true"] {
            color: #06635f !important;
            font-weight: 700 !important;
            background-color: #ffffff !important;
            border-bottom: 3px solid #087e78 !important;
        }
        [data-testid="stTabs"] [data-testid="stTabsContent"] {
            background-color: #ffffff !important;
            border: 1px solid #d5e5e4 !important;
            border-top: none !important;
            border-radius: 0 0 15px 15px !important;
            padding: 20px !important;
            box-shadow: 0 3px 15px rgba(23, 59, 66, 0.04) !important;
        }

        /* 2d. Bảng st.dataframe: viền #d5e5e4, bo góc */
        [data-testid="stDataFrame"],
        [data-testid="stTable"] {
            border: 1px solid #d5e5e4 !important;
            border-radius: 12px !important;
            overflow: hidden !important;
            background-color: #ffffff !important;
            box-shadow: 0 2px 8px rgba(23, 59, 66, 0.02) !important;
        }

        /* 2e. Ô nhập: viền #a8c5c2, bo 8px */
        input[type="text"],
        input[type="number"],
        input[type="password"],
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stDateInput"] input,
        [data-baseweb="input"] input,
        [data-baseweb="input"],
        [data-baseweb="base-input"],
        div[data-baseweb="select"] > div {
            border: 1px solid #a8c5c2 !important;
            border-radius: 8px !important;
            min-height: 42px !important;
            background-color: #ffffff !important;
            color: #183b42 !important;
        }

        /* 2f. Focus: outline 3px #e39d48 */
        input:focus,
        input:focus-visible,
        select:focus-visible,
        button:focus-visible,
        [data-baseweb="input"]:focus-within,
        [data-baseweb="select"]:focus-within,
        [data-baseweb="base-input"]:focus-within {
            outline: 3px solid #e39d48 !important;
            outline-offset: 2px !important;
            border-color: #e39d48 !important;
        }

        /* 2g. Thông báo lỗi nền #fce9e7 chữ #9a2a27; thành công nền #d9f3e6 chữ #20563c */
        [data-testid="stAlert"] {
            border-radius: 9px !important;
            border: none !important;
        }
        div[data-testid="stAlert"]:has([data-testid="stNotificationContentError"]),
        div:has(> [data-testid="stNotificationContentError"]),
        .stAlert:has([data-testid="stNotificationContentError"]) {
            background-color: #fce9e7 !important;
            color: #9a2a27 !important;
        }
        [data-testid="stNotificationContentError"],
        [data-testid="stNotificationContentError"] * {
            color: #9a2a27 !important;
        }
        [data-testid="stAlert"] [data-testid="stNotificationContentError"] svg {
            fill: #9a2a27 !important;
            color: #9a2a27 !important;
        }
        div[data-testid="stAlert"]:has([data-testid="stNotificationContentSuccess"]),
        div:has(> [data-testid="stNotificationContentSuccess"]),
        .stAlert:has([data-testid="stNotificationContentSuccess"]) {
            background-color: #d9f3e6 !important;
            color: #20563c !important;
        }
        [data-testid="stNotificationContentSuccess"],
        [data-testid="stNotificationContentSuccess"] * {
            color: #20563c !important;
        }
        [data-testid="stAlert"] [data-testid="stNotificationContentSuccess"] svg {
            fill: #20563c !important;
        }

        /* Hide sidebar completely */
        [data-testid="stSidebar"] { display: none !important; }
        section[data-testid="stSidebarContent"] { display: none !important; }
        button[data-testid="collapsedControl"] { display: none !important; }

        /* Pill navigation (st.radio horizontal) */
        div[data-testid="stRadio"] > div,
        div[data-testid="stRadio"] [data-testid="stRadioGroup"] {
            display: flex !important;
            flex-direction: row !important;
            gap: 8px !important;
            flex-wrap: wrap !important;
            align-items: center !important;
            background: transparent !important;
        }
        div[data-testid="stRadio"] label[data-baseweb="radio"],
        div[data-testid="stRadio"] label[data-testid="stRadioOption"] {
            background: #f0f7f6 !important;
            border: 1.5px solid #d5e5e4 !important;
            border-radius: 24px !important;
            padding: 8px 18px !important;
            cursor: pointer !important;
            font-size: 14.5px !important;
            font-weight: 500 !important;
            color: #183b42 !important;
            transition: all 0.15s ease-in-out !important;
            white-space: nowrap !important;
            display: inline-flex !important;
            align-items: center !important;
            margin-bottom: 0 !important;
        }
        div[data-testid="stRadio"] label[data-baseweb="radio"]:hover,
        div[data-testid="stRadio"] label[data-testid="stRadioOption"]:hover {
            background: #e6f5f2 !important;
            border-color: #087e78 !important;
        }
        div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked),
        div[data-testid="stRadio"] label[data-testid="stRadioOption"]:has(input:checked),
        div[data-testid="stRadio"] label[data-testid="stRadioOption"][data-selected="true"] {
            background: #087e78 !important;
            border-color: #087e78 !important;
            color: #ffffff !important;
            font-weight: 700 !important;
        }
        div[data-testid="stRadio"] label[data-testid="stRadioOption"]:has(input:checked) p,
        div[data-testid="stRadio"] label[data-testid="stRadioOption"][data-selected="true"] p,
        div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) div {
            color: #ffffff !important;
            font-weight: 700 !important;
        }
        /* Hide the actual radio circle */
        div[data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child,
        div[data-testid="stRadio"] label[data-testid="stRadioOption"] > div > div:first-child:not([data-testid="stMarkdownContainer"]) {
            display: none !important;
        }

        /* Nav divider */
        hr.nav-divider {
            border: none !important;
            border-top: 1.5px solid #d5e5e4 !important;
            margin: 4px 0 20px 0 !important;
        }

        /* Top header in col layout */
        .top-header-banner {
            background: transparent !important;
            border: none !important;
            padding: 8px 0 !important;
            margin: 0 !important;
            box-shadow: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


# Kích hoạt style giao diện
inject_css()

# Kiểm tra trạng thái kết nối CSDL
is_connected, conn_msg = db.test_connection()

# Top nav (2-column layout: brand left, nav right)
col_brand, col_nav = st.columns([1, 3])
with col_brand:
    st.markdown(
        '<div class="top-header-banner">'
        '<div class="top-header-brand">✚ Phòng khám An Tâm</div>'
        '<div class="top-header-sub">Quản lý cơ sở dữ liệu</div>'
        '</div>',
        unsafe_allow_html=True
    )
with col_nav:
    nav = st.radio(
        "",
        ["Tổng quan", "Bệnh nhân", "Danh sách", "Báo cáo", "Nhập dữ liệu"],
        horizontal=True,
        label_visibility="collapsed",
        key="main_nav"
    )

st.markdown('<hr class="nav-divider"/>', unsafe_allow_html=True)

if not is_connected:
    st.warning("⚠️ **Chưa kết nối được với cơ sở dữ liệu**")
    st.markdown("""
    Vui lòng kiểm tra các bước sau:
    1. Đảm bảo dịch vụ MySQL đang chạy trên máy tính.
    2. Đã nạp file dữ liệu `phong_kham.sql` vào MySQL.
    3. Nhập mật khẩu MySQL chính xác vào ô bên dưới và bấm **Lưu .env** hoặc **Kết nối lại**.
    """)
    with st.expander("⚙️ Cấu hình kết nối MySQL", expanded=True):
        db_host = st.text_input("DB Host", value=os.getenv("DB_HOST", "localhost"), key="top_db_host")
        db_port = st.text_input("DB Port", value=os.getenv("DB_PORT", "3306"), key="top_db_port")
        db_user = st.text_input("DB User", value=os.getenv("DB_USER", "root"), key="top_db_user")
        db_pass = st.text_input("DB Password", value=os.getenv("DB_PASSWORD", ""), type="password", key="top_db_pass")
        db_name = st.text_input("DB Name", value=os.getenv("DB_NAME", "phong_kham"), key="top_db_name")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Kết nối lại", use_container_width=True, key="top_reconnect"):
                os.environ["DB_HOST"] = db_host
                os.environ["DB_PORT"] = db_port
                os.environ["DB_USER"] = db_user
                os.environ["DB_PASSWORD"] = db_pass
                os.environ["DB_NAME"] = db_name
                st.rerun()
        with col_btn2:
            if st.button("Lưu .env", use_container_width=True, key="top_save_env"):
                dotenv_path = os.path.join(os.getcwd(), ".env")
                set_key(dotenv_path, "DB_HOST", db_host)
                set_key(dotenv_path, "DB_PORT", db_port)
                set_key(dotenv_path, "DB_USER", db_user)
                set_key(dotenv_path, "DB_PASSWORD", db_pass)
                set_key(dotenv_path, "DB_NAME", db_name)
                st.success("Đã lưu vào .env!")
    st.stop()

# =====================================================================
# MENU 1: TỔNG QUAN
# =====================================================================
if nav == "Tổng quan":
    st.header("🏥 Tổng Quan Phòng Khám")
    st.markdown("<p class='page-desc'>Thống kê tổng thể và hoạt động gần đây của phòng khám.</p>", unsafe_allow_html=True)

    # 4 metric cards
    m1, m2, m3, m4 = st.columns(4)
    ok_cnt_bn, rows_cnt_bn, _ = db.execute_query("SELECT COUNT(*) AS cnt FROM benh_nhan")
    ok_cnt_bs, rows_cnt_bs, _ = db.execute_query("SELECT COUNT(*) AS cnt FROM bac_sy")
    ok_cnt_yt, rows_cnt_yt, _ = db.execute_query("SELECT COUNT(*) AS cnt FROM y_ta")
    ok_cnt_dot, rows_cnt_dot, _ = db.execute_query("SELECT COUNT(*) AS cnt FROM dot_benh WHERE ngay_ket_thuc IS NULL")

    with m1:
        cnt_bn = rows_cnt_bn[0]["cnt"] if ok_cnt_bn and rows_cnt_bn else 0
        st.metric("Bệnh nhân", cnt_bn)
    with m2:
        cnt_bs = rows_cnt_bs[0]["cnt"] if ok_cnt_bs and rows_cnt_bs else 0
        st.metric("Bác sỹ", cnt_bs)
    with m3:
        cnt_yt = rows_cnt_yt[0]["cnt"] if ok_cnt_yt and rows_cnt_yt else 0
        st.metric("Y tá", cnt_yt)
    with m4:
        cnt_dot = rows_cnt_dot[0]["cnt"] if ok_cnt_dot and rows_cnt_dot else 0
        st.metric("Đợt đang điều trị", cnt_dot)

    st.markdown("---")

    # Lần khám gần đây
    st.subheader("Lần khám gần đây")
    ok_lk, lk_recent, _ = db.execute_query("""
        SELECT lk.ma_lan_kham, lk.ngay_vao, lk.ngay_ra, bn.ho_ten, b.ten_benh,
               nv.ho_ten AS ten_bs, lk.tong_tien
        FROM lan_kham lk
        JOIN dot_benh d ON d.ma_dot = lk.ma_dot
        JOIN benh_nhan bn ON bn.ma_bn = d.ma_bn
        JOIN benh b ON b.ma_benh = d.ma_benh
        JOIN nhan_vien nv ON nv.ma_nv = d.ma_bs
        ORDER BY lk.ngay_vao DESC, lk.ma_lan_kham DESC
        LIMIT 8
    """)
    if ok_lk and lk_recent:
        df_lk_recent = pd.DataFrame(lk_recent)
        df_lk_recent["tong_tien"] = df_lk_recent["tong_tien"].apply(fmt_vnd)
        df_lk_recent.columns = ["Mã LK", "Ngày Vào", "Ngày Ra", "Bệnh Nhân", "Tên Bệnh", "Bác Sỹ", "Tổng Tiền"]
        st.dataframe(df_lk_recent, use_container_width=True, hide_index=True)
    else:
        st.info("Chưa có lần khám nào trong hệ thống.")

    st.markdown("---")

    # Tải trọng bác sỹ
    st.subheader("Tải trọng bác sỹ")
    ok_wl, wl_rows, _ = db.execute_query("""
        SELECT nv.ho_ten, COUNT(d.ma_dot) AS so_dot_hien_tai
        FROM bac_sy bs
        JOIN nhan_vien nv ON nv.ma_nv = bs.ma_nv
        LEFT JOIN dot_benh d ON d.ma_bs = bs.ma_nv AND d.ngay_ket_thuc IS NULL
        GROUP BY bs.ma_nv, nv.ho_ten
        ORDER BY so_dot_hien_tai DESC
    """)
    if ok_wl and wl_rows:
        df_wl = pd.DataFrame(wl_rows)
        df_wl.columns = ["Bác Sỹ", "Đợt Đang Điều Trị (/ tối đa 30)"]
        st.dataframe(df_wl, use_container_width=True, hide_index=True)
    else:
        st.info("Chưa có dữ liệu bác sỹ.")
    st.caption("Mỗi bác sỹ phụ trách tối đa 30 đợt bệnh đang điều trị cùng lúc.")

# =====================================================================
# MENU 2: BỆNH NHÂN
# =====================================================================
elif nav == "Bệnh nhân":
    st.header("👥 Bệnh Nhân")
    tab_tracuu, tab_quanly = st.tabs(["🔍 Tra cứu hồ sơ", "👥 Quản lý bệnh nhân"])

    # ---- Tab 1: Tra cứu hồ sơ (old menu 3) ----
    with tab_tracuu:
        st.subheader("🔍 Tra Cứu Hồ Sơ Khám Chữa Bệnh")
        st.markdown("<p class='page-desc'>Xem thông tin cá nhân, tình trạng bệnh hiện tại và toàn bộ lịch sử khám chữa bệnh của bệnh nhân.</p>", unsafe_allow_html=True)
        st.caption("Kết quả tự cập nhật khi bạn đổi lựa chọn.")

        ok_bn, bn_list, _ = db.execute_query("SELECT ma_bn, ma_so, ho_ten, cmt FROM benh_nhan ORDER BY ma_bn")

        if ok_bn and bn_list:
            bn_options = {f"{b['ma_so']} - {b['ho_ten']} (CMT: {b['cmt']})": b["ma_bn"] for b in bn_list}
            selected_label = st.selectbox("Chọn bệnh nhân để tra cứu:", options=list(bn_options.keys()), key="tracuu_sel")
            ma_bn = bn_options[selected_label]
        else:
            ma_bn = st.number_input("Nhập Mã Bệnh Nhân (ID):", min_value=1, value=1, key="tracuu_id")

        success, results, err = db.call_procedure("sp_thong_tin_benh_nhan", (ma_bn,))

        if not success:
            st.error(f"❌ Lỗi khi tra cứu: {err}")
        elif results and len(results) >= 3:
            info_rows = results[0]
            history_rows = results[1]
            active_rows = results[2]

            if not info_rows:
                st.warning("Không tìm thấy thông tin bệnh nhân này.")
            else:
                bn = info_rows[0]
                st.subheader("👤 Thông Tin Bệnh Nhân")
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.write(f"**Mã số:** `{bn['ma_so']}`")
                    st.write(f"**Họ tên:** **{bn['ho_ten']}**")
                with c2:
                    st.write(f"**Số CMT/CCCD:** `{bn['cmt']}`")
                    st.write(f"**Ngày sinh:** {bn['ngay_sinh']}")
                with c3:
                    st.write(f"**Số điện thoại:** {bn['sdt']}")
                    st.write(f"**Địa chỉ:** {bn['dia_chi']}")
                with c4:
                    st.write(f"**Số loại bệnh từng mắc:** {len(set(r['ten_benh'] for r in history_rows)) if history_rows else 0}")
                    st.write(f"**Tổng số lần khám:** {len(history_rows) if history_rows else 0}")

                st.markdown("---")

                st.subheader("🩺 Tình Trạng Bệnh Hiện Tại (Đang Điều Trị)")
                if not active_rows:
                    st.success("✅ Hiện tại bệnh nhân không có bệnh nào đang điều trị (đã chữa khỏi hoặc chưa có đợt mới).")
                else:
                    df_active = pd.DataFrame(active_rows)
                    df_active.columns = ["Tên Bệnh Đang Mắc", "Ngày Bắt Đầu Đợt", "Đã Khám Lần Thứ Mấy", "Bác Sỹ Phụ Trách"]
                    st.dataframe(df_active, use_container_width=True, hide_index=True)

                st.subheader("📜 Toàn Bộ Lịch Sử Khám Chữa Bệnh")
                if not history_rows:
                    st.info("Bệnh nhân chưa có lịch sử khám chữa bệnh nào.")
                else:
                    df_hist = pd.DataFrame(history_rows)
                    df_hist["phi_kham"] = df_hist["phi_kham"].apply(fmt_vnd)
                    df_hist["tong_tien"] = df_hist["tong_tien"].apply(fmt_vnd)
                    df_hist.columns = [
                        "Tên Bệnh", "Lần Mắc Thứ (Đợt)", "Lần Khám Thứ (Trong đợt)",
                        "Ngày Vào", "Ngày Ra", "Bác Sỹ Phụ Trách", "Phí Khám", "Tổng Tiền (Kèm thuốc)"
                    ]
                    st.dataframe(df_hist, use_container_width=True, hide_index=True)

    # ---- Tab 2: Quản lý bệnh nhân (old menu 5) ----
    with tab_quanly:
        st.subheader("👥 Quản Lý Bệnh Nhân")
        st.markdown("<p class='page-desc'>Tra cứu, thêm mới, chỉnh sửa thông tin hoặc xóa hồ sơ bệnh nhân.</p>", unsafe_allow_html=True)

        keyword = st.text_input("🔍 Tìm kiếm theo tên, mã số (BN...) hoặc số CMT/CCCD:", value="", key="quanly_kw")

        if keyword.strip():
            kw = f"%{keyword.strip()}%"
            ok_bn, bn_list, err = db.execute_query(
                "SELECT ma_bn, ma_so, cmt, ho_ten, ngay_sinh, dia_chi, sdt FROM benh_nhan WHERE ho_ten LIKE %s OR ma_so LIKE %s OR cmt LIKE %s ORDER BY ma_bn DESC",
                (kw, kw, kw)
            )
        else:
            ok_bn, bn_list, err = db.execute_query(
                "SELECT ma_bn, ma_so, cmt, ho_ten, ngay_sinh, dia_chi, sdt FROM benh_nhan ORDER BY ma_bn DESC"
            )

        if ok_bn and bn_list:
            df_bn = pd.DataFrame(bn_list)
            df_bn.columns = ["Mã BN", "Mã Số", "Số CMT/CCCD", "Họ Tên", "Ngày Sinh", "Địa Chỉ", "Số Điện Thoại"]
            st.dataframe(df_bn, use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có bệnh nhân nào hoặc không tìm thấy kết quả phù hợp.")

        st.markdown("---")
        tab_add, tab_edit, tab_del = st.tabs(["➕ Thêm Bệnh Nhân Mới", "✏️ Sửa Thông Tin Bệnh Nhân", "🗑️ Xóa Bệnh Nhân"])

        # Thêm bệnh nhân
        with tab_add:
            st.subheader("Nhập thông tin bệnh nhân mới")
            with st.form("form_add_bn", clear_on_submit=True):
                f_col1, f_col2 = st.columns(2)
                with f_col1:
                    new_ms = st.text_input("Mã số bệnh nhân (*)", placeholder="Ví dụ: BN005").strip()
                    new_cmt = st.text_input("Số CMT / CCCD (*)", placeholder="12 chữ số").strip()
                    new_ten = st.text_input("Họ và tên (*)", placeholder="Nguyễn Văn A").strip()
                with f_col2:
                    new_ns = st.date_input("Ngày sinh (*)", value=datetime.date(1995, 1, 1), min_value=datetime.date(1920, 1, 1), max_value=datetime.date.today())
                    new_sdt = st.text_input("Số điện thoại", placeholder="0901234567").strip()
                    new_dc = st.text_input("Địa chỉ", placeholder="Số nhà, đường, quận/huyện, tỉnh/thành").strip()

                btn_submit_add = st.form_submit_button("Lưu bệnh nhân", type="primary")

            if btn_submit_add:
                if not new_ms or not new_cmt or not new_ten:
                    st.error("❌ Vui lòng điền đầy đủ các thông tin bắt buộc (*): Mã số, CMT, Họ tên.")
                else:
                    ok_cmt, msg_cmt = validate_cmt(new_cmt)
                    if not ok_cmt:
                        st.error(f"❌ {msg_cmt}")
                    else:
                        ok_sdt, msg_sdt = validate_sdt(new_sdt, allow_empty=True)
                        if not ok_sdt:
                            st.error(f"❌ {msg_sdt}")
                        else:
                            sql_insert = "INSERT INTO benh_nhan (ma_so, cmt, ho_ten, ngay_sinh, dia_chi, sdt) VALUES (%s, %s, %s, %s, %s, %s)"
                            ok, _, err_msg = db.execute_statement(sql_insert, (new_ms, new_cmt, new_ten, str(new_ns), new_dc, new_sdt))
                            if not ok:
                                st.error(f"❌ {err_msg}")
                            else:
                                st.success(f"✅ Đã thêm bệnh nhân **{new_ten}** ({new_ms}) thành công!")
                                st.rerun()

        # Sửa bệnh nhân
        with tab_edit:
            st.subheader("Cập nhật thông tin bệnh nhân")
            if ok_bn and bn_list:
                options_edit = {f"{b['ma_so']} - {b['ho_ten']} (CMT: {b['cmt']})": b for b in bn_list}
                sel_label = st.selectbox("Chọn bệnh nhân cần sửa:", options=list(options_edit.keys()), key="sel_edit_bn")
                cur_bn = options_edit[sel_label]

                with st.form("form_edit_bn"):
                    e_col1, e_col2 = st.columns(2)
                    with e_col1:
                        st.text_input("Mã số (Không đổi)", value=cur_bn["ma_so"], disabled=True)
                        st.text_input("Số CMT (Không đổi)", value=cur_bn["cmt"], disabled=True)
                        e_ten = st.text_input("Họ và tên (*)", value=cur_bn["ho_ten"]).strip()
                    with e_col2:
                        default_ns = cur_bn["ngay_sinh"] if isinstance(cur_bn["ngay_sinh"], datetime.date) else datetime.date(1995, 1, 1)
                        e_ns = st.date_input("Ngày sinh (*)", value=default_ns, min_value=datetime.date(1920, 1, 1), max_value=datetime.date.today())
                        e_sdt = st.text_input("Số điện thoại", value=cur_bn["sdt"] or "").strip()
                        e_dc = st.text_input("Địa chỉ", value=cur_bn["dia_chi"] or "").strip()

                    btn_submit_edit = st.form_submit_button("Lưu thay đổi", type="primary")

                if btn_submit_edit:
                    if not e_ten:
                        st.error("❌ Họ và tên không được để trống!")
                    else:
                        ok_sdt, msg_sdt = validate_sdt(e_sdt, allow_empty=True)
                        if not ok_sdt:
                            st.error(f"❌ {msg_sdt}")
                        else:
                            sql_update = "UPDATE benh_nhan SET ho_ten = %s, ngay_sinh = %s, dia_chi = %s, sdt = %s WHERE ma_bn = %s"
                            ok, _, err_msg = db.execute_statement(sql_update, (e_ten, str(e_ns), e_dc, e_sdt, cur_bn["ma_bn"]))
                            if not ok:
                                st.error(f"❌ {err_msg}")
                            else:
                                st.success(f"✅ Đã cập nhật thông tin bệnh nhân **{e_ten}** thành công!")
                                st.rerun()
            else:
                st.info("Không có dữ liệu bệnh nhân để sửa.")

        # Xóa bệnh nhân
        with tab_del:
            st.subheader("Xóa hồ sơ bệnh nhân")
            if ok_bn and bn_list:
                options_del = {f"{b['ma_so']} - {b['ho_ten']} (CMT: {b['cmt']})": b for b in bn_list}
                sel_del_label = st.selectbox("Chọn bệnh nhân cần xóa:", options=list(options_del.keys()), key="sel_del_bn")
                bn_to_del = options_del[sel_del_label]

                st.warning(f"⚠️ Bạn có chắc chắn muốn xóa bệnh nhân **{bn_to_del['ho_ten']}** ({bn_to_del['ma_so']})?")
                st.write("Lưu ý: Nếu bệnh nhân đã có lịch sử khám bệnh trong hệ thống, dữ liệu sẽ được giữ lại để đảm bảo tính toàn vẹn.")

                if st.button("🗑️ Xác nhận xóa", type="primary"):
                    sql_delete = "DELETE FROM benh_nhan WHERE ma_bn = %s"
                    ok, _, err_msg = db.execute_statement(sql_delete, (bn_to_del["ma_bn"],))
                    if not ok:
                        st.error(f"❌ {err_msg}")
                    else:
                        st.success(f"✅ Đã xóa bệnh nhân **{bn_to_del['ho_ten']}** thành công!")
                        st.rerun()
            else:
                st.info("Không có dữ liệu bệnh nhân để xóa.")

# =====================================================================
# MENU 3: DANH SÁCH
# =====================================================================
elif nav == "Danh sách":
    st.header("📋 Danh Sách")
    tab_bs, tab_yt, tab_bn, tab_thuoc, tab_benh = st.tabs([
        "👨‍⚕️ Bác sỹ", "👩‍⚕️ Y tá", "👥 Bệnh nhân", "💊 Thuốc", "🦠 Bệnh"
    ])

    # ---- Tab Bác sỹ ----
    with tab_bs:
        st.subheader("📋 Danh Sách Bác Sỹ Hiện Tại")
        ok_bs_all, all_bs, _ = db.execute_query("""
            SELECT nv.ma_so, nv.cmt, nv.ho_ten, nv.ngay_sinh, nv.sdt, nv.tham_nien,
                   bs.bac_nghe, bs.trinh_do_dao_tao, bs.chuyen_mon
            FROM bac_sy bs
            JOIN nhan_vien nv ON nv.ma_nv = bs.ma_nv
            ORDER BY nv.ma_so
        """)
        if ok_bs_all and all_bs:
            df_all_bs = pd.DataFrame(all_bs)
            df_all_bs.columns = ["Mã BS", "Số CMT", "Họ Tên", "Ngày Sinh", "Số ĐT", "Thâm Niên (Năm)", "Bậc Nghề", "Trình Độ", "Chuyên Môn"]
            st.dataframe(df_all_bs, use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có bác sỹ nào trong hệ thống.")

        st.markdown("---")
        st.subheader("➕ Thêm Bác Sỹ Mới")
        with st.form("form_add_bs", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                bs_ma_so = st.text_input("Mã số BS (*):", placeholder="Ví dụ: BS004").strip()
                bs_cmt = st.text_input("Số CMT/CCCD (*):", placeholder="12 chữ số").strip()
                bs_ten = st.text_input("Họ và tên Bác sỹ (*):", placeholder="Ví dụ: Hoàng Quốc Huy").strip()
                bs_ns = st.date_input("Ngày sinh (*):", value=datetime.date(1985, 5, 20), min_value=datetime.date(1940, 1, 1), max_value=datetime.date.today())
                bs_tham_nien = st.number_input("Thâm niên (năm):", min_value=0, max_value=60, value=5)
            with c2:
                bs_sdt = st.text_input("Số điện thoại:", placeholder="0901xxxxxx").strip()
                bs_dc = st.text_input("Địa chỉ:", placeholder="Hà Nội...").strip()
                bs_bac_nghe = st.selectbox("Bậc nghề (*):", options=["Bác sỹ chuyên khoa I", "Bác sỹ chuyên khoa II", "Bác sỹ đa khoa", "Bác sỹ nội trú"])
                bs_trinh_do = st.selectbox("Trình độ đào tạo (*):", options=["Tiến sỹ", "Thạc sỹ", "Bác sỹ"])
                bs_chuyen_mon = st.text_input("Chuyên môn (*):", placeholder="Ví dụ: Tai Mũi Họng, Răng Hàm Mặt, Mắt...").strip()

            btn_submit_bs = st.form_submit_button("Lưu Bác sỹ", type="primary")

        if btn_submit_bs:
            if not bs_ma_so or not bs_cmt or not bs_ten or not bs_chuyen_mon:
                st.error("❌ Vui lòng nhập đầy đủ các thông tin bắt buộc (*): Mã số, CMT, Họ tên, Chuyên môn!")
            else:
                ok_cmt, msg_cmt = validate_cmt(bs_cmt)
                if not ok_cmt:
                    st.error(f"❌ {msg_cmt}")
                else:
                    ok_sdt, msg_sdt = validate_sdt(bs_sdt, allow_empty=True)
                    if not ok_sdt:
                        st.error(f"❌ {msg_sdt}")
                    else:
                        ok_bs, new_bs_id, err_msg = db.add_doctor(
                            bs_ma_so, bs_cmt, bs_ten, str(bs_ns), bs_dc, bs_sdt, bs_tham_nien,
                            bs_bac_nghe, bs_trinh_do, bs_chuyen_mon
                        )
                        if not ok_bs:
                            st.error(f"❌ {err_msg}")
                        else:
                            st.success(f"🎉 Đã thêm Bác sỹ **{bs_ten}** ({bs_ma_so}) thành công!")
                            st.rerun()

    # ---- Tab Y tá ----
    with tab_yt:
        st.subheader("📋 Danh Sách Y Tá Hiện Tại")
        ok_yt_all, all_yt, _ = db.execute_query("""
            SELECT nv.ma_so, nv.cmt, nv.ho_ten, nv.ngay_sinh, nv.sdt, nv.tham_nien, yt.trinh_do
            FROM y_ta yt
            JOIN nhan_vien nv ON nv.ma_nv = yt.ma_nv
            ORDER BY nv.ma_so
        """)
        if ok_yt_all and all_yt:
            df_all_yt = pd.DataFrame(all_yt)
            df_all_yt.columns = ["Mã YT", "Số CMT", "Họ Tên", "Ngày Sinh", "Số ĐT", "Thâm Niên (Năm)", "Trình Độ Đào Tạo"]
            st.dataframe(df_all_yt, use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có y tá nào trong hệ thống.")

        st.markdown("---")
        st.subheader("➕ Thêm Y Tá Mới")
        with st.form("form_add_yt", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                yt_ma_so = st.text_input("Mã số Y tá (*):", placeholder="Ví dụ: YT005").strip()
                yt_cmt = st.text_input("Số CMT/CCCD (*):", placeholder="12 chữ số").strip()
                yt_ten = st.text_input("Họ và tên Y tá (*):", placeholder="Ví dụ: Lê Thị Hoa").strip()
                yt_ns = st.date_input("Ngày sinh (*):", value=datetime.date(1996, 8, 15), min_value=datetime.date(1940, 1, 1), max_value=datetime.date.today(), key="ns_yt")
            with c2:
                yt_sdt = st.text_input("Số điện thoại:", placeholder="0912xxxxxx", key="sdt_yt").strip()
                yt_dc = st.text_input("Địa chỉ:", placeholder="Hà Nội...", key="dc_yt").strip()
                yt_tham_nien = st.number_input("Thâm niên (năm):", min_value=0, max_value=60, value=2, key="tn_yt")
                yt_trinh_do = st.selectbox("Trình độ đào tạo (*):", options=["Đại học Điều dưỡng", "Cao đẳng Điều dưỡng", "Trung cấp Y tế"])

            btn_submit_yt = st.form_submit_button("Lưu Y tá", type="primary")

        if btn_submit_yt:
            if not yt_ma_so or not yt_cmt or not yt_ten:
                st.error("❌ Vui lòng nhập đầy đủ các thông tin bắt buộc (*): Mã số, CMT, Họ tên!")
            else:
                ok_cmt, msg_cmt = validate_cmt(yt_cmt)
                if not ok_cmt:
                    st.error(f"❌ {msg_cmt}")
                else:
                    ok_sdt, msg_sdt = validate_sdt(yt_sdt, allow_empty=True)
                    if not ok_sdt:
                        st.error(f"❌ {msg_sdt}")
                    else:
                        ok_yt, new_yt_id, err_msg = db.add_nurse(
                            yt_ma_so, yt_cmt, yt_ten, str(yt_ns), yt_dc, yt_sdt, yt_tham_nien, yt_trinh_do
                        )
                        if not ok_yt:
                            st.error(f"❌ {err_msg}")
                        else:
                            st.success(f"🎉 Đã thêm Y tá **{yt_ten}** ({yt_ma_so}) thành công!")
                            st.rerun()

    # ---- Tab Bệnh nhân ----
    with tab_bn:
        st.subheader("👥 Danh Sách Bệnh Nhân")
        keyword_ds = st.text_input("🔍 Tìm kiếm theo tên, mã số hoặc CMT/CCCD:", value="", key="ds_bn_kw")
        if keyword_ds.strip():
            kw_ds = f"%{keyword_ds.strip()}%"
            ok_ds_bn, ds_bn_list, _ = db.execute_query(
                "SELECT ma_bn, ma_so, cmt, ho_ten, ngay_sinh, dia_chi, sdt FROM benh_nhan WHERE ho_ten LIKE %s OR ma_so LIKE %s OR cmt LIKE %s ORDER BY ma_bn DESC",
                (kw_ds, kw_ds, kw_ds)
            )
        else:
            ok_ds_bn, ds_bn_list, _ = db.execute_query(
                "SELECT ma_bn, ma_so, cmt, ho_ten, ngay_sinh, dia_chi, sdt FROM benh_nhan ORDER BY ma_bn DESC"
            )
        if ok_ds_bn and ds_bn_list:
            df_ds_bn = pd.DataFrame(ds_bn_list)
            df_ds_bn.columns = ["Mã BN", "Mã Số", "Số CMT/CCCD", "Họ Tên", "Ngày Sinh", "Địa Chỉ", "Số Điện Thoại"]
            st.dataframe(df_ds_bn, use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có bệnh nhân nào hoặc không tìm thấy kết quả phù hợp.")

    # ---- Tab Thuốc ----
    with tab_thuoc:
        st.subheader("💊 Danh Mục Thuốc Hiện Tại")
        ok_t, thuoc_list, _ = db.execute_query("SELECT ma_thuoc, ten_thuoc, don_vi, don_gia FROM thuoc ORDER BY ma_thuoc")
        if ok_t and thuoc_list:
            df_t = pd.DataFrame(thuoc_list)
            df_t["don_gia_fmt"] = df_t["don_gia"].apply(fmt_vnd)
            disp_t = df_t[["ma_thuoc", "ten_thuoc", "don_vi", "don_gia_fmt"]].copy()
            disp_t.columns = ["Mã Thuốc", "Tên Thuốc", "Đơn Vị Tính", "Đơn Giá Hiện Tại"]
            st.dataframe(disp_t, use_container_width=True, hide_index=True)

        st.markdown("---")
        col_t1, col_t2 = st.columns(2)

        with col_t1:
            st.subheader("➕ Thêm thuốc mới")
            with st.form("form_add_thuoc", clear_on_submit=True):
                new_ten_thuoc = st.text_input("Tên thuốc (*):", placeholder="Ví dụ: Cefixim 200mg").strip()
                new_don_vi = st.text_input("Đơn vị tính (*):", placeholder="viên, chai, vỉ, gói...").strip()
                new_don_gia = st.number_input("Đơn giá (VNĐ) (*):", min_value=0, value=5000, step=1000)
                btn_add_thuoc = st.form_submit_button("Lưu thuốc mới", type="primary")

            if btn_add_thuoc:
                if not new_ten_thuoc or not new_don_vi:
                    st.error("❌ Tên thuốc và đơn vị tính không được để trống!")
                else:
                    sql_add_t = "INSERT INTO thuoc (ten_thuoc, don_vi, don_gia) VALUES (%s, %s, %s)"
                    ok_t_ins, _, err_msg = db.execute_statement(sql_add_t, (new_ten_thuoc, new_don_vi, new_don_gia))
                    if not ok_t_ins:
                        st.error(f"❌ {err_msg}")
                    else:
                        st.success(f"✅ Đã thêm thuốc **{new_ten_thuoc}** vào danh mục thành công!")
                        st.rerun()

        with col_t2:
            st.subheader("✏️ Điều chỉnh giá thuốc")
            if ok_t and thuoc_list:
                dict_up_t = {f"{t['ten_thuoc']} ({t['don_vi']}) - Hiện tại: {fmt_vnd(t['don_gia'])}": t for t in thuoc_list}
                sel_up_key = st.selectbox("Chọn thuốc cần đổi giá:", options=list(dict_up_t.keys()))
                t_to_update = dict_up_t[sel_up_key]

                with st.form("form_update_gia_thuoc"):
                    cur_price = int(t_to_update["don_gia"])
                    updated_price = st.number_input("Nhập đơn giá mới (VNĐ) (*):", min_value=0, value=cur_price, step=1000)
                    btn_up_price = st.form_submit_button("Cập nhật đơn giá", type="primary")

                if btn_up_price:
                    sql_up_p = "UPDATE thuoc SET don_gia = %s WHERE ma_thuoc = %s"
                    ok_up, _, err_msg = db.execute_statement(sql_up_p, (updated_price, t_to_update["ma_thuoc"]))
                    if not ok_up:
                        st.error(f"❌ {err_msg}")
                    else:
                        st.success(f"✅ Đã cập nhật giá thuốc **{t_to_update['ten_thuoc']}** thành {fmt_vnd(updated_price)}!")
                        st.rerun()

    # ---- Tab Bệnh ----
    with tab_benh:
        st.subheader("🦠 Danh Mục Các Loại Bệnh")
        ok_b, benh_list, _ = db.execute_query("SELECT ma_benh, ten_benh FROM benh ORDER BY ma_benh")
        if ok_b and benh_list:
            df_b = pd.DataFrame(benh_list)
            df_b.columns = ["Mã Bệnh", "Tên Bệnh"]
            st.dataframe(df_b, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("➕ Thêm loại bệnh mới")
        with st.form("form_add_benh", clear_on_submit=True):
            new_ten_benh = st.text_input("Tên bệnh (*):", placeholder="Ví dụ: Viêm xoang, Đau mắt đỏ...").strip()
            btn_add_benh = st.form_submit_button("Lưu bệnh mới", type="primary")

        if btn_add_benh:
            if not new_ten_benh:
                st.error("❌ Tên bệnh không được để trống!")
            else:
                sql_add_b = "INSERT INTO benh (ten_benh) VALUES (%s)"
                ok_b_ins, _, err_msg = db.execute_statement(sql_add_b, (new_ten_benh,))
                if not ok_b_ins:
                    st.error(f"❌ {err_msg}")
                else:
                    st.success(f"✅ Đã thêm bệnh **{new_ten_benh}** vào danh mục thành công!")
                    st.rerun()

# =====================================================================
# MENU 4: BÁO CÁO
# =====================================================================
elif nav == "Báo cáo":
    st.header("📊 Báo Cáo")
    tab_bc1, tab_bc2, tab_bc3, tab_bc4 = st.tabs([
        "📋 Bệnh theo tháng", "💰 Bảng lương", "📈 Doanh thu", "🛡️ Kiểm tra ràng buộc"
    ])

    # ---- Tab 1: Bệnh theo tháng (old menu 1) ----
    with tab_bc1:
        st.subheader("📋 Liệt Kê Các Bệnh Theo Tháng")
        st.markdown("<p class='page-desc'>Danh sách các loại bệnh trong tháng, sắp xếp theo số lượng bệnh nhân mắc giảm dần.</p>", unsafe_allow_html=True)
        st.markdown("Một bệnh nhân khám nhiều lần liên tiếp cho cùng một bệnh chỉ tính là một lần mắc.")
        st.caption("Kết quả tự cập nhật khi bạn đổi lựa chọn.")

        col1, col2 = st.columns(2)
        with col1:
            thang = st.selectbox("Chọn tháng", options=list(range(1, 13)), index=10)
        with col2:
            nam = st.number_input("Chọn năm", min_value=2020, max_value=2030, value=2026)

        success, results, err = db.call_procedure("sp_benh_theo_thang", (thang, nam))

        if not success:
            st.error(f"❌ Không thể lấy dữ liệu: {err}")
        else:
            rows = results[0] if results else []
            if not rows:
                st.info(f"Không có lượt bệnh nhân nào đến khám trong tháng {thang}/{nam}.")
            else:
                df = pd.DataFrame(rows)
                df.columns = ["Mã Bệnh", "Tên Bệnh", "Số Bệnh Nhân Mắc (Đợt)"]

                m1, m2 = st.columns(2)
                with m1:
                    st.metric("Tổng số loại bệnh ghi nhận trong tháng", f"{len(df)} bệnh")
                with m2:
                    top_benh = df.iloc[0]["Tên Bệnh"]
                    top_so = df.iloc[0]["Số Bệnh Nhân Mắc (Đợt)"]
                    st.metric("Bệnh có nhiều bệnh nhân nhất", f"{top_benh} ({top_so} BN)")

                c_table, c_chart = st.columns([1, 1])
                with c_table:
                    st.subheader("Bảng dữ liệu chi tiết")
                    st.dataframe(df, use_container_width=True, hide_index=True)
                with c_chart:
                    st.subheader("Biểu đồ phân bố bệnh nhân")
                    chart_data = df.set_index("Tên Bệnh")["Số Bệnh Nhân Mắc (Đợt)"]
                    st.bar_chart(chart_data)

    # ---- Tab 2: Bảng lương (old menu 2) ----
    with tab_bc2:
        st.subheader("💰 Bảng Lương Bác Sỹ & Y Tá Trong Tháng")
        st.markdown("<p class='page-desc'>Bảng tính chi tiết tiền lương hàng tháng của Bác sỹ và Y tá dựa trên kết quả hoạt động.</p>", unsafe_allow_html=True)
        st.markdown("""
        **Cách tính lương theo đề bài:**
        * **Bác sỹ:** Lương cơ bản **7.000.000 đ** + **1.000.000 đ** cho mỗi đợt bệnh nhân được chữa khỏi trong tháng.
        * **Y tá:** Lương cơ bản **5.000.000 đ** + **200.000 đ** cho mỗi lần khám bệnh mà y tá tham gia hỗ trợ trong tháng.
        """)
        st.caption("Kết quả tự cập nhật khi bạn đổi lựa chọn.")

        col_opt, col_m, col_y = st.columns([2, 1, 1])
        with col_opt:
            is_current_month = st.checkbox("Lấy tháng hiện tại (mặc định)", value=True)
        with col_m:
            thang_input = st.selectbox("Tháng", options=list(range(1, 13)), index=10, disabled=is_current_month)
        with col_y:
            nam_input = st.number_input("Năm", min_value=2020, max_value=2030, value=2026, disabled=is_current_month)

        p_thang = None if is_current_month else thang_input
        p_nam = None if is_current_month else nam_input

        success, results, err = db.call_procedure("sp_tinh_luong", (p_thang, p_nam))

        if not success:
            st.error(f"❌ Lỗi khi tính lương: {err}")
        else:
            rows = results[0] if results else []
            if not rows:
                st.info("Chưa có dữ liệu nhân viên để tính lương.")
            else:
                df = pd.DataFrame(rows)
                total_payroll = df["tong_luong"].sum()
                total_bonus = df["thuong"].sum()
                num_staff = len(df)

                kpi1, kpi2, kpi3 = st.columns(3)
                with kpi1:
                    st.metric("Tổng chi trả lương tháng", fmt_vnd(total_payroll))
                with kpi2:
                    st.metric("Tổng tiền thưởng", fmt_vnd(total_bonus))
                with kpi3:
                    st.metric("Tổng số nhân sự", f"{num_staff} người")

                df_bs = df[df["chuc_vu"] == "Bác sỹ"].copy()
                df_yt = df[df["chuc_vu"] == "Y tá"].copy()

                for d in [df_bs, df_yt]:
                    d["luong_co_ban_fmt"] = d["luong_co_ban"].apply(fmt_vnd)
                    d["thuong_fmt"] = d["thuong"].apply(fmt_vnd)
                    d["tong_luong_fmt"] = d["tong_luong"].apply(fmt_vnd)

                tab_bs_l, tab_yt_l, tab_all = st.tabs(["👨‍⚕️ Bảng Lương Bác Sỹ", "👩‍⚕️ Bảng Lương Y Tá", "📑 Toàn Bộ Nhân Sự"])

                with tab_bs_l:
                    st.write("Bác sỹ được cộng thêm 1.000.000 đ cho mỗi đợt bệnh nhân được chữa khỏi trong tháng.")
                    disp_bs = df_bs[["ma_so", "ho_ten", "luong_co_ban_fmt", "so_luot_tinh_thuong", "thuong_fmt", "tong_luong_fmt"]]
                    disp_bs.columns = ["Mã BS", "Họ Tên", "Lương Cơ Bản", "Số Đợt Chữa Khỏi", "Tiền Thưởng", "Tổng Lương"]
                    st.dataframe(disp_bs, use_container_width=True, hide_index=True)

                with tab_yt_l:
                    st.write("Y tá được cộng thêm 200.000 đ cho mỗi lần khám bệnh tham gia hỗ trợ trong tháng.")
                    disp_yt = df_yt[["ma_so", "ho_ten", "luong_co_ban_fmt", "so_luot_tinh_thuong", "thuong_fmt", "tong_luong_fmt"]]
                    disp_yt.columns = ["Mã YT", "Họ Tên", "Lương Cơ Bản", "Số Lần Khám Hỗ Trợ", "Tiền Thưởng", "Tổng Lương"]
                    st.dataframe(disp_yt, use_container_width=True, hide_index=True)

                with tab_all:
                    disp_all = df.copy()
                    disp_all["luong_co_ban"] = disp_all["luong_co_ban"].apply(fmt_vnd)
                    disp_all["thuong"] = disp_all["thuong"].apply(fmt_vnd)
                    disp_all["tong_luong"] = disp_all["tong_luong"].apply(fmt_vnd)
                    disp_all.columns = ["Mã Số", "Họ Tên", "Chức Vụ", "Lương Cơ Bản", "Số Lượt Thưởng", "Tiền Thưởng", "Tổng Lương"]
                    st.dataframe(disp_all, use_container_width=True, hide_index=True)

    # ---- Tab 3: Doanh thu (old menu 4) ----
    with tab_bc3:
        st.subheader("📈 Báo Cáo Doanh Thu Phòng Khám")
        st.markdown("<p class='page-desc'>Doanh thu phòng khám bao gồm tiền khám chữa bệnh và tiền bán thuốc trên các đơn thuốc.</p>", unsafe_allow_html=True)

        tab_range, tab_monthly = st.tabs(["📅 Doanh Thu Theo Khoảng Ngày", "📊 Doanh Thu Từng Tháng"])

        with tab_range:
            st.subheader("Doanh thu trong khoảng thời gian")
            st.caption("Kết quả tự cập nhật khi bạn đổi lựa chọn ngày.")
            today = datetime.date.today()
            first_day_of_month = today.replace(day=1)
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                d_from = st.date_input("Từ ngày", value=first_day_of_month)
            with col_d2:
                d_to = st.date_input("Đến ngày", value=today)

            if d_from > d_to:
                st.error("Ngày bắt đầu không được lớn hơn ngày kết thúc!")
            else:
                success, results, err = db.call_procedure("sp_doanh_thu", (str(d_from), str(d_to)))
                if not success:
                    st.error(f"❌ Lỗi: {err}")
                elif results and results[0]:
                    data = results[0][0]
                    luot_kham = data.get("so_luot_kham", 0)
                    dt_kham = data.get("doanh_thu_kham", 0)
                    dt_thuoc = data.get("doanh_thu_thuoc", 0)
                    tong_dt = data.get("tong_doanh_thu", 0)

                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Tổng lượt khám", f"{luot_kham} lượt")
                    m2.metric("Doanh thu tiền khám", fmt_vnd(dt_kham))
                    m3.metric("Doanh thu tiền thuốc", fmt_vnd(dt_thuoc))
                    m4.metric("TỔNG DOANH THU", fmt_vnd(tong_dt))

                    if tong_dt > 0:
                        st.write("---")
                        st.write("**Cơ cấu doanh thu:**")
                        df_pie = pd.DataFrame({
                            "Khoản thu": ["Tiền khám chữa", "Tiền thuốc"],
                            "Doanh thu": [float(dt_kham), float(dt_thuoc)]
                        }).set_index("Khoản thu")
                        st.bar_chart(df_pie)

        with tab_monthly:
            st.subheader("Doanh thu tổng hợp theo từng tháng")
            ok, rows, err = db.execute_query("SELECT nam, thang, doanh_thu_kham, doanh_thu_thuoc, tong_doanh_thu FROM v_doanh_thu_theo_thang ORDER BY nam DESC, thang DESC")
            if not ok:
                st.error(f"❌ Lỗi đọc doanh thu: {err}")
            elif not rows:
                st.info("Chưa có dữ liệu doanh thu tháng.")
            else:
                df_m = pd.DataFrame(rows)
                df_m["Tháng/Năm"] = df_m.apply(lambda r: f"Tháng {r['thang']:02d}/{r['nam']}", axis=1)

                disp_m = df_m.copy()
                disp_m["doanh_thu_kham"] = disp_m["doanh_thu_kham"].apply(fmt_vnd)
                disp_m["doanh_thu_thuoc"] = disp_m["doanh_thu_thuoc"].apply(fmt_vnd)
                disp_m["tong_doanh_thu"] = disp_m["tong_doanh_thu"].apply(fmt_vnd)
                disp_m = disp_m[["Tháng/Năm", "doanh_thu_kham", "doanh_thu_thuoc", "tong_doanh_thu"]]
                disp_m.columns = ["Tháng/Năm", "Doanh Thu Khám", "Doanh Thu Thuốc", "Tổng Doanh Thu"]

                st.dataframe(disp_m, use_container_width=True, hide_index=True)

                st.write("**Biểu đồ doanh thu các tháng:**")
                chart_df = df_m.set_index("Tháng/Năm")[["doanh_thu_kham", "doanh_thu_thuoc"]]
                chart_df.columns = ["Tiền Khám", "Tiền Thuốc"]
                st.bar_chart(chart_df)

    # ---- Tab 4: Kiểm tra ràng buộc (old menu 13) ----
    with tab_bc4:
        st.subheader("🛡️ Kiểm Tra Ràng Buộc Dữ Liệu")
        st.markdown("<p class='page-desc'>Kiểm tra và thử nghiệm các quy tắc ràng buộc toàn vẹn của hệ thống quản lý phòng khám.</p>", unsafe_allow_html=True)

        with st.expander("Chi tiết kỹ thuật", expanded=False):
            st.markdown("""
            Hệ thống tự động kiểm tra tính toàn vẹn dữ liệu và các quy tắc nghiệp vụ trong cơ sở dữ liệu.
            Khi có hành vi cập nhật hoặc thêm dữ liệu không hợp lệ, hệ thống sẽ phát hiện và hiển thị thông báo lỗi bằng tiếng Việt rõ ràng cho người dùng.
            """)

        tab_auto, tab_manual = st.tabs(["🚀 Chạy Bộ Kiểm Thử Tự Động", "🧪 Thử Nghiệm Từng Ràng Buộc"])

        with tab_auto:
            st.subheader("Kết quả kiểm thử tự động toàn bộ 8 trường hợp")
            st.write("Bấm nút bên dưới để hệ thống tự động kiểm tra tất cả các quy tắc nghiệp vụ:")
            if st.button("▶️ Chạy toàn bộ 8 bài kiểm thử", type="primary"):
                with st.spinner("Đang thực thi các trường hợp kiểm thử..."):
                    ok, res, err = db.call_procedure("sp_chay_tat_ca_test")
                    if not ok:
                        st.error(f"❌ Không thể chạy kiểm thử: {err}")
                    elif res and res[0]:
                        df_test = pd.DataFrame(res[0])
                        st.success("🎉 Đã thực thi xong toàn bộ các bài kiểm thử!")
                        st.dataframe(df_test, use_container_width=True, hide_index=True)

        with tab_manual:
            st.subheader("Thử nghiệm trực tiếp từng tình huống vi phạm quy tắc")

            with st.expander("Tình huống 1: Bệnh nhân trùng bệnh đang điều trị"):
                st.markdown("""
                **Mô tả:** Bệnh nhân BN001 hiện đang điều trị bệnh **Tăng huyết áp** (đợt 3).
                Thử mở thêm một đợt khám mới cho bệnh nhân này cũng với bệnh Tăng huyết áp.
                """)
                if st.button("Thử thêm đợt trùng bệnh cho BN001"):
                    sql = "INSERT INTO dot_benh (ma_bn, ma_benh, ma_bs, ngay_bat_dau) VALUES (1, 2, 1, '2026-11-06');"
                    ok, affected, err_msg = db.execute_statement(sql)
                    if not ok:
                        st.error(f"⛔ **HỆ THỐNG ĐÃ CHẶN THÀNH CÔNG:** {err_msg}")
                    else:
                        st.warning("⚠️ Lệnh đã lọt (chưa bị chặn)!")

            with st.expander("Tình huống 2: Bác sỹ tối đa 30 đợt bệnh đang điều trị"):
                st.markdown("""
                **Mô tả:** Tạo 30 đợt bệnh đang điều trị cho BS003, sau đó thử mở đợt thứ 31 cho bác sỹ này.
                """)
                if st.button("Thử gán đợt thứ 31 cho BS003"):
                    db.call_procedure("sp_test_setup_rb3")
                    sql = "INSERT INTO dot_benh (ma_bn, ma_benh, ma_bs, ngay_bat_dau) VALUES (1, 1, 3, '2026-11-06');"
                    ok, affected, err_msg = db.execute_statement(sql)
                    db.call_procedure("sp_test_cleanup_rb3")
                    if not ok:
                        st.error(f"⛔ **HỆ THỐNG ĐÃ CHẶN THÀNH CÔNG:** {err_msg}")
                    else:
                        st.warning("⚠️ Lệnh đã lọt!")

            with st.expander("Tình huống 3: Mỗi lần khám tối đa 3 y tá hỗ trợ"):
                st.markdown("""
                **Mô tả:** Lần khám 8 đã có đủ 3 y tá tham gia hỗ trợ. Thử phân công thêm y tá thứ 4 vào lần khám này.
                """)
                if st.button("Thử thêm y tá thứ 4 vào lần khám 8"):
                    sql = "INSERT INTO y_ta_ho_tro (ma_lan_kham, ma_yta, vai_tro) VALUES (8, 7, 'Tiếp đón');"
                    ok, affected, err_msg = db.execute_statement(sql)
                    if not ok:
                        st.error(f"⛔ **HỆ THỐNG ĐÃ CHẶN THÀNH CÔNG:** {err_msg}")
                    else:
                        st.warning("⚠️ Lệnh đã lọt!")

            with st.expander("Tình huống 4: Ngày khám nằm ngoài thời gian đợt bệnh"):
                st.markdown("""
                **Mô tả:** Đợt bệnh 6 bắt đầu từ ngày 12/10/2026. Thử thêm lần khám có ngày vào 01/10/2026 (trước ngày bắt đầu đợt).
                """)
                if st.button("Thử thêm lần khám có ngày vào trước đợt bệnh"):
                    sql = "INSERT INTO lan_kham (ma_dot, ngay_vao, phi_kham) VALUES (6, '2026-10-01', 100000);"
                    ok, affected, err_msg = db.execute_statement(sql)
                    if not ok:
                        st.error(f"⛔ **HỆ THỐNG ĐÃ CHẶN THÀNH CÔNG:** {err_msg}")
                    else:
                        st.warning("⚠️ Lệnh đã lọt!")

            with st.expander("Tình huống 5: Sửa phí khám thì tổng tiền tự động tính lại"):
                st.markdown("""
                **Mô tả:** Lần khám 1 ban đầu có phí khám 150.000 đ, tiền thuốc 25.000 đ (Tổng tiền = 175.000 đ).
                Khi tăng phí khám lên 250.000 đ, hệ thống tự động tính lại tổng tiền thành 275.000 đ.
                """)
                col_u1, col_u2 = st.columns(2)
                with col_u1:
                    if st.button("Tăng phí khám lên 250.000 đ"):
                        db.execute_statement("UPDATE lan_kham SET phi_kham = 250000 WHERE ma_lan_kham = 1;")
                        st.success("Đã cập nhật phí khám = 250.000 đ")
                with col_u2:
                    if st.button("Đặt lại phí khám về 150.000 đ"):
                        db.execute_statement("UPDATE lan_kham SET phi_kham = 150000 WHERE ma_lan_kham = 1;")
                        st.info("Đã khôi phục phí khám = 150.000 đ")

                _, lk_rows, _ = db.execute_query("SELECT ma_lan_kham, phi_kham, (tong_tien - phi_kham) as tien_thuoc, tong_tien FROM lan_kham WHERE ma_lan_kham = 1;")
                if lk_rows:
                    r = lk_rows[0]
                    st.write(f"👉 Hiện tại lần khám 1: Phí khám = **{fmt_vnd(r['phi_kham'])}** | Tiền thuốc = **{fmt_vnd(r['tien_thuoc'])}** | Tổng tiền = **{fmt_vnd(r['tong_tien'])}**")

            with st.expander("Tình huống 6: Đóng đợt với ngày kết thúc sớm hơn lần khám cuối"):
                st.markdown("""
                **Mô tả:** Đợt 1 có lần khám cuối vào ngày 14/08/2026.
                Thử đóng đợt với ngày kết thúc là 12/08/2026 (sớm hơn ngày bệnh nhân vào khám).
                """)
                if st.button("Thử đóng đợt 1 với ngày kết thúc 12/08/2026"):
                    sql = "UPDATE dot_benh SET ngay_ket_thuc = '2026-08-12' WHERE ma_dot = 1;"
                    ok, affected, err_msg = db.execute_statement(sql)
                    if not ok:
                        st.error(f"⛔ **HỆ THỐNG ĐÃ CHẶN THÀNH CÔNG:** {err_msg}")
                    else:
                        st.warning("⚠️ Lệnh đã lọt!")

# =====================================================================
# MENU 5: NHẬP DỮ LIỆU
# =====================================================================
elif nav == "Nhập dữ liệu":
    st.header("📝 Nhập Dữ Liệu")
    tab_nd1, tab_nd2, tab_nd3, tab_nd4, tab_nd5 = st.tabs([
        "🏥 Mở đợt bệnh", "🩺 Thêm lần khám", "💊 Kê đơn thuốc",
        "👩‍⚕️ Phân công y tá", "🎉 Ghi nhận chữa khỏi"
    ])

    # ---- Tab 1: Mở đợt bệnh (old menu 6) ----
    with tab_nd1:
        st.subheader("🏥 Mở Đợt Bệnh Mới Cho Bệnh Nhân")
        st.markdown("<p class='page-desc'>Tiếp nhận bệnh nhân đến khám bệnh. Mỗi đợt bệnh được chỉ định một bác sỹ phụ trách.</p>", unsafe_allow_html=True)
        st.caption("Mỗi bệnh nhân chỉ có một đợt đang điều trị cho cùng một bệnh.")

        ok_bn, bn_list, _ = db.execute_query("SELECT ma_bn, ma_so, ho_ten, cmt FROM benh_nhan ORDER BY ma_so")
        ok_b, b_list, _ = db.execute_query("SELECT ma_benh, ten_benh FROM benh ORDER BY ten_benh")
        ok_bs, bs_list, _ = db.execute_query("""
            SELECT bs.ma_nv, nv.ma_so, nv.ho_ten, bs.chuyen_mon, bs.bac_nghe
            FROM bac_sy bs
            JOIN nhan_vien nv ON nv.ma_nv = bs.ma_nv
            ORDER BY nv.ma_so
        """)

        with st.form("form_mo_dot"):
            c1, c2 = st.columns(2)
            with c1:
                dict_bn = {f"{b['ma_so']} - {b['ho_ten']} (CMT: {b['cmt']})": b["ma_bn"] for b in (bn_list or [])}
                sel_bn = st.selectbox("1. Chọn Bệnh nhân (*):", options=list(dict_bn.keys())) if dict_bn else None

                dict_b = {f"{b['ten_benh']}": b["ma_benh"] for b in (b_list or [])}
                sel_b = st.selectbox("2. Chọn Bệnh mắc phải (*):", options=list(dict_b.keys())) if dict_b else None

            with c2:
                dict_bs = {f"{b['ma_so']} - BS. {b['ho_ten']} ({b['chuyen_mon']})": b["ma_nv"] for b in (bs_list or [])}
                sel_bs = st.selectbox("3. Chỉ định Bác sỹ phụ trách (*):", options=list(dict_bs.keys())) if dict_bs else None

                ngay_bd = st.date_input("4. Ngày bắt đầu khám/điều trị (*):", value=datetime.date.today())

            btn_mo_dot = st.form_submit_button("🚀 Mở đợt bệnh mới", type="primary")

        if btn_mo_dot:
            if not sel_bn or not sel_b or not sel_bs:
                st.error("❌ Vui lòng chọn đầy đủ Bệnh nhân, Bệnh và Bác sỹ!")
            else:
                p_ma_bn = dict_bn[sel_bn]
                p_ma_benh = dict_b[sel_b]
                p_ma_bs = dict_bs[sel_bs]

                sql_insert_dot = "INSERT INTO dot_benh (ma_bn, ma_benh, ma_bs, ngay_bat_dau, ngay_ket_thuc) VALUES (%s, %s, %s, %s, NULL)"
                ok, new_id, err_msg = db.execute_insert(sql_insert_dot, (p_ma_bn, p_ma_benh, p_ma_bs, str(ngay_bd)))

                if not ok:
                    st.error(f"❌ {err_msg}")
                else:
                    st.success(f"🎉 Mở đợt bệnh mới thành công! (Mã đợt: `{new_id}`). Hãy tiếp tục thêm lần khám đầu tiên cho bệnh nhân.")
                    st.rerun()

        st.markdown("---")
        st.subheader("📋 Danh Sách Các Đợt Bệnh Đang Điều Trị Hiện Tại")
        ok_cur, cur_dots, _ = db.execute_query("""
            SELECT d.ma_dot, bn.ma_so AS ma_bn, bn.ho_ten AS ten_bn, b.ten_benh,
                   nv.ho_ten AS ten_bs, d.ngay_bat_dau,
                   (SELECT COUNT(*) FROM lan_kham WHERE ma_dot = d.ma_dot) AS so_lan_da_kham
            FROM dot_benh d
            JOIN benh_nhan bn ON bn.ma_bn = d.ma_bn
            JOIN benh b ON b.ma_benh = d.ma_benh
            JOIN nhan_vien nv ON nv.ma_nv = d.ma_bs
            WHERE d.ngay_ket_thuc IS NULL
            ORDER BY d.ma_dot DESC
        """)
        if ok_cur and cur_dots:
            df_cur = pd.DataFrame(cur_dots)
            df_cur.columns = ["Mã Đợt", "Mã BN", "Tên Bệnh Nhân", "Bệnh Đang Điều Trị", "Bác Sỹ Phụ Trách", "Ngày Bắt Đầu", "Số Lần Đã Khám"]
            st.dataframe(df_cur, use_container_width=True, hide_index=True)
        else:
            st.info("Hiện không có đợt bệnh nào đang điều trị.")

    # ---- Tab 2: Thêm lần khám (old menu 7) ----
    with tab_nd2:
        st.subheader("🩺 Thêm Lần Khám Cho Đợt Bệnh")
        st.markdown("<p class='page-desc'>Ghi nhận một lần đến khám/chữa bệnh của bệnh nhân trong đợt điều trị.</p>", unsafe_allow_html=True)
        st.caption("Ngày vào khám phải nằm trong khoảng thời gian điều trị của đợt bệnh.")

        ok_dot, dot_active, _ = db.execute_query("""
            SELECT d.ma_dot, d.ngay_bat_dau, bn.ma_so, bn.ho_ten AS ten_bn, b.ten_benh, nv.ho_ten AS ten_bs
            FROM dot_benh d
            JOIN benh_nhan bn ON bn.ma_bn = d.ma_bn
            JOIN benh b ON b.ma_benh = d.ma_benh
            JOIN nhan_vien nv ON nv.ma_nv = d.ma_bs
            WHERE d.ngay_ket_thuc IS NULL
            ORDER BY d.ma_dot DESC
        """)

        if not dot_active:
            st.warning("⚠️ Hiện tại không có đợt bệnh nào đang điều trị. Vui lòng mở đợt bệnh mới trước.")
        else:
            dict_dot = {
                f"Đợt {d['ma_dot']}: {d['ten_bn']} ({d['ma_so']}) - Bệnh: {d['ten_benh']} | Bắt đầu: {d['ngay_bat_dau']}": d
                for d in dot_active
            }

            with st.form("form_add_lan_kham"):
                sel_dot_key = st.selectbox("1. Chọn Đợt bệnh đang điều trị (*):", options=list(dict_dot.keys()))
                dot_info = dict_dot[sel_dot_key]

                st.write(f"Đợt bệnh bắt đầu từ ngày **{dot_info['ngay_bat_dau']}**, do BS. **{dot_info['ten_bs']}** phụ trách.")

                c1, c2, c3 = st.columns(3)
                with c1:
                    ngay_vao = st.date_input("2. Ngày vào khám (*):", value=datetime.date.today())
                with c2:
                    co_ngay_ra = st.checkbox("Có ngày ra viện ngay?")
                    ngay_ra = st.date_input("Ngày ra viện:", value=datetime.date.today()) if co_ngay_ra else None
                with c3:
                    phi_kham = st.number_input("3. Phí khám/chữa bệnh (VNĐ) (*):", min_value=0, value=150000, step=10000)

                btn_submit_lk = st.form_submit_button("Thêm lần khám", type="primary")

            if btn_submit_lk:
                p_ma_dot = dot_info["ma_dot"]
                p_ngay_ra = str(ngay_ra) if co_ngay_ra and ngay_ra else None

                sql_lk = "INSERT INTO lan_kham (ma_dot, ngay_vao, ngay_ra, phi_kham) VALUES (%s, %s, %s, %s)"
                ok, new_lk_id, err_msg = db.execute_insert(sql_lk, (p_ma_dot, str(ngay_vao), p_ngay_ra, phi_kham))

                if not ok:
                    st.error(f"❌ {err_msg}")
                else:
                    st.success(f"✅ Thêm lần khám thành công! (Mã lần khám: `{new_lk_id}`). Số lần khám và tổng tiền ban đầu đã được ghi nhận.")
                    st.rerun()

        st.markdown("---")
        st.subheader("📋 Lịch Sử Các Lần Khám Gần Đây")
        ok_lks, lk_list, _ = db.execute_query("""
            SELECT lk.ma_lan_kham, lk.ma_dot, bn.ho_ten AS ten_bn, b.ten_benh,
                   lk.so_lan AS lan_thu, lk.ngay_vao, lk.ngay_ra, lk.phi_kham, lk.tong_tien
            FROM lan_kham lk
            JOIN dot_benh d ON d.ma_dot = lk.ma_dot
            JOIN benh_nhan bn ON bn.ma_bn = d.ma_bn
            JOIN benh b ON b.ma_benh = d.ma_benh
            ORDER BY lk.ma_lan_kham DESC
            LIMIT 10
        """)
        if ok_lks and lk_list:
            df_lks = pd.DataFrame(lk_list)
            df_lks["phi_kham"] = df_lks["phi_kham"].apply(fmt_vnd)
            df_lks["tong_tien"] = df_lks["tong_tien"].apply(fmt_vnd)
            df_lks.columns = ["Mã LK", "Mã Đợt", "Bệnh Nhân", "Bệnh", "Lần Khám Thứ", "Ngày Vào", "Ngày Ra", "Phí Khám", "Tổng Tiền (Kèm thuốc)"]
            st.dataframe(df_lks, use_container_width=True, hide_index=True)

    # ---- Tab 3: Kê đơn thuốc (old menu 8) ----
    with tab_nd3:
        st.subheader("💊 Kê Đơn Thuốc Cho Lần Khám")
        st.markdown("<p class='page-desc'>Thêm các loại thuốc được kê đơn cho bệnh nhân trong một lần khám.</p>", unsafe_allow_html=True)
        st.caption("Đơn giá thuốc và tổng tiền viện phí sẽ tự động được cập nhật khi kê đơn.")

        ok_lks, lk_list, _ = db.execute_query("""
            SELECT lk.ma_lan_kham, lk.ma_dot, lk.so_lan, lk.ngay_vao, lk.phi_kham, lk.tong_tien,
                   bn.ho_ten AS ten_bn, bn.ma_so AS ma_bn, b.ten_benh
            FROM lan_kham lk
            JOIN dot_benh d ON d.ma_dot = lk.ma_dot
            JOIN benh_nhan bn ON bn.ma_bn = d.ma_bn
            JOIN benh b ON b.ma_benh = d.ma_benh
            ORDER BY lk.ma_lan_kham DESC
        """)

        ok_t, thuoc_list, _ = db.execute_query("SELECT ma_thuoc, ten_thuoc, don_vi, don_gia FROM thuoc ORDER BY ten_thuoc")

        if not ok_lks or not lk_list:
            st.warning("Chưa có lần khám nào trong hệ thống. Vui lòng thêm lần khám trước.")
        else:
            dict_lk = {
                f"LK {lk['ma_lan_kham']} (Lần {lk['so_lan']} - {lk['ngay_vao']}): {lk['ten_bn']} ({lk['ten_benh']}) | Tổng tiền: {fmt_vnd(lk['tong_tien'])}": lk
                for lk in lk_list
            }
            sel_lk_key = st.selectbox("1. Chọn Lần khám cần kê đơn:", options=list(dict_lk.keys()))
            selected_lk = dict_lk[sel_lk_key]
            ma_lk = selected_lk["ma_lan_kham"]

            st.markdown("---")
            c_form, c_cur = st.columns([1, 1])

            with c_form:
                st.subheader("➕ Kê thêm thuốc vào đơn")
                dict_t = {
                    f"{t['ten_thuoc']} ({t['don_vi']}) - Đơn giá: {fmt_vnd(t['don_gia'])}": t
                    for t in (thuoc_list or [])
                }
                with st.form("form_ke_thuoc", clear_on_submit=True):
                    sel_t_key = st.selectbox("Chọn loại thuốc (*):", options=list(dict_t.keys())) if dict_t else None
                    so_luong = st.number_input("Số lượng kê đơn (*):", min_value=1, value=10, step=1)
                    btn_ke = st.form_submit_button("Kê thuốc vào đơn", type="primary")

                if btn_ke and sel_t_key:
                    t_obj = dict_t[sel_t_key]
                    p_ma_thuoc = t_obj["ma_thuoc"]

                    sql_ke = "INSERT INTO ke_don (ma_lan_kham, ma_thuoc, so_luong) VALUES (%s, %s, %s)"
                    ok_ins, _, err_msg = db.execute_statement(sql_ke, (ma_lk, p_ma_thuoc, so_luong))

                    if not ok_ins:
                        st.error(f"❌ {err_msg}")
                    else:
                        st.success(f"✅ Đã kê **{so_luong} {t_obj['don_vi']} {t_obj['ten_thuoc']}**! Tổng tiền lần khám đã được cập nhật.")
                        st.rerun()

            with c_cur:
                st.subheader(f"📋 Các thuốc đã kê cho lần khám #{ma_lk}")
                ok_kd, don_thuoc, _ = db.execute_query("""
                    SELECT t.ten_thuoc, t.don_vi, kd.don_gia, kd.so_luong, (kd.so_luong * kd.don_gia) AS thanh_tien
                    FROM ke_don kd
                    JOIN thuoc t ON t.ma_thuoc = kd.ma_thuoc
                    WHERE kd.ma_lan_kham = %s
                """, (ma_lk,))

                _, lk_now, _ = db.execute_query("SELECT phi_kham, tong_tien FROM lan_kham WHERE ma_lan_kham = %s", (ma_lk,))
                phi_kham_val = lk_now[0]["phi_kham"] if lk_now else 0
                tong_tien_val = lk_now[0]["tong_tien"] if lk_now else 0

                if not don_thuoc:
                    st.info("Lần khám này chưa được kê loại thuốc nào.")
                else:
                    df_kd = pd.DataFrame(don_thuoc)
                    tong_tien_thuoc = df_kd["thanh_tien"].sum()
                    df_kd["don_gia"] = df_kd["don_gia"].apply(fmt_vnd)
                    df_kd["thanh_tien"] = df_kd["thanh_tien"].apply(fmt_vnd)
                    df_kd.columns = ["Tên Thuốc", "Đơn Vị", "Đơn Giá", "Số Lượng", "Thành Tiền"]
                    st.dataframe(df_kd, use_container_width=True, hide_index=True)

                    st.write(f"🔹 **Phí khám:** `{fmt_vnd(phi_kham_val)}`")
                    st.write(f"🔹 **Tiền thuốc:** `{fmt_vnd(tong_tien_thuoc)}`")
                    st.markdown(f"### 👉 **Tổng Tiền Viện Phí:** `{fmt_vnd(tong_tien_val)}`")

    # ---- Tab 4: Phân công y tá (old menu 9) ----
    with tab_nd4:
        st.subheader("👩‍⚕️ Phân Công Y Tá Hỗ Trợ Cho Lần Khám")
        st.markdown("<p class='page-desc'>Phân công các y tá hỗ trợ bệnh nhân trong một lần khám (tiếp đón, cấp thuốc, tiêm thuốc, theo dõi).</p>", unsafe_allow_html=True)
        st.caption("Mỗi lần khám có tối đa 3 y tá tham gia hỗ trợ.")

        ok_lks, lk_list, _ = db.execute_query("""
            SELECT lk.ma_lan_kham, lk.ma_dot, lk.so_lan, lk.ngay_vao,
                   bn.ho_ten AS ten_bn, b.ten_benh
            FROM lan_kham lk
            JOIN dot_benh d ON d.ma_dot = lk.ma_dot
            JOIN benh_nhan bn ON bn.ma_bn = d.ma_bn
            JOIN benh b ON b.ma_benh = d.ma_benh
            ORDER BY lk.ma_lan_kham DESC
        """)

        ok_yt, yt_list, _ = db.execute_query("""
            SELECT yt.ma_nv, nv.ma_so, nv.ho_ten, yt.trinh_do
            FROM y_ta yt
            JOIN nhan_vien nv ON nv.ma_nv = yt.ma_nv
            ORDER BY nv.ma_so
        """)

        if not ok_lks or not lk_list:
            st.warning("Chưa có lần khám nào trong hệ thống. Vui lòng thêm lần khám trước.")
        else:
            dict_lk = {
                f"Lần khám #{lk['ma_lan_kham']} (Lần {lk['so_lan']} - {lk['ngay_vao']}): {lk['ten_bn']} ({lk['ten_benh']})": lk
                for lk in lk_list
            }
            sel_lk_key = st.selectbox("1. Chọn Lần khám cần phân công:", options=list(dict_lk.keys()))
            selected_lk = dict_lk[sel_lk_key]
            ma_lk = selected_lk["ma_lan_kham"]

            st.markdown("---")
            col_assign, col_view = st.columns([1, 1])

            with col_assign:
                st.subheader("➕ Phân công thêm y tá")
                dict_yt = {
                    f"{y['ma_so']} - {y['ho_ten']} ({y['trinh_do']})": y["ma_nv"]
                    for y in (yt_list or [])
                }
                with st.form("form_assign_yt"):
                    sel_yt_key = st.selectbox("Chọn y tá (*):", options=list(dict_yt.keys())) if dict_yt else None
                    vai_tro = st.selectbox(
                        "Chọn vai trò hỗ trợ (*):",
                        options=["Tiếp đón", "Cấp thuốc", "Tiêm thuốc", "Chăm sóc theo dõi"]
                    )
                    btn_assign = st.form_submit_button("Phân công y tá", type="primary")

                if btn_assign and sel_yt_key:
                    p_ma_yta = dict_yt[sel_yt_key]
                    sql_assign = "INSERT INTO y_ta_ho_tro (ma_lan_kham, ma_yta, vai_tro) VALUES (%s, %s, %s)"
                    ok_as, _, err_msg = db.execute_statement(sql_assign, (ma_lk, p_ma_yta, vai_tro))

                    if not ok_as:
                        st.error(f"❌ {err_msg}")
                    else:
                        st.success(f"✅ Phân công y tá thành công với vai trò **{vai_tro}**!")
                        st.rerun()

            with col_view:
                st.subheader(f"👥 Danh sách y tá hỗ trợ lần khám #{ma_lk}")
                ok_cur_yt, cur_yts, _ = db.execute_query("""
                    SELECT nv.ma_so, nv.ho_ten, yt.trinh_do, h.vai_tro
                    FROM y_ta_ho_tro h
                    JOIN y_ta yt ON yt.ma_nv = h.ma_yta
                    JOIN nhan_vien nv ON nv.ma_nv = yt.ma_nv
                    WHERE h.ma_lan_kham = %s
                """, (ma_lk,))

                if not cur_yts:
                    st.info("Lần khám này chưa có y tá nào được phân công.")
                else:
                    df_cur_yt = pd.DataFrame(cur_yts)
                    df_cur_yt.columns = ["Mã Số", "Họ Tên Y Tá", "Trình Độ", "Vai Trò"]
                    st.dataframe(df_cur_yt, use_container_width=True, hide_index=True)

                    distinct_cnt = len(set(r["ma_so"] for r in cur_yts))
                    st.write(f"Lần khám này hiện có **{distinct_cnt}/3** y tá khác nhau tham gia hỗ trợ.")

    # ---- Tab 5: Ghi nhận chữa khỏi (old menu 10) ----
    with tab_nd5:
        st.subheader("🎉 Ghi Nhận Chữa Khỏi (Đóng Đợt Bệnh)")
        st.markdown("<p class='page-desc'>Ghi nhận ngày chữa khỏi bệnh và kết thúc đợt điều trị của bệnh nhân.</p>", unsafe_allow_html=True)
        st.caption("Ngày kết thúc đợt bệnh không được sớm hơn ngày vào của lần khám cuối cùng.")

        ok_dot, dot_active, _ = db.execute_query("""
            SELECT d.ma_dot, d.ngay_bat_dau, bn.ma_so, bn.ho_ten AS ten_bn, b.ten_benh, nv.ho_ten AS ten_bs,
                   (SELECT MAX(ngay_vao) FROM lan_kham WHERE ma_dot = d.ma_dot) AS ngay_kham_cuoi,
                   (SELECT COUNT(*) FROM lan_kham WHERE ma_dot = d.ma_dot) AS tong_so_lan_kham
            FROM dot_benh d
            JOIN benh_nhan bn ON bn.ma_bn = d.ma_bn
            JOIN benh b ON b.ma_benh = d.ma_benh
            JOIN nhan_vien nv ON nv.ma_nv = d.ma_bs
            WHERE d.ngay_ket_thuc IS NULL
            ORDER BY d.ma_dot DESC
        """)

        if not dot_active:
            st.success("✅ Tuyệt vời! Hiện tại không còn đợt bệnh nào đang điều trị (tất cả các đợt đều đã chữa khỏi).")
        else:
            dict_dot = {
                f"Đợt #{d['ma_dot']}: {d['ten_bn']} - Bệnh: {d['ten_benh']} | BS: {d['ten_bs']} (Bắt đầu: {d['ngay_bat_dau']})": d
                for d in dot_active
            }
            sel_dot_key = st.selectbox("1. Chọn Đợt bệnh cần ghi nhận chữa khỏi (*):", options=list(dict_dot.keys()))
            selected_dot = dict_dot[sel_dot_key]

            c_info1, c_info2 = st.columns(2)
            with c_info1:
                st.write(f"👤 **Bệnh nhân:** {selected_dot['ten_bn']} ({selected_dot['ma_so']})")
                st.write(f"🩺 **Bệnh:** **{selected_dot['ten_benh']}**")
                st.write(f"👨‍⚕️ **Bác sỹ điều trị:** {selected_dot['ten_bs']}")
            with c_info2:
                st.write(f"📅 **Ngày bắt đầu đợt:** `{selected_dot['ngay_bat_dau']}`")
                st.write(f"🏥 **Lần khám cuối cùng vào ngày:** `{selected_dot['ngay_kham_cuoi'] or 'Chưa có lần khám nào'}`")
                st.write(f"🔢 **Tổng số lần đã khám:** {selected_dot['tong_so_lan_kham']} lần")

            with st.form("form_dong_dot"):
                def_end_date = selected_dot["ngay_kham_cuoi"] if selected_dot["ngay_kham_cuoi"] else datetime.date.today()
                ngay_kt = st.date_input("2. Chọn Ngày kết thúc / Ngày chữa khỏi (*):", value=def_end_date)
                btn_dong = st.form_submit_button("Xác nhận đã chữa khỏi bệnh", type="primary")

            if btn_dong:
                sql_close = "UPDATE dot_benh SET ngay_ket_thuc = %s WHERE ma_dot = %s"
                ok_cl, _, err_msg = db.execute_statement(sql_close, (str(ngay_kt), selected_dot["ma_dot"]))

                if not ok_cl:
                    st.error(f"❌ {err_msg}")
                else:
                    st.success(f"🎉 Chúc mừng! Đã ghi nhận chữa khỏi đợt bệnh #{selected_dot['ma_dot']} thành công vào ngày {ngay_kt}!")
                    st.rerun()

        st.markdown("---")
        st.subheader("📋 Các Đợt Bệnh Đã Được Chữa Khỏi Gần Đây")
        ok_done, done_dots, _ = db.execute_query("""
            SELECT d.ma_dot, bn.ho_ten AS ten_bn, b.ten_benh, nv.ho_ten AS ten_bs,
                   d.ngay_bat_dau, d.ngay_ket_thuc,
                   (SELECT COUNT(*) FROM lan_kham WHERE ma_dot = d.ma_dot) AS tong_lan_kham
            FROM dot_benh d
            JOIN benh_nhan bn ON bn.ma_bn = d.ma_bn
            JOIN benh b ON b.ma_benh = d.ma_benh
            JOIN nhan_vien nv ON nv.ma_nv = d.ma_bs
            WHERE d.ngay_ket_thuc IS NOT NULL
            ORDER BY d.ngay_ket_thuc DESC
            LIMIT 10
        """)
        if ok_done and done_dots:
            df_done = pd.DataFrame(done_dots)
            df_done.columns = ["Mã Đợt", "Bệnh Nhân", "Tên Bệnh", "Bác Sỹ Phụ Trách", "Ngày Bắt Đầu", "Ngày Khỏi Bệnh", "Tổng Số Lần Khám"]
            st.dataframe(df_done, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------
# DB CONFIG EXPANDER — always at bottom
# ---------------------------------------------------------------------
st.markdown("---")
with st.expander("⚙️ Cấu hình kết nối MySQL", expanded=False):
    if is_connected:
        st.success("🟢 " + conn_msg)
    else:
        st.error("🔴 " + conn_msg)
        st.info("Hãy kiểm tra file `.env` hoặc nhập mật khẩu bên dưới:")

    bot_db_host = st.text_input("DB Host", value=os.getenv("DB_HOST", "localhost"), key="bot_db_host")
    bot_db_port = st.text_input("DB Port", value=os.getenv("DB_PORT", "3306"), key="bot_db_port")
    bot_db_user = st.text_input("DB User", value=os.getenv("DB_USER", "root"), key="bot_db_user")
    bot_db_pass = st.text_input("DB Password", value=os.getenv("DB_PASSWORD", ""), type="password", key="bot_db_pass")
    bot_db_name = st.text_input("DB Name", value=os.getenv("DB_NAME", "phong_kham"), key="bot_db_name")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Kết nối lại", use_container_width=True, key="bot_reconnect"):
            os.environ["DB_HOST"] = bot_db_host
            os.environ["DB_PORT"] = bot_db_port
            os.environ["DB_USER"] = bot_db_user
            os.environ["DB_PASSWORD"] = bot_db_pass
            os.environ["DB_NAME"] = bot_db_name
            st.rerun()
    with col_btn2:
        if st.button("Lưu .env", use_container_width=True, key="bot_save_env"):
            dotenv_path = os.path.join(os.getcwd(), ".env")
            set_key(dotenv_path, "DB_HOST", bot_db_host)
            set_key(dotenv_path, "DB_PORT", bot_db_port)
            set_key(dotenv_path, "DB_USER", bot_db_user)
            set_key(dotenv_path, "DB_PASSWORD", bot_db_pass)
            set_key(dotenv_path, "DB_NAME", bot_db_name)
            st.success("Đã lưu vào .env!")

# ---------------------------------------------------------------------
# CHÂN TRANG HỆ THỐNG
# ---------------------------------------------------------------------
st.markdown(
    "<footer class='custom-footer'>Dữ liệu minh hoạ • MySQL 8 • Streamlit</footer>",
    unsafe_allow_html=True
)
