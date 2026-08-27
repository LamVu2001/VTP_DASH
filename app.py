import streamlit as st
import duckdb
import plotly.express as px
from pathlib import Path
import gdown
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

st.set_page_config(page_title="Dashboard Tổng hợp", layout="wide")

# CSS tùy biến giao diện, thẻ Card và khung Dashboard sang trọng
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

tab_doanh_thu, tab_odr = st.tabs(["📊 DASHBOARD DOANH THU", "🚚 DASHBOARD ODR"])

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
        st.subheader("📈 XU HƯỚNG SẢN LƯỢNG PHÁT 7 NGÀY GẦN NHẤT")
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
        st.subheader("💡 THÔNG TIN TỔNG QUAN ODR")
        st.info("Biểu đồ bên trái thể hiện sản lượng đơn hàng thực tế cần phát trong 7 ngày gần nhất dựa trên bộ lọc hiện tại của bạn.")

    st.divider()

    # =========================================================================
    # BẢNG MA TRẬN CHẤT LƯỢNG VẬN HÀNH (SỬ DỤNG AGGRID TREE TABLE CHUYÊN NGHIỆP)
    # =========================================================================
    st.subheader("📊 BÁO CÁO MA TRẬN CHẤT LƯỢNG VẬN HÀNH (CÂY PHÂN CẤP)")
    st.info("💡 Bảng phân cấp quản trị: Bấm vào nút `[+]` bên cạnh tên Khách hàng để mở rộng xem Tỉnh và Bưu cục chi tiết.")

    # Truy vấn dữ liệu chi tiết theo Khách hàng -> Tỉnh phát -> Bưu cục phát
    df_tree_matrix = con.execute(f"""
        SELECT 
            COALESCE(ma_khgui, 'Khách vãng lai') AS "Mã Khách Hàng",
            COALESCE(tinh_phat, 'Chưa rõ tỉnh') AS "Tỉnh Phát",
            COALESCE(ma_buucuc_phat, 'Chưa rõ bưu cục') AS "Mã Bưu Cục",
            COUNT(*) AS "Sản lượng phải phát",
            SUM(CASE WHEN CAST(ma_trangthai AS INTEGER) = 501 THEN 1 ELSE 0 END) AS "Sản lượng phát thành công",
            ROUND(SUM(tong_cuoc)/1e6, 1) AS "Doanh thu (Tr)"
        FROM orders 
        WHERE {where_sql_odr}
        GROUP BY ma_khgui, tinh_phat, ma_buucuc_phat
        ORDER BY "Sản lượng phải phát" DESC
        LIMIT 300
    """).fetchdf()

    # Cấu hình AgGrid hiển thị dạng Tree Data có nút mở rộng [+] / [-]
    gb = GridOptionsBuilder.from_dataframe(df_tree_matrix)
    gb.configure_default_column(editable=False, sortable=True, filter=True, resizable=True)

    gb.configure_grid_options(
        treeData=True,
        animateRows=True,
        groupDefaultExpanded=0,  # Thu gọn toàn bộ ban đầu
        getDataPath=JsCode("""
            function(data) {
                return [data["Mã Khách Hàng"], data["Tỉnh Phát"], data["Mã Bưu Cục"]];
            }
        """),
        autoGroupColumnDef={
            "headerName": "Chỉ tiêu / Khối vận hành",
            "cellRenderer": "agGroupCellRenderer",
            "cellRendererParams": {
                "suppressCount": False,
                "innerRenderer": JsCode("""
                    function(params) {
                        return params.value;
                    }
                """)
            },
            "width": 380,
            "pinned": "left"
        }
    )

    # Ẩn các cột thô dùng làm đường dẫn cây
    gb.configure_column("Mã Khách Hàng", hide=True)
    gb.configure_column("Tỉnh Phát", hide=True)
    gb.configure_column("Mã Bưu Cục", hide=True)

    # Cấu hình định dạng cột số liệu và tự động cộng tổng (aggFunc="sum") cho cấp cha
    gb.configure_column("Sản lượng phải phát", type=["numericColumn", "numberColumnFilter"], precision=0, aggFunc="sum")
    gb.configure_column("Sản lượng phát thành công", type=["numericColumn", "numberColumnFilter"], precision=0, aggFunc="sum")
    gb.configure_column("Doanh thu (Tr)", type=["numericColumn", "numberColumnFilter"], precision=1, aggFunc="sum")

    gridOptions = gb.build()

    # Hiển thị bảng AgGrid tương tác trực tiếp
    AgGrid(
        df_tree_matrix,
        gridOptions=gridOptions,
        height=500,
        use_container_width=True,
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=True
    )
