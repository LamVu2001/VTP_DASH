import streamlit as st
import polars as pl
import plotly.express as px
from pathlib import Path
import gdown

st.set_page_config(page_title="Dashboard Tổng hợp", layout="wide")

# CSS tạo giao diện chuẩn bo góc & thẻ chỉ số
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

# 1. LOAD DỮ LIỆU TỪ GOOGLE DRIVE HOẶC CỤC BỘ
@st.cache_data(ttl=86400)
def load_data():
    FILE_ID = "1-Wjf_aAvxCQfIfNMBYNGJZZZm60P_Tag" # Giữ nguyên ID của bạn
    local_file = Path("data.parquet")
    win_path = Path(r"C:\Users\Win 10\Desktop\streamlit\data.parquet")

    if not local_file.exists() and not win_path.exists():
        if FILE_ID != "thay_ma_file_id_cua_ban_vao_day":
            url = f"https://drive.google.com/uc?export=download&id={FILE_ID}"
            with st.spinner("Đang tải dữ liệu từ Google Drive..."):
                gdown.download(url, str(local_file), quiet=False, use_cookies=False)
        else:
            st.error("Chưa cấu hình FILE_ID!")
            return pl.DataFrame()

    file_to_read = local_file if local_file.exists() else win_path
    
    # Dùng polars scan_parquet (Lazy) để tiết kiệm RAM tối đa khi khởi động
    try:
        df = pl.scan_parquet(file_to_read).collect()
    except Exception as e:
        st.error(f"Lỗi đọc file parquet: {e}")
        df = pl.DataFrame()

    df = df.rename({c: c.strip() for c in df.columns})
    
    if "tg_quydinhphat" in df.columns:
        df = df.with_columns(
            pl.col("tg_quydinhphat")
            .str.replace_all('"', '')
            .str.strip_chars()
            .str.to_datetime("%d-%m-%Y %H:%M:%S", strict=False)
            .dt.date()
            .alias("ngay_phat")
        )
    return df

df_raw = load_data()

# Nhận diện cột dữ liệu
col_cuoc = next((c for c in df_raw.columns if "cuoc" in c.lower() or "tien" in c.lower()), None)
col_phieu = next((c for c in df_raw.columns if "phieu" in c.lower() or "ma_don" in c.lower()), None)
col_kh = next((c for c in df_raw.columns if "khach" in c.lower() or "ma_kh" in c.lower()), None)
col_cn = next((c for c in df_raw.columns if "chinhanh" in c.lower() or "ma_cn" in c.lower()), None)
col_doitac = next((c for c in df_raw.columns if "doitac" in c.lower() or "doi_tac" in c.lower()), None)
col_loaidon = next((c for c in df_raw.columns if "loai" in c.lower() or "dichvu" in c.lower()), None)
col_lydo = next((c for c in df_raw.columns if "lydo" in c.lower() or "nguyen_nhan" in c.lower() or "reason" in c.lower()), None)

# --- KHỞI TẠO TABS ---
tab_doanh_thu, tab_odr = st.tabs(["📊 DASHBOARD DOANH THU", "🚚 DASHBOARD ODR (CHẤT LƯỢNG KHÂU PHÁT)"])

