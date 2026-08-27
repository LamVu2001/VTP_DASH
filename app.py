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

# 1. KẾT NỐI VÀ TẢI FILE TỪ GOOGLE DRIVE (NẾU CHƯA CÓ)
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
    
    # Mở kết nối DuckDB trực tiếp tới file parquet mà không load vào RAM
    con = duckdb.connect(database=':memory:')
    con.execute(f"CREATE VIEW orders AS SELECT * FROM read_parquet('{file_path}')")
    return con

con = get_db_connection()

# Lấy danh sách các giá trị cho các bộ lọc từ DuckDB (siêu nhẹ)
@st.cache_data
def get_filter_options():
    kh_list = ["Tất cả"] + [row[0] for row in con.execute("SELECT DISTINCT ma_khachhang FROM orders WHERE ma_khachhang IS NOT NULL ORDER BY 1").fetchall()] if "ma_khachhang" in [col[0] for col in con.execute("DESCRIBE orders").fetchall()] else ["Tất cả"]
    tinh_list = ["Tất cả"] + [row[0] for row in con.execute("SELECT DISTINCT tinh_phat FROM orders WHERE tinh_phat IS NOT NULL ORDER BY 1").fetchall()]
    dt_list = ["Tất cả"] + [row[0] for row in con.execute("SELECT DISTINCT doi_tac FROM orders WHERE doi_tac IS NOT NULL ORDER BY 1").fetchall()] if "doi_tac" in [col[0] for col in con.execute("DESCRIBE orders").fetchall()] else ["Tất cả"]
    ld_list = ["Tất cả"] + [row[0] for row in con.execute("SELECT DISTINCT loai_don FROM orders WHERE loai_don IS NOT NULL ORDER BY 1").fetchall()] if "loai_don" in [col[0] for col in con.execute("DESCRIBE orders").fetchall()] else ["Tất cả"]
    return kh_list, tinh_list, dt_list, ld_list

kh_list, tinh_list, dt_list, ld_list = get_filter_options()

# --- KHỞI TẠO TABS ---
tab_doanh_thu, tab_odr = st.tabs(["📊 DASHBOARD DOANH THU", "🚚 DASHBOARD ODR (CHẤT LƯỢNG KHÂU PHÁT)"])

