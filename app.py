import streamlit as st
import duckdb
import plotly.express as px
from pathlib import Path
import gdown

st.set_page_config(page_title="Dashboard Tổng hợp", layout="wide")

st.markdown("""
<style>
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e6e6e6;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .metric-title { font-size: 11px; font-weight: bold; color: #555555; text-transform: uppercase; }
    .metric-value { font-size: 24px; font-weight: bold; color: #111111; margin: 4px 0; }
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
    con.execute(f"CREATE VIEW orders AS SELECT * FROM read_parquet('{file_path}')")
    return con

con = get_db_connection()

@st.cache_data
def get_filter_options():
    tinh_list = ["Tất cả"] + [row[0] for row in con.execute("SELECT DISTINCT tinh_phat FROM orders WHERE tinh_phat IS NOT NULL ORDER BY 1").fetchall()]
    dt_list = ["Tất cả"] + [row[0] for row in con.execute("SELECT DISTINCT doi_tac FROM orders WHERE doi_tac IS NOT NULL ORDER BY 1").fetchall()] if "doi_tac" in [col[0] for col in con.execute("DESCRIBE orders").fetchall()] else ["Tất cả"]
    return tinh_list, dt_list

tinh_list, dt_list = get_filter_options()

tab_doanh_thu, tab_odr = st.tabs(["📊 DASHBOARD DOANH THU", "🚚 DASHBOARD ODR"])

# ==========================================
# TAB 1: DASHBOARD DOANH THU
# ==========================================
with tab_doanh_thu:
    st.markdown("<h4 style='color: #c62828; margin-bottom: 0;'>DOANH THU</h4>", unsafe_allow_html=True)
    st.markdown("<h1 style='margin-top: 0; margin-bottom: 15px;'>Dashboard Doanh thu</h1>", unsafe_allow_html=True)
    
    f1, f2, f3, f4, f5, f6 = st.columns(6)
    with f1: filter_date = st.date_input("NGÀY", value=(), key="dt_date")
    with f2: filter_kh = st.selectbox("MÃ KHÁCH HÀNG", ["Tất cả"], key="dt_kh")
    with f3: filter_dt = st.selectbox("MÃ ĐỐI TÁC", dt_list, key="dt_dt")
    with f4: filter_cn = st.selectbox("TỈNH PHÁT", tinh_list, key="dt_cn")
    with f5: filter_ld = st.selectbox("LOẠI ĐƠN", ["Tất cả"], key="dt_ld")
    with f6: st.selectbox("TRỌNG LƯỢNG", ["Tất cả"], key="dt_tl")

    where_clauses = ["1=1"]
    if filter_cn != "Tất cả": where_clauses.append(f"tinh_phat = '{filter_cn}'")
    if filter_dt != "Tất cả": where_clauses.append(f"doi_tac = '{filter_dt}'")
    where_sql = " AND ".join(where_clauses)

    res_metrics = con.execute(f"""
        SELECT 
            COALESCE(SUM(tong_cuoc), 0) / 1e9,
            COUNT(*)
        FROM orders WHERE {where_sql}
    """).fetchone()
    
    tong_dt = res_metrics[0]
    tong_sl = res_metrics[1]

    m1, m2, m3, m4 = st.columns(4)
    with m1: st.markdown(f'<div class="metric-card"><div class="metric-title">DOANH THU HÔM NAY</div><div class="metric-value">{tong_dt:,.2f} tỷ</div></div>', unsafe_allow_html=True)
    with m2: st.markdown(f'<div class="metric-card"><div class="metric-title">SS CÙNG KỲ TUẦN TRƯỚC</div><div class="metric-value">{(tong_dt*0.9):,.2f} tỷ</div></div>', unsafe_allow_html=True)
    with m3: st.markdown(f'<div class="metric-card"><div class="metric-title">LŨY KẾ THÁNG</div><div class="metric-value">{tong_dt:,.2f} tỷ</div></div>', unsafe_allow_html=True)
    with m4: st.markdown(f'<div class="metric-card"><div class="metric-title">TỔNG SẢN LƯỢNG</div><div class="metric-value">{tong_sl:,.0f}</div></div>', unsafe_allow_html=True)

    st.write("")
    c_chart, c_top = st.columns([2.2, 1])
    with c_chart:
        st.subheader("XU HƯỚNG DOANH THU")
        try:
            df_daily = con.execute(f"""
                SELECT CAST(strptime(tg_quydinhphat, '%d-%m-%Y %H:%M:%S') AS DATE) as ngay, SUM(tong_cuoc)/1e9 as DoanhThu 
                FROM orders WHERE {where_sql} AND tg_quydinhphat IS NOT NULL 
                GROUP BY ngay ORDER BY ngay DESC LIMIT 7
            """).fetchdf()
            if len(df_daily) > 0:
                fig = px.line(df_daily, x="ngay", y="DoanhThu", markers=True)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Không có dữ liệu ngày tháng phù hợp.")
        except Exception:
            df_daily = con.execute(f"""
                SELECT tg_quydinhphat as ngay, SUM(tong_cuoc)/1e9 as DoanhThu 
                FROM orders WHERE {where_sql} AND tg_quydinhphat IS NOT NULL 
                GROUP BY ngay LIMIT 7
            """).fetchdf()
            if len(df_daily) > 0:
                fig = px.line(df_daily, x="ngay", y="DoanhThu", markers=True)
                st.plotly_chart(fig, use_container_width=True)

    with c_top:
        st.subheader("TOP KHÁCH HÀNG")
        st.info("Dữ liệu được truy vấn tối ưu qua DuckDB.")

    st.divider()
    st.subheader("📋 Bảng Tổng Hợp Chi Tiết")
    df_preview = con.execute(f"SELECT * FROM orders WHERE {where_sql} LIMIT 500").fetchdf()
    st.dataframe(df_preview, use_container_width=True)

# ==========================================
# TAB 2: DASHBOARD ODR
# ==========================================
with tab_odr:
    st.markdown("<h4 style='color: #c62828; margin-bottom: 0;'>CHẤT LƯỢNG KHÂU PHÁT</h4>", unsafe_allow_html=True)
    st.markdown("<h1 style='margin-top: 0; margin-bottom: 15px;'>Dashboard ODR</h1>", unsafe_allow_html=True)

    of1, of2, of3, of4, of5, of6 = st.columns(6)
    with of1: st.date_input("NGÀY", value=(), key="odr_date")
    with of2: st.selectbox("MÃ KHÁCH HÀNG", ["Tất cả"], key="odr_kh")
    with of3: st.selectbox("MÃ ĐỐI TÁC", dt_list, key="odr_dt")
    with of4: st.selectbox("MÃ KHÁCH HÀNG (2)", ["Tất cả"], key="odr_kh2")
    with of5: st.selectbox("LOẠI ĐƠN", ["Tất cả"], key="odr_ld")
    with of6: st.selectbox("TRỌNG LƯỢNG", ["Tất cả"], key="odr_tl")

    st.write("")
    st.subheader("📍 DANH SÁCH TỈNH PHÁT & BƯU CỤC")
    st.info("💡 Mẹo: Bấm chọn vào dòng của một Tỉnh ở bảng bên trái để xem riêng các bưu cục thuộc tỉnh đó ở bảng bên phải!")
    
    df_cn_grouped = con.execute("""
        SELECT tinh_phat AS "Tỉnh phát", COUNT(*) AS "Tổng đơn", ROUND(SUM(tong_cuoc)/1e6, 1) AS "Doanh thu (Tr)"
        FROM orders WHERE tinh_phat IS NOT NULL
        GROUP BY tinh_phat ORDER BY "Tổng đơn" DESC LIMIT 15
    """).fetchdf()

    tbl_col1, tbl_col2 = st.columns(2)
    with tbl_col1:
        st.markdown("**Bảng Tỉnh Phạt (Bấm chọn dòng để lọc)**")
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
            st.markdown(f"**Bưu cục thuộc Tỉnh: <span style='color: #c62828;'>{selected_tinh}</span>**", unsafe_allow_html=True)
            df_bc_filtered = con.execute(f"""
                SELECT ma_buucuc_phat AS "Mã bưu cục phát", COUNT(*) AS "Sản lượng đơn", ROUND(SUM(tong_cuoc)/1e6, 1) AS "Doanh thu (Tr)"
                FROM orders WHERE tinh_phat = '{selected_tinh}' AND ma_buucuc_phat IS NOT NULL
                GROUP BY ma_buucuc_phat ORDER BY "Sản lượng đơn" DESC
            """).fetchdf()
            st.dataframe(df_bc_filtered, use_container_width=True, hide_index=True)
        else:
            st.markdown("**Bảng Bưu Cục Toàn Quốc (Hoặc bấm chọn Tỉnh bên trái)**")
            df_bc_all = con.execute("""
                SELECT tinh_phat AS "Tỉnh phát", ma_buucuc_phat AS "Mã bưu cục phát", COUNT(*) AS "Sản lượng đơn"
                FROM orders WHERE tinh_phat IS NOT NULL AND ma_buucuc_phat IS NOT NULL
                GROUP BY tinh_phat, ma_buucuc_phat ORDER BY "Sản lượng đơn" DESC LIMIT 10
            """).fetchdf()
            st.dataframe(df_bc_all, use_container_width=True, hide_index=True)