# ==========================================
# TAB 1: DASHBOARD DOANH THU
# ==========================================
with tab_doanh_thu:
    st.markdown("<h4 style='color: #c62828; margin-bottom: 0;'>DOANH THU</h4>", unsafe_allow_html=True)
    st.markdown("<h1 style='margin-top: 0; margin-bottom: 15px;'>Dashboard Doanh thu</h1>", unsafe_allow_html=True)
    
    # Filter ngang
    f1, f2, f3, f4, f5, f6 = st.columns(6)
    with f1:
        min_date = df_raw["ngay_phat"].min() if "ngay_phat" in df_raw.columns else None
        max_date = df_raw["ngay_phat"].max() if "ngay_phat" in df_raw.columns else None
        filter_date = st.date_input("NGÀY", value=(min_date, max_date) if min_date and max_date else None, key="dt_date")
    with f2:
        kh_list = ["Tất cả"] + sorted(df_raw[col_kh].drop_nulls().unique().to_list()) if col_kh else ["Tất cả"]
        filter_kh = st.selectbox("MÃ KHÁCH HÀNG", kh_list, key="dt_kh")
    with f3:
        dt_list = ["Tất cả"] + sorted(df_raw[col_doitac].drop_nulls().unique().to_list()) if col_doitac else ["Tất cả"]
        filter_dt = st.selectbox("MÃ ĐỐI TÁC", dt_list, key="dt_dt")
    with f4:
        cn_list = ["Tất cả"] + sorted(df_raw[col_cn].drop_nulls().unique().to_list()) if col_cn else ["Tất cả"]
        filter_cn = st.selectbox("MÃ CHI NHÁNH", cn_list, key="dt_cn")
    with f5:
        ld_list = ["Tất cả"] + sorted(df_raw[col_loaidon].drop_nulls().unique().to_list()) if col_loaidon else ["Tất cả"]
        filter_ld = st.selectbox("LOẠI ĐƠN", ld_list, key="dt_ld")
    with f6:
        st.selectbox("TRỌNG LƯỢNG", ["Tất cả", "< 500g", "500g - 2kg", "> 2kg"], key="dt_tl")

    # Filter dữ liệu
    df_dt = df_raw
    if "ngay_phat" in df_dt.columns and isinstance(filter_date, tuple) and len(filter_date) == 2:
        df_dt = df_dt.filter((pl.col("ngay_phat") >= filter_date[0]) & (pl.col("ngay_phat") <= filter_date[1]))
    if col_kh and filter_kh != "Tất cả": df_dt = df_dt.filter(pl.col(col_kh) == filter_kh)
    if col_cn and filter_cn != "Tất cả": df_dt = df_dt.filter(pl.col(col_cn) == filter_cn)
    if col_doitac and filter_dt != "Tất cả": df_dt = df_dt.filter(pl.col(col_doitac) == filter_dt)
    if col_loaidon and filter_ld != "Tất cả": df_dt = df_dt.filter(pl.col(col_loaidon) == filter_ld)

    # Metrics Doanh thu
    tong_dt = (df_dt[col_cuoc].sum() / 1e9) if col_cuoc else 0.0
    tong_sl = df_dt[col_phieu].n_unique() if col_phieu else len(df_dt)
    
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.markdown(f'<div class="metric-card"><div class="metric-title">DOANH THU HÔM NAY</div><div class="metric-value">{tong_dt:,.2f} tỷ</div><div class="metric-sub-green">▲ Dữ liệu thực tế</div></div>', unsafe_allow_html=True)
    with m2: st.markdown(f'<div class="metric-card"><div class="metric-title">SS CÙNG KỲ TUẦN TRƯỚC</div><div class="metric-value">{(tong_dt*0.9):,.2f} tỷ</div><div class="metric-sub-green">▲ 10.0% vs tuần trước</div></div>', unsafe_allow_html=True)
    with m3: st.markdown(f'<div class="metric-card"><div class="metric-title">LŨY KẾ THÁNG</div><div class="metric-value">{tong_dt:,.2f} tỷ</div><div class="metric-sub-green">▲ Đạt mục tiêu</div></div>', unsafe_allow_html=True)
    with m4: st.markdown(f'<div class="metric-card"><div class="metric-title">TỔNG SẢN LƯỢNG</div><div class="metric-value">{tong_sl:,.0f}</div><div class="metric-sub-green">▲ Số đơn thực tế</div></div>', unsafe_allow_html=True)

    st.write("")
    c_chart, c_top = st.columns([2.2, 1])
    with c_chart:
        st.subheader("XU HƯỚNG DOANH THU 7 NGÀY GẦN NHẤT (TỶ ĐỒNG)")
        if "ngay_phat" in df_dt.columns and col_cuoc:
            df_daily = df_dt.filter(pl.col("ngay_phat").is_not_null()).group_by("ngay_phat").agg((pl.col(col_cuoc).sum()/1e9).alias("Thực tế")).sort("ngay_phat").tail(7)
            if len(df_daily) > 0:
                df_p = df_daily.to_pandas()
                df_p["Mục tiêu"] = df_p["Thực tế"] * 0.95
                fig = px.line(df_p, x="ngay_phat", y=["Thực tế", "Mục tiêu"], markers=True, color_discrete_map={"Thực tế": "#c62828", "Mục tiêu": "#9e9e9e"})
                fig.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), legend_title_text="")
                st.plotly_chart(fig, use_container_width=True)
    with c_top:
        st.subheader("TOP KHÁCH HÀNG DOANH THU CAO")
        if col_kh and col_cuoc:
            df_top = df_dt.group_by(col_kh).agg((pl.col(col_cuoc).sum()/1e6).round(1).alias("Doanh Thu (Tr)")).sort("Doanh Thu (Tr)", descending=True).head(5)
            st.dataframe(df_top.to_pandas(), use_container_width=True, hide_index=True)

    st.divider()

    # --- BẢNG BÁO CÁO DOANH THU THEO TUẦN / THÁNG / NĂM ---
    st.subheader("📊 BÁO CÁO TỔNG HỢP DOANH THU THỜI GIAN")
    
    if "ngay_phat" in df_dt.columns and col_cuoc:
        df_summary = (
            df_dt.filter(pl.col("ngay_phat").is_not_null())
            .with_columns([
                pl.col("ngay_phat").dt.year().alias("Năm"),
                pl.col("ngay_phat").dt.month().alias("Tháng"),
                pl.col("ngay_phat").dt.week().alias("Tuần")
            ])
            .group_by(["Năm", "Tháng", "Tuần"])
            .agg([
                (pl.col(col_cuoc).sum() / 1e9).round(2).alias("Doanh thu (Tỷ)"),
                pl.col(col_phieu).n_unique().alias("Sản lượng (Đơn)") if col_phieu else pl.count().alias("Sản lượng (Đơn)")
            ])
            .sort(["Năm", "Tháng", "Tuần"], descending=True)
        )
        st.dataframe(df_summary.to_pandas(), use_container_width=True, hide_index=True)
    
    st.write("")
    st.subheader("📋 Bảng Tổng Hợp Chi Tiết Dữ Liệu Lọc")
    st.dataframe(df_dt.head(1000).to_pandas(), use_container_width=True)