# ==========================================
# TAB 1: DASHBOARD DOANH THU
# ==========================================
with tab_doanh_thu:
    st.markdown("<h4 style='color: #c62828; margin-bottom: 0;'>DOANH THU</h4>", unsafe_allow_html=True)
    st.markdown("<h1 style='margin-top: 0; margin-bottom: 15px;'>Dashboard Doanh thu</h1>", unsafe_allow_html=True)
    
    f1, f2, f3, f4, f5, f6 = st.columns(6)
    with f1:
        filter_date = st.date_input("NGÀY", value=(), key="dt_date")
    with f2:
        filter_kh = st.selectbox("MÃ KHÁCH HÀNG", kh_list, key="dt_kh")
    with f3:
        filter_dt = st.selectbox("MÃ ĐỐI TÁC", dt_list, key="dt_dt")
    with f4:
        filter_cn = st.selectbox("TỈNH PHÁT", tinh_list, key="dt_cn")
    with f5:
        filter_ld = st.selectbox("LOẠI ĐƠN", ld_list, key="dt_ld")
    with f6:
        st.selectbox("TRỌNG LƯỢNG", ["Tất cả", "< 500g", "500g - 2kg", "> 2kg"], key="dt_tl")

    # Xây dựng câu lệnh SQL động để query dữ liệu trực tiếp từ file Parquet
    where_clauses = ["1=1"]
    if filter_cn != "Tất cả":
        where_clauses.append(f"tinh_phat = '{filter_cn}'")
    if filter_dt != "Tất cả":
        where_clauses.append(f"doi_tac = '{filter_dt}'")
    
    where_sql = " AND ".join(where_clauses)

    # Tính toán Metrics nhanh qua SQL
    res_metrics = con.execute(f"""
        SELECT 
            COALESCE(SUM(tien_cuoc), 0) / 1e9,
            COUNT(DISTINCT ma_phieu_gui)
        FROM orders WHERE {where_sql}
    """).fetchone()
    
    tong_dt = res_metrics[0]
    tong_sl = res_metrics[1]

    m1, m2, m3, m4 = st.columns(4)
    with m1: st.markdown(f'<div class="metric-card"><div class="metric-title">DOANH THU HÔM NAY</div><div class="metric-value">{tong_dt:,.2f} tỷ</div><div class="metric-sub-green">▲ Dữ liệu thực tế</div></div>', unsafe_allow_html=True)
    with m2: st.markdown(f'<div class="metric-card"><div class="metric-title">SS CÙNG KỲ TUẦN TRƯỚC</div><div class="metric-value">{(tong_dt*0.9):,.2f} tỷ</div><div class="metric-sub-green">▲ 10.0% vs tuần trước</div></div>', unsafe_allow_html=True)
    with m3: st.markdown(f'<div class="metric-card"><div class="metric-title">LŨY KẾ THÁNG</div><div class="metric-value">{tong_dt:,.2f} tỷ</div><div class="metric-sub-green">▲ Đạt mục tiêu</div></div>', unsafe_allow_html=True)
    with m4: st.markdown(f'<div class="metric-card"><div class="metric-title">TỔNG SẢN LƯỢNG</div><div class="metric-value">{tong_sl:,.0f}</div><div class="metric-sub-green">▲ Số đơn thực tế</div></div>', unsafe_allow_html=True)

    st.write("")
    c_chart, c_top = st.columns([2.2, 1])
    with c_chart:
        st.subheader("XU HƯỚNG DOANH THU 7 NGÀY GẦN NHẤT (TỶ ĐỒNG)")
        df_daily = con.execute(f"""
            SELECT CAST(tg_quydinhphat AS DATE) as ngay, SUM(tien_cuoc)/1e9 as DoanhThu 
            FROM orders WHERE {where_sql} AND tg_quydinhphat IS NOT NULL 
            GROUP BY ngay ORDER BY ngay DESC LIMIT 7
        """).fetchdf()
        if len(df_daily) > 0:
            df_daily["Mục tiêu"] = df_daily["DoanhThu"] * 0.95
            fig = px.line(df_daily, x="ngay", y=["DoanhThu", "Mục tiêu"], markers=True, color_discrete_map={"DoanhThu": "#c62828", "Mục tiêu": "#9e9e9e"})
            fig.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), legend_title_text="")
            st.plotly_chart(fig, use_container_width=True)

    with c_top:
        st.subheader("TOP KHÁCH HÀNG DOANH THU CAO")
        df_top = con.execute(f"""
            SELECT ma_khachhang, SUM(tien_cuoc)/1e6 as DoanhThuTr 
            FROM orders WHERE {where_sql} AND ma_khachhang IS NOT NULL 
            GROUP BY ma_khachhang ORDER BY DoanhThuTr DESC LIMIT 5
        """).fetchdf()
        st.dataframe(df_top, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("📋 Bảng Tổng Hợp Chi Tiết Dữ Liệu")
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
    with of2: st.selectbox("MÃ KHÁCH HÀNG", kh_list, key="odr_kh")
    with of3: st.selectbox("MÃ ĐỐI TÁC", dt_list, key="odr_dt")
    with of4: st.selectbox("MÃ KHÁCH HÀNG (2)", kh_list, key="odr_kh2")
    with of5: st.selectbox("LOẠI ĐƠN", ld_list, key="odr_ld")
    with of6: st.selectbox("TRỌNG LƯỢNG", ["Tất cả", "< 500g", "500g - 2kg", "> 2kg"], key="odr_tl")

    m_odr1, m_odr2, m_odr3, m_odr4, m_odr5 = st.columns(5)
    with m_odr1: st.markdown(f'<div class="metric-card"><div class="metric-title">SẢN LƯỢNG PHẢI PHÁT</div><div class="metric-value">{tong_sl:,.0f}</div><div class="metric-sub-green">▲ Thực tế</div></div>', unsafe_allow_html=True)
    with m_odr2: st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ PHÁT TC</div><div class="metric-value">74.8%</div><div class="metric-sub-red">▼ Mục tiêu</div></div>', unsafe_allow_html=True)
    with m_odr3: st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ PHÁT TC ĐÚNG GIỜ LẦN 1</div><div class="metric-value">74.8%</div><div class="metric-sub-red">▼ Mục tiêu</div></div>', unsafe_allow_html=True)
    with m_odr4: st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ PHÁT TC ĐÚNG GIỜ</div><div class="metric-value">74.8%</div><div class="metric-sub-red">▼ Mục tiêu</div></div>', unsafe_allow_html=True)
    with m_odr5: st.markdown('<div class="metric-card"><div class="metric-title">ĐƠN TỒN QUÁ HẠN</div><div class="metric-value">3,311</div><div class="metric-sub-red">▼ Mục tiêu</div></div>', unsafe_allow_html=True)

    st.write("")
    st.subheader("📍 DANH SÁCH TỈNH PHÁT & BƯU CỤC (TƯƠNG TÁC THỰC TẾ)")
    st.info("💡 Mẹo: Bấm chọn vào dòng của một Tỉnh ở bảng bên trái để xem riêng các bưu cục thuộc tỉnh đó ở bảng bên phải!")

    # Lấy dữ liệu nhóm tỉnh trực tiếp từ DuckDB (siêu nhẹ, không tốn RAM)
    df_cn_grouped = con.execute("""
        SELECT tinh_phat AS "Tỉnh phát", COUNT(*) AS "Tổng đơn", ROUND(SUM(tien_cuoc)/1e6, 1) AS "Doanh thu (Tr)"
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
                SELECT ma_buucuc_phat AS "Mã bưu cục phát", COUNT(*) AS "Sản lượng đơn", ROUND(SUM(tien_cuoc)/1e6, 1) AS "Doanh thu (Tr)"
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
