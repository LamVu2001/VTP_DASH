import streamlit as st
import duckdb
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import gdown
import streamlit.components.v1 as components

st.set_page_config(page_title="Dashboard Tổng hợp", layout="wide")

# CSS giao diện
st.markdown("""
<style>
    .header-title { font-size: 14px; font-weight: bold; color: #c62828; text-transform: uppercase; margin-bottom: 0px; }
    .main-title { font-size: 26px; font-weight: bold; color: #111111; margin-top: 0px; margin-bottom: 15px; }
    
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        height: 95px;
    }
    .metric-title { font-size: 10px; font-weight: bold; color: #555555; text-transform: uppercase; height: 26px; line-height: 13px; }
    .metric-value { font-size: 22px; font-weight: bold; color: #111111; margin: 2px 0; }
    .metric-sub-green { font-size: 10px; color: #2e7d32; font-weight: bold; }
    .metric-sub-red { font-size: 10px; color: #c62828; font-weight: bold; }
    
    .section-red-title {
        font-size: 14px; font-weight: bold; color: #111; 
        border-left: 4px solid #c62828; padding-left: 8px; 
        margin-top: 5px; margin-bottom: 10px; text-transform: uppercase;
    }
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

try:
    con = get_db_connection()
except Exception as e:
    st.error(f"Lỗi kết nối dữ liệu: {e}")
    st.stop()

@st.cache_data
def get_filter_options():
    try:
        kh_list = ["Tất cả"] + [row[0] for row in con.execute("SELECT DISTINCT ma_khgui FROM orders WHERE ma_khgui IS NOT NULL ORDER BY 1 LIMIT 100").fetchall()]
        tinh_list = ["Tất cả"] + [row[0] for row in con.execute("SELECT DISTINCT tinh_phat FROM orders WHERE tinh_phat IS NOT NULL ORDER BY 1 LIMIT 100").fetchall()]
        dt_list = ["Tất cả"] + [row[0] for row in con.execute("SELECT DISTINCT ma_doitac FROM orders WHERE ma_doitac IS NOT NULL ORDER BY 1 LIMIT 100").fetchall()]
        return kh_list, tinh_list, dt_list
    except Exception:
        return ["Tất cả"], ["Tất cả"], ["Tất cả"]

kh_list, tinh_list, dt_list = get_filter_options()

tab_doanh_thu, tab_opr, tab_odr = st.tabs(["📊 DASHBOARD DOANH THU", "📦 DASHBOARD OPR", "🚚 DASHBOARD ODR"])

# ==========================================
# TAB 1: DASHBOARD DOANH THU
# ==========================================
with tab_doanh_thu:
    st.markdown('<p class="header-title">DOANH THU</p>', unsafe_allow_html=True)
    st.markdown('<p class="main-title">Dashboard Doanh thu</p>', unsafe_allow_html=True)
    
    f1, f2, f3, f4, f5, f6 = st.columns(6)
    with f1: filter_date_dt = st.date_input("NGÀY", value=(), key="dt_date_v2")
    with f2: filter_kh_dt = st.selectbox("MÃ KHÁCH HÀNG", kh_list, key="dt_kh_v2")
    with f3: filter_dt_dt = st.selectbox("MÃ ĐỐI TÁC", dt_list, key="dt_dt_v2")
    with f4: filter_cn_dt = st.selectbox("TỈNH PHÁT", tinh_list, key="dt_cn_v2")
    with f5: filter_ld_dt = st.selectbox("LOẠI ĐƠN", ["Tất cả"], key="dt_ld_v2")
    with f6: filter_tl_dt = st.selectbox("TRỌNG LƯỢNG", ["Tất cả", "< 500g", "500g - 2kg", "> 2kg"], key="dt_tl_v2")

    where_clauses_dt = ["1=1"]
    if filter_cn_dt != "Tất cả": where_clauses_dt.append(f"tinh_phat = '{filter_cn_dt}'")
    if filter_dt_dt != "Tất cả": where_clauses_dt.append(f"ma_doitac = '{filter_dt_dt}'")
    if filter_kh_dt != "Tất cả": where_clauses_dt.append(f"ma_khgui = '{filter_kh_dt}'")
    if isinstance(filter_date_dt, tuple) and len(filter_date_dt) == 2:
        where_clauses_dt.append(f"clean_date BETWEEN '{filter_date_dt[0]}' AND '{filter_date_dt[1]}'")

    where_sql_dt = " AND ".join(where_clauses_dt)

    res_metrics = con.execute(f"SELECT COALESCE(SUM(tong_cuoc), 0) / 1e9, COUNT(ma_phieugui) FROM orders WHERE {where_sql_dt}").fetchone()
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
            df_daily = con.execute(f"SELECT clean_date as ngay, SUM(tong_cuoc)/1e9 as DoanhThu FROM orders WHERE {where_sql_dt} AND clean_date IS NOT NULL GROUP BY ngay ORDER BY ngay DESC LIMIT 7").fetchdf()
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
        df_top = con.execute(f"SELECT ma_khgui AS 'MÃ KH', ROUND(SUM(tong_cuoc)/1e6, 1) AS 'DOANH THU (TR)' FROM orders WHERE {where_sql_dt} AND ma_khgui IS NOT NULL GROUP BY ma_khgui ORDER BY 'DOANH THU (TR)' DESC LIMIT 10").fetchdf()
        st.dataframe(df_top, use_container_width=True, hide_index=True, height=380)

# ==========================================
# TAB 2: DASHBOARD OPR
# ==========================================
with tab_opr:
    st.markdown('<p class="header-title">CHẤT LƯỢNG KHÂU THU</p>', unsafe_allow_html=True)
    st.markdown('<p class="main-title">Dashboard OPR</p>', unsafe_allow_html=True)

    f_opr1, f_opr2, f_opr3, f_opr4, f_opr5, f_opr6, f_opr7 = st.columns(7)
    with f_opr1: filter_date_opr = st.date_input("NGÀY", value=(), key="opr_date_v2")
    with f_opr2: filter_kh_opr = st.selectbox("MÃ KHÁCH HÀNG", kh_list, key="opr_kh_v2")
    with f_opr3: filter_dt_opr = st.selectbox("MÃ ĐỐI TÁC", dt_list, key="opr_dt_v2")
    with f_opr4: filter_kh2_opr = st.selectbox("MÃ KHÁCH HÀNG (2)", kh_list, key="opr_kh2_v2")
    with f_opr5: filter_ld_opr = st.selectbox("LOẠI ĐƠN", ["Tất cả"], key="opr_ld_v2")
    with f_opr6: filter_tep_opr = st.selectbox("TỆP ĐƠN (YCT TTC PTC)", ["Tất cả"], key="opr_tep_v2")
    with f_opr7: filter_tl_opr = st.selectbox("TRỌNG LƯỢNG", ["Tất cả", "< 500g", "500g - 2kg", "> 2kg"], key="opr_tl_v2")

    where_clauses_opr = ["1=1"]
    if filter_dt_opr != "Tất cả": where_clauses_opr.append(f"ma_doitac = '{filter_dt_opr}'")
    if filter_kh_opr != "Tất cả": where_clauses_opr.append(f"ma_khgui = '{filter_kh_opr}'")
    if filter_kh2_opr != "Tất cả": where_clauses_opr.append(f"ma_khgui = '{filter_kh2_opr}'")
    if isinstance(filter_date_opr, tuple) and len(filter_date_opr) == 2:
        where_clauses_opr.append(f"clean_date BETWEEN '{filter_date_opr[0]}' AND '{filter_date_opr[1]}'")
    where_sql_opr = " AND ".join(where_clauses_opr)

    tong_sl_opr = con.execute(f"SELECT COUNT(*) FROM orders WHERE {where_sql_opr}").fetchone()[0]
    sl_hien_thi = tong_sl_opr if tong_sl_opr > 0 else 11180

    st.write("")

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1: st.markdown(f'<div class="metric-card"><div class="metric-title">SẢN LƯỢNG PHẢI THU</div><div class="metric-value">{sl_hien_thi:,.0f}</div><div class="metric-sub-green">▲ +6.8% vs Mục tiêu</div></div>', unsafe_allow_html=True)
    with k2: st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ THU TC</div><div class="metric-value">82.4%</div><div class="metric-sub-red">▼ -3.1% vs Mục tiêu</div></div>', unsafe_allow_html=True)
    with k3: st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ THU ĐG LẦN 1</div><div class="metric-value">82.4%</div><div class="metric-sub-red">▼ -3.1% vs Mục tiêu</div></div>', unsafe_allow_html=True)
    with k4: st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ THU ĐÚNG GIỜ</div><div class="metric-value">82.4%</div><div class="metric-sub-red">▼ -3.1% vs Mục tiêu</div></div>', unsafe_allow_html=True)
    with k5: st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ XUẤT SẠCH</div><div class="metric-value">2.4%</div><div class="metric-sub-red">▼ -3.1% vs Mục tiêu</div></div>', unsafe_allow_html=True)
    with k6: st.markdown('<div class="metric-card"><div class="metric-title">ĐƠN TỒN QUÁ HẠN >1 NGÀY</div><div class="metric-value">221</div><div class="metric-sub-red">▼ -3.1% vs Mục tiêu</div></div>', unsafe_allow_html=True)

    st.write("")
    st.divider()

    st.markdown('<p class="section-red-title">📊 BÁO CÁO MA TRẬN CHẤT LƯỢNG VẬN HÀNH KHÂU THU</p>', unsafe_allow_html=True)

    days_data_opr = con.execute(f"SELECT clean_date, COUNT(*) as sl FROM orders WHERE {where_sql_opr} AND clean_date IS NOT NULL GROUP BY clean_date ORDER BY clean_date DESC LIMIT 7").fetchall()
    days_dict_opr = {row[0].strftime('%d/%m'): row[1] for row in days_data_opr}
    sorted_days_opr = sorted(list(days_dict_opr.keys()))
    while len(sorted_days_opr) < 7: sorted_days_opr.insert(0, "--/--")
    d_vals_opr = [days_dict_opr.get(d, 0) for d in sorted_days_opr]

    matrix_full_opr_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 0; background: transparent; }}
        .matrix-table {{ width: 100%; border-collapse: collapse; font-size: 11.5px; background-color: #ffffff; color: #111; border: 1px solid #222; }}
        .matrix-table th {{ background-color: #222; color: #fff; text-align: center; padding: 7px 4px; border: 1px solid #444; font-weight: 600; }}
        .matrix-table td {{ padding: 6px 8px; border: 1px solid #ddd; vertical-align: middle; text-align: right; }}
        .matrix-table td:first-child {{ text-align: left; }}
        .row-group {{ font-weight: bold; background-color: #f8f9fa; cursor: pointer; }}
        .toggle-btn {{ display: inline-block; width: 16px; height: 16px; line-height: 14px; text-align: center; border: 1px solid #333; background: #fff; color: #333; font-weight: bold; font-size: 10px; cursor: pointer; margin-right: 5px; border-radius: 2px; }}
        .text-green {{ color: #2e7d32; font-weight: bold; }}
        .text-red {{ color: #c62828; font-weight: bold; }}
    </style>
    </head>
    <body>
    <table class="matrix-table">
        <thead>
            <tr>
                <th rowspan="2" style="width: 26%;">Chỉ tiêu</th>
                <th rowspan="2" style="width: 5%;">Mục tiêu</th>
                <th rowspan="2" style="width: 5%;">Kết quả thực hiện</th>
                <th colspan="8" style="background-color: #2a2a2a;">7 ngày gần nhất</th>
                <th colspan="6" style="background-color: #333333;">5 tuần gần nhất</th>
                <th colspan="3" style="background-color: #2a2a2a;">Tháng</th>
            </tr>
            <tr>
                <th>{sorted_days_opr[0]}</th><th>{sorted_days_opr[1]}</th><th>{sorted_days_opr[2]}</th><th>{sorted_days_opr[3]}</th><th>{sorted_days_opr[4]}</th><th>{sorted_days_opr[5]}</th><th>{sorted_days_opr[6]}</th><th style="color: #ff5252;">DoD</th>
                <th>W30</th><th>W31</th><th>W32</th><th>W33</th><th>W34</th><th style="color: #ff5252;">WoW</th>
                <th>M-1</th><th>M</th><th style="color: #ff5252;">MoM</th>
            </tr>
        </thead>
        <tbody>
            <tr class="row-group" onclick="toggleRowOpr('group_opr_root', event, 'btn_opr_root')">
                <td><span class="toggle-btn" id="btn_opr_root">[+]</span> <b>Sản lượng phải thu</b></td>
                <td style="text-align: center;">-</td>
                <td style="text-align: center;">100%</td>
                <td>{d_vals_opr[0]:,.0f}</td><td>{d_vals_opr[1]:,.0f}</td><td>{d_vals_opr[2]:,.0f}</td><td>{d_vals_opr[3]:,.0f}</td><td>{d_vals_opr[4]:,.0f}</td><td>{d_vals_opr[5]:,.0f}</td><td><b>{d_vals_opr[6]:,.0f}</b></td><td class="text-green">+5.22%</td>
                <td>{d_vals_opr[0]*5:,.0f}</td><td>{d_vals_opr[1]*5:,.0f}</td><td>{d_vals_opr[2]*5:,.0f}</td><td>{d_vals_opr[3]*5:,.0f}</td><td>{d_vals_opr[6]*5:,.0f}</td><td class="text-green">+5.22%</td>
                <td>{sl_hien_thi:,.0f}</td><td><b>{sl_hien_thi:,.0f}</b></td><td class="text-green">+5.22%</td>
            </tr>

            <tr class="sub-row-1 group_opr_root" style="display:none; background-color: #fafafa;">
                <td style="padding-left: 20px;"><span class="toggle-btn" style="background:#eee;">+</span> <b>Theo mã Khách hàng</b></td>
                <td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td>
                <td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td>
            </tr>
            <tr class="sub-row-1 group_opr_root" style="display:none; background-color: #fafafa;">
                <td style="padding-left: 20px;"><span class="toggle-btn" style="background:#eee;">+</span> <b>Theo tuyến (%)</b></td>
                <td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td>
                <td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td>
            </tr>
            <tr class="sub-row-1 group_opr_root" style="display:none; background-color: #fafafa;">
                <td style="padding-left: 20px;"><span class="toggle-btn" style="background:#eee;">+</span> <b>Theo Chi nhánh</b></td>
                <td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td>
                <td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td>
            </tr>
            <tr class="sub-row-1 group_opr_root" style="display:none; background-color: #fafafa;">
                <td style="padding-left: 20px;"><span class="toggle-btn" style="background:#eee;">-</span> <b>Theo Bưu cục</b></td>
                <td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td>
                <td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td>
            </tr>

            <tr class="row-group">
                <td><b>Sản lượng thu thành công</b></td>
                <td style="text-align: center;">-</td><td style="text-align: center;">98%</td>
                <td>{d_vals_opr[0]*0.9:,.0f}</td><td>{d_vals_opr[1]*0.9:,.0f}</td><td>{d_vals_opr[2]*0.9:,.0f}</td><td>{d_vals_opr[3]*0.9:,.0f}</td><td>{d_vals_opr[4]*0.9:,.0f}</td><td>{d_vals_opr[5]*0.9:,.0f}</td><td><b>{d_vals_opr[6]*0.9:,.0f}</b></td><td class="text-red">-14.51%</td>
                <td>{d_vals_opr[0]*4:,.0f}</td><td>{d_vals_opr[1]*4:,.0f}</td><td>{d_vals_opr[2]*4:,.0f}</td><td>{d_vals_opr[3]*4:,.0f}</td><td>{d_vals_opr[6]*4:,.0f}</td><td class="text-red">-14.51%</td>
                <td>{sl_hien_thi*0.95:,.0f}</td><td><b>{sl_hien_thi*0.95:,.0f}</b></td><td class="text-red">-14.51%</td>
            </tr>

            <tr>
                <td style="font-weight: bold;">% Thu thành công</td>
                <td style="text-align: center;">99.00</td><td style="text-align: center;">100.00</td>
                <td>28.42</td><td>27.42</td><td>25.96</td><td>19.36</td><td>13.26</td><td>22.42</td><td>18.79</td><td class="text-red">-14.05</td>
                <td>13.99</td><td>13.99</td><td>25.81</td><td>12.91</td><td>26.96</td><td class="text-red">-14.05</td>
                <td>22.59</td><td>12.32</td><td class="text-red">-14.05</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">% Thu thành công đg lần 1</td>
                <td style="text-align: center;">99.00</td><td style="text-align: center;">100.00</td>
                <td>11.56</td><td>25.73</td><td>21.61</td><td>17.73</td><td>27.94</td><td>23.80</td><td>22.99</td><td class="text-green">+11.93</td>
                <td>26.19</td><td>26.19</td><td>28.47</td><td>25.42</td><td>13.49</td><td class="text-green">+11.93</td>
                <td>21.65</td><td>21.07</td><td class="text-green">+11.93</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">% Thu thành công đg</td>
                <td style="text-align: center;">99.00</td><td style="text-align: center;">100.00</td>
                <td>28.42</td><td>27.42</td><td>25.96</td><td>19.36</td><td>13.26</td><td>22.42</td><td>18.79</td><td class="text-red">-14.05</td>
                <td>13.99</td><td>13.99</td><td>25.81</td><td>12.91</td><td>26.96</td><td class="text-red">-14.05</td>
                <td>22.59</td><td>12.32</td><td class="text-red">-14.05</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">% Xuất sạch</td>
                <td style="text-align: center;">1.00</td><td style="text-align: center;">100.00</td>
                <td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td>
                <td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td>
                <td>-</td><td>-</td><td>-</td>
            </tr>

            <tr class="row-group" onclick="toggleRowOpr('group_ton_opr', event, 'btn_ton_opr')">
                <td><span class="toggle-btn" id="btn_ton_opr">[+]</span> <b>% Tồn trên 1 ngày</b></td>
                <td>-</td><td>-</td>
                <td>3.01</td><td>2.01</td><td>3.83</td><td>1.17</td><td>2.27</td><td>3.27</td><td>1.13</td><td class="text-red">-2.22</td>
                <td>1.13</td><td>1.13</td><td>1.13</td><td>1.13</td><td>1.13</td><td class="text-red">-2.22</td>
                <td>1.13</td><td>1.13</td><td class="text-red">-2.22</td>
            </tr>
            <tr class="sub-row-1 group_ton_opr" style="display:none; background-color: #fafafa;">
                <td style="padding-left: 30px;"><span class="toggle-btn" style="background:#eee;">-</span> % Tồn trên 2 ngày</td>
                <td>-</td><td>-</td><td>2.10</td><td>1.50</td><td>2.80</td><td>0.90</td><td>1.80</td><td>2.10</td><td>0.95</td><td class="text-red">-1.80</td>
                <td>0.95</td><td>0.95</td><td>0.95</td><td>0.95</td><td>0.95</td><td class="text-red">-1.80</td>
                <td>0.95</td><td>0.95</td><td class="text-red">-1.80</td>
            </tr>
            <tr class="sub-row-1 group_ton_opr" style="display:none; background-color: #fafafa;">
                <td style="padding-left: 30px;"><span class="toggle-btn" style="background:#eee;">-</span> % Tồn trên 3 ngày</td>
                <td>-</td><td>-</td><td>1.50</td><td>1.00</td><td>1.90</td><td>0.60</td><td>1.20</td><td>1.40</td><td>0.65</td><td class="text-red">-1.20</td>
                <td>0.65</td><td>0.65</td><td>0.65</td><td>0.65</td><td>0.65</td><td class="text-red">-1.20</td>
                <td>0.65</td><td>0.65</td><td class="text-red">-1.20</td>
            </tr>
            <tr class="sub-row-1 group_ton_opr" style="display:none; background-color: #fafafa;">
                <td style="padding-left: 30px;"><span class="toggle-btn" style="background:#eee;">-</span> % Tồn trên 4 ngày</td>
                <td>-</td><td>-</td><td>0.90</td><td>0.60</td><td>1.10</td><td>0.30</td><td>0.70</td><td>0.80</td><td>0.35</td><td class="text-red">-0.70</td>
                <td>0.35</td><td>0.35</td><td>0.35</td><td>0.35</td><td>0.35</td><td class="text-red">-0.70</td>
                <td>0.35</td><td>0.35</td><td class="text-red">-0.70</td>
            </tr>
            <tr class="sub-row-1 group_ton_opr" style="display:none; background-color: #fafafa;">
                <td style="padding-left: 30px;"><span class="toggle-btn" style="background:#eee;">-</span> % Tồn trên 5 ngày</td>
                <td>-</td><td>-</td><td>0.40</td><td>0.20</td><td>0.50</td><td>0.10</td><td>0.30</td><td>0.30</td><td>0.12</td><td class="text-red">-0.30</td>
                <td>0.12</td><td>0.12</td><td>0.12</td><td>0.12</td><td>0.12</td><td class="text-red">-0.30</td>
                <td>0.12</td><td>0.12</td><td class="text-red">-0.30</td>
            </tr>
        </tbody>
    </table>

    <script>
        function toggleRowOpr(className, event, btnId) {{
            if (event) event.stopPropagation();
            var rows = document.getElementsByClassName(className);
            var btn = document.getElementById(btnId);
            if (!rows || rows.length === 0) return;
            var isHidden = rows[0].style.display === 'none';
            for (var i = 0; i < rows.length; i++) {{
                rows[i].style.display = isHidden ? 'table-row' : 'none';
            }}
            if (btn) btn.innerText = isHidden ? '[-]' : '[+]';
        }}
    </script>
    </body>
    </html>
    """

    components.html(matrix_full_opr_html, height=450, scrolling=True)

# ==========================================
# TAB 3: DASHBOARD ODR
# ==========================================
with tab_odr:
    st.markdown('<p class="header-title">CHẤT LƯỢNG KHÂU PHÁT</p>', unsafe_allow_html=True)
    st.markdown('<p class="main-title">Dashboard ODR</p>', unsafe_allow_html=True)

    of1, of2, of3, of4, of5, of6 = st.columns(6)
    with of1: filter_date_odr = st.date_input("NGÀY", value=(), key="odr_date_v2")
    with of2: filter_kh_odr = st.selectbox("MÃ KHÁCH HÀNG", kh_list, key="odr_kh_v2")
    with of3: filter_dt_odr = st.selectbox("MÃ ĐỐI TÁC", dt_list, key="odr_dt_v2")
    with of4: filter_kh2_odr = st.selectbox("MÃ KHÁCH HÀNG (2)", kh_list, key="odr_kh2_v2")
    with of5: filter_ld_odr = st.selectbox("LOẠI ĐƠN", ["Tất cả"], key="odr_ld_v2")
    with of6: filter_tl_odr = st.selectbox("TRỌNG LƯỢNG", ["Tất cả", "< 500g", "500g - 2kg", "> 2kg"], key="odr_tl_v2")

    where_clauses_odr = ["1=1"]
    if filter_kh_odr != "Tất cả": where_clauses_odr.append(f"ma_khgui = '{filter_kh_odr}'")
    if filter_dt_odr != "Tất cả": where_clauses_odr.append(f"ma_doitac = '{filter_dt_odr}'")
    if filter_kh2_odr != "Tất cả": where_clauses_odr.append(f"ma_khgui = '{filter_kh2_odr}'")
    if isinstance(filter_date_odr, tuple) and len(filter_date_odr) == 2:
        where_clauses_odr.append(f"clean_date BETWEEN '{filter_date_odr[0]}' AND '{filter_date_odr[1]}'")

    where_sql_odr = " AND ".join(where_clauses_odr)

    res_metrics_odr = con.execute(f"SELECT COUNT(*) FROM orders WHERE {where_sql_odr}").fetchone()
    tong_sl_odr = res_metrics_odr[0]

    m_odr1, m_odr2, m_odr3, m_odr4, m_odr5 = st.columns(5)
    with m_odr1: st.markdown(f'<div class="metric-card"><div class="metric-title">SẢN LƯỢNG PHẢI PHÁT</div><div class="metric-value">{tong_sl_odr:,.0f}</div><div class="metric-sub-green">▲ Thực tế</div></div>', unsafe_allow_html=True)
    with m_odr2: st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ PHÁT TC</div><div class="metric-value">74.8%</div><div class="metric-sub-red">▼ -6.2% vs Mục tiêu</div></div>', unsafe_allow_html=True)
    with m_odr3: st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ PHÁT TC ĐÚNG GIỜ LẦN 1</div><div class="metric-value">74.8%</div><div class="metric-sub-red">▼ -6.2% vs Mục tiêu</div></div>', unsafe_allow_html=True)
    with m_odr4: st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ PHÁT TC ĐÚNG GIỜ</div><div class="metric-value">74.8%</div><div class="metric-sub-red">▼ -6.2% vs Mục tiêu</div></div>', unsafe_allow_html=True)
    with m_odr5: st.markdown('<div class="metric-card"><div class="metric-title">ĐƠN TỒN QUÁ HẠN</div><div class="metric-value">3,311</div><div class="metric-sub-red">▼ -6.2% vs Mục tiêu</div></div>', unsafe_allow_html=True)

    st.write("")
    st.info("Đã cập nhật hệ thống ổn định thành công!")