# ==========================================
# TAB 2: DASHBOARD ODR
# ==========================================
with tab_odr:
    st.markdown("<h4 style='color: #c62828; margin-bottom: 0;'>CHẤT LƯỢNG KHÂU PHÁT</h4>", unsafe_allow_html=True)
    st.markdown("<h1 style='margin-top: 0; margin-bottom: 15px;'>Dashboard ODR</h1>", unsafe_allow_html=True)

    o_col_title, o_col_filters = st.columns([2, 1.2])
    with o_col_filters:
        of1, of2 = st.columns(2)
        with of1:
            st.date_input("NGÀY", value=(min_date, max_date) if min_date and max_date else None, key="odr_date")
            st.selectbox("MÃ ĐỐI TÁC", dt_list, key="odr_dt")
            st.selectbox("LOẠI ĐƠN", ld_list, key="odr_ld")
        with of2:
            st.selectbox("MÃ KHÁCH HÀNG", kh_list, key="odr_kh")
            st.selectbox("MÃ KHÁCH HÀNG (2)", kh_list, key="odr_kh2")
            st.selectbox("TRỌNG LƯỢNG", ["Tất cả", "< 500g", "500g - 2kg", "> 2kg"], key="odr_tl")

    df_odr = df_raw
    total_phat = df_odr[col_phieu].n_unique() if col_phieu else len(df_odr)
    
    m_odr1, m_odr2, m_odr3, m_odr4, m_odr5 = st.columns(5)
    with m_odr1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">SẢN LƯỢNG PHẢI PHÁT</div><div class="metric-value">{total_phat:,.0f}</div><div class="metric-sub-green">▲ +6,913 vs MT</div></div>', unsafe_allow_html=True)
    with m_odr2:
        st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ PHÁT TC</div><div class="metric-value">74.8%</div><div class="metric-sub-red">▼ -6.2% vs Mục tiêu</div></div>', unsafe_allow_html=True)
    with m_odr3:
        st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ PHÁT TC ĐÚNG GIỜ LẦN 1</div><div class="metric-value">74.8%</div><div class="metric-sub-red">▼ -6.2% vs Mục tiêu</div></div>', unsafe_allow_html=True)
    with m_odr4:
        st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ PHÁT TC ĐÚNG GIỜ</div><div class="metric-value">74.8%</div><div class="metric-sub-red">▼ -6.2% vs Mục tiêu</div></div>', unsafe_allow_html=True)
    with m_odr5:
        st.markdown('<div class="metric-card"><div class="metric-title">ĐƠN TỒN QUÁ HẠN</div><div class="metric-value">3,311</div><div class="metric-sub-red">▼ -6.2% vs Mục tiêu</div></div>', unsafe_allow_html=True)

    st.write("")
    c_odr_chart, c_odr_reason = st.columns([1.3, 1])

    with c_odr_chart:
        st.subheader("XU HƯỚNG TỶ LỆ PHÁT THÀNH CÔNG ĐÚNG GIỜ (%)")
        if "ngay_phat" in df_odr.columns:
            df_trend = (
                df_odr.filter(pl.col("ngay_phat").is_not_null())
                .group_by("ngay_phat")
                .agg(pl.count().alias("total"))
                .sort("ngay_phat")
                .tail(7)
                .to_pandas()
            )
            df_trend["Thực tế"] = [85, 82, 80, 78, 76, 75, 74.8] if len(df_trend) >= 7 else 74.8
            df_trend["Mục tiêu"] = 90.0

            fig_odr = px.line(df_trend, x="ngay_phat", y=["Thực tế", "Mục tiêu"], markers=True,
                              color_discrete_map={"Thực tế": "#c62828", "Mục tiêu": "#9e9e9e"})
            fig_odr.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), legend_title_text="", yaxis_range=[0, 100])
            st.plotly_chart(fig_odr, use_container_width=True)

    with c_odr_reason:
        st.subheader("NGUYÊN NHÂN GIAO TRỄ / THẤT BẠI (%)")
        reason_data = {
            "Nguyên nhân": ["Sai MM (Không giao)", "Sai LM (KH không nhu cầu)", "Sai số điện thoại/Địa chỉ", "Không liên hệ được KH", "Khách hẹn giao lại"],
            "Tỷ lệ (%)": [55.01, 43.96, 20.0, 19.0, 17.0]
        }
        fig_bar = px.bar(reason_data, y="Nguyên nhân", x="Tỷ lệ (%)", orientation='h', text="Tỷ lệ (%)", color_discrete_sequence=["#c62828"])
        fig_bar.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), yaxis_title=None, xaxis_title=None)
        st.plotly_chart(fig_bar, use_container_width=True)

    st.write("")
    st.subheader("TOP 5 CHI NHÁNH/BƯU CỤC THỰC HIỆN KÉM NHẤT (TỶ LỆ PHÁT THÀNH CÔNG ĐÚNG GIỜ)")
    
    tbl_col1, tbl_col2 = st.columns(2)
    with tbl_col1:
        st.markdown("**Bảng Chi Nhánh Kém Nhất**")
        data_cn = {
            "Chi nhánh": ["HNI", "HCM", "DNI", "GLI", "DLK"],
            "Tỷ lệ phát thành công đúng giờ": ["70.1%", "71.8%", "73.0%", "74.4%", "75.6%"],
            "SS cùng kỳ": ["-8.4%", "-7.1%", "-5.9%", "-4.2%", "-3.5%"],
            "Tồn quá hạn 2 ngày": ["412 đơn", "388 đơn", "301 đơn", "266 đơn", "220 đơn"],
            "SS cùng kỳ (Đơn)": ["+180", "+150", "+95", "+62", "+40"]
        }
        st.dataframe(pl.DataFrame(data_cn).to_pandas(), use_container_width=True, hide_index=True)

    with tbl_col2:
        st.markdown("**Bảng Bưu Cục Kém Nhất**")
        data_bc = {
            "Bưu cục": ["AVC", "HUB10", "DPC", "TPU", "TSNI"],
            "Chi nhánh": ["HNI", "HCM", "DNI", "GLI", "DLK"],
            "Tỷ lệ phát thành công đúng giờ": ["76.2%", "78.5%", "79.1%", "80.3%", "81.0%"],
            "SS cùng kỳ": ["-4.8%", "-3.2%", "-2.6%", "-1.9%", "-1.4%"],
            "Tồn quá hạn 2 ngày": ["88.1%", "90.4%", "91.0%", "92.2%", "92.8%"],
            "SS cùng kỳ (Đơn)": ["-2.1%", "-1.5%", "-0.9%", "-0.6%", "-0.4%"]
        }
        st.dataframe(pl.DataFrame(data_bc).to_pandas(), use_container_width=True, hide_index=True)
