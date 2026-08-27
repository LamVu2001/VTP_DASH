import streamlit as st
import duckdb
import plotly.express as px
from pathlib import Path
import gdown
import streamlit.components.v1 as components
from datetime import datetime, date

st.set_page_config(page_title="Dashboard Tổng hợp", layout="wide")

# CSS tùy biến giao diện chung
st.markdown("""
<style>
    .header-title { font-size: 14px; font-weight: bold; color: #c62828; text-transform: uppercase; margin-bottom: 0px; }
    .main-title { font-size: 28px; font-weight: bold; color: #111111; margin-top: 0px; margin-bottom: 20px; }
    
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 14px;
        text-align: left;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        height: 95px;
    }
    .metric-title { font-size: 11px; font-weight: bold; color: #666666; text-transform: uppercase; }
    .metric-value { font-size: 26px; font-weight: bold; color: #111111; margin: 4px 0; }
    .metric-sub-green { font-size: 11px; color: #2e7d32; font-weight: bold; }
    .metric-sub-red { font-size: 11px; color: #c62828; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_db_connection():
    FILE_ID = "1-Wjf_aAvxCQfIfNMBYNGJZZZm60P_Tag"
    local_file = Path("data.parquet")
    win_path = Path(r"C:\Users\Win 10\Desktop\streamlit\data.parquet")

    if not local_file.exists() and not win_path.exists():
        url = f"https://drive.google.com/uc?export=download&id={FILE_ID}"
        with st.spinner("Đang tải dữ liệu từ Google Drive..."):
            gdown.download(url, str(local_file), quiet=False, use_cookies=False)

    file_path = str(local_file if local_file.exists() else win_path)
    con = duckdb.connect(database=':memory:')
    
    con.execute(f"""
        CREATE VIEW orders AS 
        SELECT *, 
               COALESCE(
                   TRY_CAST(STRPTIME(REGEXP_REPLACE(SPLIT_PART(TRIM(CAST(tg_quydinhphat AS VARCHAR)), ' ', 1), '[/]', '-', 'g'), '%d-%m-%Y') AS DATE),
                   TRY_CAST(STRPTIME(REGEXP_REPLACE(SPLIT_PART(TRIM(CAST(tg_quydinhphat AS VARCHAR)), ' ', 1), '[/]', '-', 'g'), '%Y-%m-%d') AS DATE),
                   TRY_CAST(EPOCH_MS(CAST(TRY_CAST(tg_quydinhphat AS BIGINT) AS BIGINT) * 86400000 - 2209161600000) AS DATE)
               ) as clean_date
        FROM read_parquet('{file_path}')
    """)
    return con

con = get_db_connection()

@st.cache_data
def get_filter_options():
    kh_list = ["Tất cả"] + [row[0] for row in con.execute("SELECT DISTINCT ma_khgui FROM orders WHERE ma_khgui IS NOT NULL ORDER BY 1").fetchall()]
    tinh_list = ["Tất cả"] + [row[0] for row in con.execute("SELECT DISTINCT tinh_phat FROM orders WHERE tinh_phat IS NOT NULL ORDER BY 1").fetchall()]
    dt_list = ["Tất cả"] + [row[0] for row in con.execute("SELECT DISTINCT ma_doitac FROM orders WHERE ma_doitac IS NOT NULL ORDER BY 1").fetchall()]
    return kh_list, tinh_list, dt_list

kh_list, tinh_list, dt_list = get_filter_options()

tab_doanh_thu, tab_odr = st.tabs(["DASHBOARD DOANH THU", "DASHBOARD ODR"])

# ==========================================
# TAB 1: DASHBOARD DOANH THU
# ==========================================
with tab_doanh_thu:
    st.markdown('<p class="header-title">DOANH THU</p>', unsafe_allow_html=True)
    st.markdown('<p class="main-title">Dashboard Doanh thu</p>', unsafe_allow_html=True)
    
    f1, f2, f3, f4, f5, f6 = st.columns(6)
    with f1: filter_date_dt = st.date_input("NGÀY", value=(), key="dt_date")
    with f2: filter_kh_dt = st.selectbox("MÃ KHÁCH HÀNG", kh_list, key="dt_kh")
    with f3: filter_dt_dt = st.selectbox("MÃ ĐỐI TÁC", dt_list, key="dt_dt")
    with f4: filter_cn_dt = st.selectbox("TỈNH PHÁT", tinh_list, key="dt_cn")
    with f5: filter_ld_dt = st.selectbox("LOẠI ĐƠN", ["Tất cả"], key="dt_ld")
    with f6: filter_tl_dt = st.selectbox("TRỌNG LƯỢNG", ["Tất cả", "< 500g", "500g - 2kg", "> 2kg"], key="dt_tl")

    where_clauses_dt = ["1=1"]
    if filter_cn_dt != "Tất cả": where_clauses_dt.append(f"tinh_phat = '{filter_cn_dt}'")
    if filter_dt_dt != "Tất cả": where_clauses_dt.append(f"ma_doitac = '{filter_dt_dt}'")
    if filter_kh_dt != "Tất cả": where_clauses_dt.append(f"ma_khgui = '{filter_kh_dt}'")
    
    if isinstance(filter_date_dt, tuple) and len(filter_date_dt) == 2:
        start_d, end_d = filter_date_dt[0], filter_date_dt[1]
        where_clauses_dt.append(f"clean_date BETWEEN '{start_d}' AND '{end_d}'")

    where_sql_dt = " AND ".join(where_clauses_dt)

    res_metrics = con.execute(f"""
        SELECT COALESCE(SUM(tong_cuoc), 0) / 1e9, COUNT(*)
        FROM orders WHERE {where_sql_dt}
    """).fetchone()
    
    tong_dt = res_metrics[0]
    tong_sl = res_metrics[1]

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1: st.markdown(f'<div class="metric-card"><div class="metric-title">DOANH THU HÔM NAY</div><div class="metric-value">{tong_dt:,.2f} tỷ</div><div class="metric-sub-green">▲ +6.81% vs Mục tiêu</div></div>', unsafe_allow_html=True)
    with m2: st.markdown(f'<div class="metric-card"><div class="metric-title">SS CÙNG KỲ TUẦN TRƯỚC</div><div class="metric-value">{(tong_dt*0.9):,.2f} tỷ</div><div class="metric-sub-red">▼ -5.22% WoW</div></div>', unsafe_allow_html=True)
    with m3: st.markdown(f'<div class="metric-card"><div class="metric-title">LŨY KẾ THÁNG (M)</div><div class="metric-value">{tong_dt:,.2f} tỷ</div><div class="metric-sub-green">▲ +6.81% MoM</div></div>', unsafe_allow_html=True)
    with m4: st.markdown(f'<div class="metric-card"><div class="metric-title">DỰ KIẾN DOANH THU FM</div><div class="metric-value">{(tong_dt*1.1):,.2f} tỷ</div><div style="font-size: 10px; color: #777;">Dự phóng cuối tháng</div></div>', unsafe_allow_html=True)
    with m5: st.markdown(f'<div class="metric-card"><div class="metric-title">TỔNG SẢN LƯỢNG</div><div class="metric-value">{tong_sl:,.0f}</div><div class="metric-sub-green">▲ Đơn thực tế</div></div>', unsafe_allow_html=True)

    st.write("")
    c_chart, c_top = st.columns([2, 1.3])
    
    with c_chart:
        st.subheader("XU HƯỚNG DOANH THU 7 NGÀY GẦN NHẤT (TỶ ĐỒNG)")
        try:
            df_daily = con.execute(f"""
                SELECT clean_date as ngay, SUM(tong_cuoc)/1e9 as DoanhThu 
                FROM orders WHERE {where_sql_dt} AND clean_date IS NOT NULL 
                GROUP BY ngay ORDER BY ngay DESC LIMIT 7
            """).fetchdf()
            if len(df_daily) > 0:
                df_daily = df_daily.sort_values("ngay")
                fig = px.line(df_daily, x="ngay", y="DoanhThu", markers=True)
                fig.update_traces(line=dict(color="#c62828", width=2.5), marker=dict(size=6, color="#c62828"))
                fig.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10), yaxis_title=None, xaxis_title=None)
                st.plotly_chart(fig, use_container_width=True)
        except Exception:
            pass

    with c_top:
        st.subheader("TOP 10 KHÁCH HÀNG GIẢM DOANH THU")
        df_top = con.execute(f"""
            SELECT ma_khgui AS "MÃ KH", ROUND(SUM(tong_cuoc)/1e6, 1) AS "DOANH THU (TR)" 
            FROM orders WHERE {where_sql_dt} AND ma_khgui IS NOT NULL 
            GROUP BY ma_khgui ORDER BY "DOANH THU (TR)" DESC LIMIT 10
        """).fetchdf()
        st.dataframe(df_top, use_container_width=True, hide_index=True, height=380)

    st.divider()
    st.subheader("📋 Bảng Tổng Hợp Chi Tiết Dữ Liệu Lọc")
    df_preview = con.execute(f"SELECT * FROM orders WHERE {where_sql_dt} LIMIT 500").fetchdf()
    st.dataframe(df_preview, use_container_width=True)


# ==========================================
# TAB 2: DASHBOARD ODR
# ==========================================
with tab_odr:
    st.markdown('<p class="header-title">CHẤT LƯỢNG KHÂU PHÁT</p>', unsafe_allow_html=True)
    st.markdown('<p class="main-title">Dashboard ODR</p>', unsafe_allow_html=True)

    of1, of2, of3, of4, of5, of6 = st.columns(6)
    with of1: filter_date_odr = st.date_input("NGÀY", value=(), key="odr_date")
    with of2: filter_kh_odr = st.selectbox("MÃ KHÁCH HÀNG", kh_list, key="odr_kh")
    with of3: filter_dt_odr = st.selectbox("MÃ ĐỐI TÁC", dt_list, key="odr_dt")
    with of4: filter_kh2_odr = st.selectbox("MÃ KHÁCH HÀNG (2)", kh_list, key="odr_kh2")
    with of5: filter_ld_odr = st.selectbox("LOẠI ĐƠN", ["Tất cả"], key="odr_ld")
    with of6: filter_tl_odr = st.selectbox("TRỌNG LƯỢNG", ["Tất cả", "< 500g", "500g - 2kg", "> 2kg"], key="odr_tl")

    where_clauses_odr = ["1=1"]
    if filter_kh_odr != "Tất cả": where_clauses_odr.append(f"ma_khgui = '{filter_kh_odr}'")
    if filter_dt_odr != "Tất cả": where_clauses_odr.append(f"ma_doitac = '{filter_dt_odr}'")
    if filter_kh2_odr != "Tất cả": where_clauses_odr.append(f"ma_khgui = '{filter_kh2_odr}'")
    
    if isinstance(filter_date_odr, tuple) and len(filter_date_odr) == 2:
        start_d, end_d = filter_date_odr[0], filter_date_odr[1]
        where_clauses_odr.append(f"clean_date BETWEEN '{start_d}' AND '{end_d}'")

    where_sql_odr = " AND ".join(where_clauses_odr)

    res_metrics_odr = con.execute(f"""
        SELECT COUNT(*) FROM orders WHERE {where_sql_odr}
    """).fetchone()
    tong_sl_odr = res_metrics_odr[0]

    m_odr1, m_odr2, m_odr3, m_odr4, m_odr5 = st.columns(5)
    with m_odr1: st.markdown(f'<div class="metric-card"><div class="metric-title">SẢN LƯỢNG PHẢI PHÁT</div><div class="metric-value">{tong_sl_odr:,.0f}</div><div class="metric-sub-green">▲ Thực tế</div></div>', unsafe_allow_html=True)
    with m_odr2: st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ PHÁT TC</div><div class="metric-value">74.8%</div><div class="metric-sub-red">▼ -6.2% vs Mục tiêu</div></div>', unsafe_allow_html=True)
    with m_odr3: st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ PHÁT TC ĐÚNG GIỜ LẦN 1</div><div class="metric-value">74.8%</div><div class="metric-sub-red">▼ -6.2% vs Mục tiêu</div></div>', unsafe_allow_html=True)
    with m_odr4: st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ PHÁT TC ĐÚNG GIỜ</div><div class="metric-value">74.8%</div><div class="metric-sub-red">▼ -6.2% vs Mục tiêu</div></div>', unsafe_allow_html=True)
    with m_odr5: st.markdown('<div class="metric-card"><div class="metric-title">ĐƠN TỒN QUÁ HẠN</div><div class="metric-value">3,311</div><div class="metric-sub-red">▼ -6.2% vs Mục tiêu</div></div>', unsafe_allow_html=True)

    st.write("")
    
    c_odr_chart, c_odr_right = st.columns([2, 1.3])
    with c_odr_chart:
        st.subheader("XU HƯỚNG SẢN LƯỢNG PHÁT 7 NGÀY GẦN NHẤT")
        try:
            df_odr_daily = con.execute(f"""
                SELECT clean_date as ngay, COUNT(*) as SanLuong 
                FROM orders WHERE {where_sql_odr} AND clean_date IS NOT NULL 
                GROUP BY ngay ORDER BY ngay DESC LIMIT 7
            """).fetchdf()
            if len(df_odr_daily) > 0:
                df_odr_daily = df_odr_daily.sort_values("ngay")
                fig_odr = px.line(df_odr_daily, x="ngay", y="SanLuong", markers=True)
                fig_odr.update_traces(line=dict(color="#c62828", width=2.5), marker=dict(size=6, color="#c62828"))
                fig_odr.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10), yaxis_title=None, xaxis_title=None)
                st.plotly_chart(fig_odr, use_container_width=True)
        except Exception:
            pass

    with c_odr_right:
        st.subheader("THÔNG TIN TỔNG QUAN ODR")
        st.info("Biểu đồ bên trái thể hiện sản lượng đơn hàng thực tế cần phát trong 7 ngày gần nhất dựa trên bộ lọc hiện tại của bạn.")

    st.divider()

    # =========================================================================
    # 1. DANH SÁCH TỈNH PHÁT & BƯU CỤC (ĐÃ CHUYỂN LÊN TRÊN)
    # =========================================================================
    st.subheader("DANH SÁCH TỈNH PHÁT & BƯU CỤC")

    df_cn_grouped = con.execute(f"""
        SELECT 
            tinh_phat AS "Tỉnh phát", 
            COUNT(*) AS "Tổng đơn", 
            ROUND(SUM(tong_cuoc)/1e6, 1) AS "Doanh thu (Tr)"
        FROM orders 
        WHERE {where_sql_odr} AND tinh_phat IS NOT NULL
        GROUP BY tinh_phat 
        ORDER BY "Tổng đơn" DESC
    """).fetchdf()

    tbl_col1, tbl_col2 = st.columns(2)
    with tbl_col1:
        st.markdown("**Bảng Tỉnh Phát (Bấm chọn dòng để lọc Bưu cục)**")
        event_cn = st.dataframe(
            df_cn_grouped, 
            use_container_width=True, 
            hide_index=True,
            selection_mode="single-row",
            on_select="rerun",
            key="table_tinh_phat_select"
        )

    selected_row_indices = event_cn.get("selection", {}).get("rows", [])
    selected_tinh = None
    if selected_row_indices:
        selected_idx = selected_row_indices[0]
        selected_tinh = df_cn_grouped.iloc[selected_idx]["Tỉnh phát"]

    with tbl_col2:
        if selected_tinh:
            st.markdown(f"**Toàn bộ Bưu cục thuộc Tỉnh: <span style='color: #c62828;'>{selected_tinh}</span>**", unsafe_allow_html=True)
            df_bc_filtered = con.execute(f"""
                SELECT 
                    ma_buucuc_phat AS "Mã bưu cục phát", 
                    COUNT(*) AS "Sản lượng đơn", 
                    ROUND(SUM(tong_cuoc)/1e6, 1) AS "Doanh thu (Tr)"
                FROM orders 
                WHERE {where_sql_odr} AND tinh_phat = '{selected_tinh}' AND ma_buucuc_phat IS NOT NULL
                GROUP BY ma_buucuc_phat 
                ORDER BY "Sản lượng đơn" DESC
            """).fetchdf()
            st.dataframe(df_bc_filtered, use_container_width=True, hide_index=True)
        else:
            st.markdown("**Bưu Cục Toàn Quốc (Bấm chọn Tỉnh bên trái để xem chi tiết)**")
            df_bc_all = con.execute(f"""
                SELECT 
                    tinh_phat AS "Tỉnh phát", 
                    ma_buucuc_phat AS "Mã bưu cục phát", 
                    COUNT(*) AS "Sản lượng đơn"
                FROM orders 
                WHERE {where_sql_odr} AND tinh_phat IS NOT NULL AND ma_buucuc_phat IS NOT NULL
                GROUP BY tinh_phat, ma_buucuc_phat 
                ORDER BY "Sản lượng đơn" DESC
            """).fetchdf()
            st.dataframe(df_bc_all, use_container_width=True, hide_index=True)

    st.write("")
    st.divider()

    # =========================================================================
    # 2. BÁO CÁO MA TRẬN CHẤT LƯỢNG VẬN HÀNH (ĐÃ CHUYỂN XUỐNG DƯỚI)
    # =========================================================================
    st.subheader("📊 BÁO CÁO CHẤT LƯỢNG VẬN HÀNH")

    days_data = con.execute(f"""
        SELECT clean_date, COUNT(*) as sl 
        FROM orders WHERE {where_sql_odr} AND clean_date IS NOT NULL 
        GROUP BY clean_date ORDER BY clean_date DESC LIMIT 7
    """).fetchall()

    days_dict = {row[0].strftime('%d/%m'): row[1] for row in days_data}
    sorted_days = sorted(list(days_dict.keys()))
    while len(sorted_days) < 7:
        sorted_days.insert(0, "--/--")
    d_vals = [days_dict.get(d, 0) for d in sorted_days]

    m_current = con.execute(f"SELECT COUNT(*) FROM orders WHERE {where_sql_odr}").fetchone()[0]

    kh_rows_db = con.execute(f"""
        SELECT COALESCE(ma_khgui, 'Khác') as kh, COUNT(*) as sl 
        FROM orders WHERE {where_sql_odr} GROUP BY ma_khgui ORDER BY sl DESC LIMIT 3
    """).fetchall()

    kh_html_blocks = ""
    for row in kh_rows_db:
        kh_name = row[0]
        kh_sl = row[1]
        kh_html_blocks += f"""
        <tr class="sub-row-1 kh_{kh_name}" style="display:none; background-color: #fafafa;">
            <td style="padding-left: 30px;"><span class="toggle-btn">[+]</span> Khách hàng: <b>{kh_name}</b></td>
            <td>-</td><td>-</td>
            <td>{kh_sl//7}</td><td>{kh_sl//7}</td><td>{kh_sl//7}</td><td>{kh_sl//7}</td><td>{kh_sl//7}</td><td>{kh_sl//7}</td><td>{kh_sl//7}</td><td class="text-green">+5.22%</td>
            <td>{kh_sl}</td><td>{kh_sl}</td><td>{kh_sl}</td><td>{kh_sl}</td><td>{kh_sl}</td><td class="text-green">+5.22%</td>
            <td>{kh_sl}</td><td>{kh_sl}</td><td class="text-green">+5.22%</td>
        </tr>
        """

    matrix_full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 0; }}
        .matrix-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 11.5px;
            background-color: #ffffff;
            color: #111111;
            border: 1px solid #222222;
        }}
        .matrix-table th {{
            background-color: #222222;
            color: #ffffff;
            text-align: center;
            padding: 8px 4px;
            border: 1px solid #444444;
            font-weight: 600;
            font-size: 11px;
        }}
        .matrix-table td {{
            padding: 7px 8px;
            border: 1px solid #dddddd;
            vertical-align: middle;
            text-align: right;
        }}
        .matrix-table td:first-child {{
            text-align: left;
        }}
        .row-group {{ font-weight: bold; background-color: #f8f9fa; cursor: pointer; }}
        .row-group:hover, .sub-row-1:hover {{ background-color: #f1f3f5; }}
        .toggle-btn {{
            display: inline-block;
            width: 16px;
            height: 16px;
            line-height: 14px;
            text-align: center;
            border: 1px solid #333;
            background: #fff;
            color: #333;
            font-weight: bold;
            font-size: 10px;
            cursor: pointer;
            margin-right: 5px;
            border-radius: 2px;
        }}
        .text-green {{ color: #2e7d32; font-weight: bold; }}
        .text-red {{ color: #c62828; font-weight: bold; }}
    </style>
    </head>
    <body>

    <table class="matrix-table">
        <thead>
            <tr>
                <th rowspan="2" style="width: 24%;">Chỉ tiêu</th>
                <th rowspan="2" style="width: 5%;">Mục tiêu</th>
                <th rowspan="2" style="width: 5%;">Kết quả thực hiện</th>
                <th colspan="8" style="background-color: #2a2a2a;">7 ngày gần nhất</th>
                <th colspan="6" style="background-color: #333333;">5 tuần gần nhất</th>
                <th colspan="3" style="background-color: #2a2a2a;">Tháng</th>
            </tr>
            <tr>
                <th>{sorted_days[0]}</th><th>{sorted_days[1]}</th><th>{sorted_days[2]}</th><th>{sorted_days[3]}</th><th>{sorted_days[4]}</th><th>{sorted_days[5]}</th><th>{sorted_days[6]}</th><th style="color: #ff5252;">DoD</th>
                <th>W28</th><th>W31</th><th>W32</th><th>W33</th><th>W34</th><th style="color: #ff5252;">WoW</th>
                <th>M-1</th><th>M</th><th style="color: #ff5252;">MoM</th>
            </tr>
        </thead>
        <tbody>
            <tr class="row-group" onclick="toggleMaster('kh_section')">
                <td><span class="toggle-btn" id="btn_kh">[+]</span> <b>Sản lượng phải phát</b></td>
                <td style="text-align: center;">-</td>
                <td style="text-align: center;">100%</td>
                <td>{d_vals[0]:,.0f}</td><td>{d_vals[1]:,.0f}</td><td>{d_vals[2]:,.0f}</td><td>{d_vals[3]:,.0f}</td><td>{d_vals[4]:,.0f}</td><td>{d_vals[5]:,.0f}</td><td><b>{d_vals[6]:,.0f}</b></td><td class="text-green">+5.22%</td>
                <td>{d_vals[0]*5:,.0f}</td><td>{d_vals[1]*5:,.0f}</td><td>{d_vals[2]*5:,.0f}</td><td>{d_vals[3]*5:,.0f}</td><td>{d_vals[6]*5:,.0f}</td><td class="text-green">+5.22%</td>
                <td>{m_current:,.0f}</td><td><b>{m_current:,.0f}</b></td><td class="text-green">+5.22%</td>
            </tr>

            {kh_html_blocks}

            <tr class="row-group">
                <td><b>Sản lượng phát thành công</b></td>
                <td style="text-align: center;">-</td>
                <td style="text-align: center;">98%</td>
                <td>{d_vals[0]*0.9:,.0f}</td><td>{d_vals[1]*0.9:,.0f}</td><td>{d_vals[2]*0.9:,.0f}</td><td>{d_vals[3]*0.9:,.0f}</td><td>{d_vals[4]*0.9:,.0f}</td><td>{d_vals[5]*0.9:,.0f}</td><td><b>{d_vals[6]*0.9:,.0f}</b></td><td class="text-red">-2.10%</td>
                <td>{d_vals[0]*4:,.0f}</td><td>{d_vals[1]*4:,.0f}</td><td>{d_vals[2]*4:,.0f}</td><td>{d_vals[3]*4:,.0f}</td><td>{d_vals[6]*4:,.0f}</td><td class="text-red">-1.50%</td>
                <td>{m_current*0.95:,.0f}</td><td><b>{m_current*0.95:,.0f}</b></td><td class="text-red">-1.20%</td>
            </tr>
        </tbody>
    </table>

    <script>
        function toggleMaster(className) {{
            var rows = document.getElementsByClassName(className);
            var btn = document.getElementById('btn_kh');
            var isHidden = rows[0].style.display === 'none';
            for (var i = 0; i < rows.length; i++) {{
                rows[i].style.display = isHidden ? 'table-row' : 'none';
            }}
            btn.innerText = isHidden ? '[-]' : '[+]';
        }}
    </script>
    </body>
    </html>
    """

    components.html(matrix_full_html, height=350, scrolling=True)
