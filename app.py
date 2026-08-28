import streamlit as st
import duckdb
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import gdown
import streamlit.components.v1 as components

# =======================================================================================================================================
# CẤU HÌNH TRANG STREAMLIT
# =======================================================================================================================================
st.set_page_config(page_title="Dashboard Health Score", layout="wide")

st.markdown("""
<style>
    /* Tiêu đề chính trên cùng (Full các tab) - TO NỔI BẬT */
    .top-header-title {
        font-size: 34px;
        font-weight: 900;
        color: #c62828;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-top: -15px;
        margin-bottom: 15px;
        padding-bottom: 5px;
    }
    
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

st.markdown('<div class="top-header-title">HEALTH SCORE DASHBOARD</div>', unsafe_allow_html=True)

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

tab_overview, tab_doanh_thu, tab_opr, tab_odr , tab_sla = st.tabs(["OVERVIEW", "📊 DOANH THU", "📦 OPR", "🚚 ODR", "SLA"])

# =======================================================================================================================================
# TAB 1: OVERVIEW
# =======================================================================================================================================
with tab_overview:
    st.markdown('<div style="height: 3px; background-color: #c62828; margin-bottom: 20px;"></div>', unsafe_allow_html=True)
    dt_rows = con.execute("""
        SELECT DISTINCT ma_doitac 
        FROM orders 
        WHERE ma_doitac IS NOT NULL AND TRIM(CAST(ma_doitac AS VARCHAR)) != ''
        ORDER BY ma_doitac ASC
    """).fetchall()

    if dt_rows:
        all_doitac = [str(r[0]) for r in dt_rows]
    else:
        all_doitac = ["TIKTOK", "SHOPEE", "KH813", "TMM13", "TTQ123", "TTQ124", "TTQ125", "TTQ126", "TTQ127", "TTQ128"]

    list_doitac = all_doitac[:10]

    mock_data = [
        ("bg-green", "c-green", "1.1%", "+6.8%", "91.2%", "92.5%", "96.8%", "TỐT"),
        ("bg-yellow", "c-yellow", "2.1%", "-3.4%", "85.6%", "88.9%", "93.1%", "CẢNH BÁO"),
        ("bg-red", "c-red", "4.8%", "-14.5%", "74.2%", "82.1%", "79.5%", "RỦI RO"),
        ("bg-green", "c-green", "0.9%", "+10.4%", "93.4%", "94.0%", "95.2%", "TỐT"),
        ("bg-yellow", "c-yellow", "1.8%", "+5.8%", "86.3%", "91.0%", "92.4%", "CẢNH BÁO"),
        ("bg-red", "c-red", "3.4%", "-10.3%", "78.1%", "74.8%", "85.0%", "RỦI RO"),
        ("bg-yellow", "c-yellow", "2.4%", "-0.6%", "84.2%", "85.9%", "87.1%", "CẢNH BÁO"),
        ("bg-yellow", "c-yellow", "1.6%", "+3.7%", "89.9%", "92.1%", "90.5%", "CẢNH BÁO"),
        ("bg-green", "c-green", "0.7%", "+13.7%", "95.1%", "96.3%", "97.0%", "TỐT"),
        ("bg-red", "c-red", "3.1%", "+1.6%", "81.4%", "76.2%", "79.8%", "RỦI RO"),
    ]

    table_rows_html = ""
    for idx, doitac in enumerate(list_doitac):
        m = mock_data[idx % len(mock_data)]
        table_rows_html += f"""
        <tr class="{m[0]}">
            <td style="text-align: left; padding-left: 10px;"><b>{doitac}</b></td>
            <td>100</td><td>22.30</td><td>22.30</td>
            <td class="{m[1]}">{m[2]}</td><td class="{m[1]}">{m[3]}</td>
            <td class="{m[1]}">{m[4]}</td><td class="{m[1]}">{m[5]}</td>
            <td class="{m[1]}">{m[6]}</td><td class="{m[1]}">{m[7]}</td>
        </tr>
        """

    html_overview = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        * {{ box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
        body {{ margin: 0; padding: 0; background-color: transparent; color: #111; }}

        .kpi-container {{ display: flex; gap: 16px; margin-bottom: 20px; }}
        .kpi-card {{ flex: 1; background: #ffffff; border: 1px solid #e0e0e0; border-radius: 6px; padding: 12px 16px; display: flex; justify-content: space-between; align-items: flex-end; box-shadow: 0 1px 3px rgba(0,0,0,0.03); }}
        .card-black {{ border-left: 5px solid #222222; }}
        .card-green {{ border-left: 5px solid #1b5e20; }}
        .card-yellow {{ border-left: 5px solid #b78103; }}
        .card-red {{ border-left: 5px solid #c62828; }}

        .kpi-title {{ font-size: 11px; font-weight: 800; color: #444; text-transform: uppercase; }}
        .kpi-val {{ font-size: 36px; font-weight: 800; line-height: 1; margin-top: 8px; }}
        .kpi-sub {{ font-size: 11px; color: #777; font-weight: 500; }}

        .v-black {{ color: #222; }}
        .v-green {{ color: #1b5e20; }}
        .v-yellow {{ color: #b78103; }}
        .v-red {{ color: #c62828; }}

        .bracket-wrapper {{ position: relative; width: 100%; height: 28px; }}
        .bracket-box {{ position: absolute; right: 11.2%; width: 29.8%; border-top: 1.5px solid #4a7ebb; border-left: 1.5px solid #4a7ebb; border-right: 1.5px solid #4a7ebb; height: 12px; top: 12px; text-align: center; }}
        .bracket-text {{ position: relative; top: -10px; background: #ffffff; padding: 0 10px; font-size: 11px; font-weight: 700; color: #2b547e; display: inline-block; }}

        .tbl-main {{ width: 100%; border-collapse: collapse; font-size: 11px; text-align: center; }}
        .tbl-main th {{ background-color: #222222; color: #ffffff; padding: 9px 4px; font-weight: 700; border: 1px solid #333333; }}
        .tbl-main th.th-red {{ background-color: #b71c1c; }}
        .tbl-main td {{ padding: 7px 4px; border: 1px solid #e2e8f0; font-weight: 600; }}

        .bg-green {{ background-color: #e8f5e9; }}
        .bg-yellow {{ background-color: #fffde7; }}
        .bg-red {{ background-color: #fbe9e7; }}

        .c-green {{ color: #2e7d32; font-weight: 700; }}
        .c-yellow {{ color: #b78103; font-weight: 700; }}
        .c-red {{ color: #c62828; font-weight: 700; }}

        .legend-wrapper {{ display: flex; gap: 20px; margin-top: 12px; }}
        .tbl-legend {{ flex: 1; border-collapse: collapse; font-size: 10.5px; }}
        .tbl-legend th {{ background-color: #222222; color: #ffffff; padding: 6px; border: 1px solid #333; font-weight: 700; }}
        .tbl-legend td {{ padding: 6px 8px; border: 1px solid #e2e8f0; }}
    </style>
    </head>
    <body>
        <div class="kpi-container">
            <div class="kpi-card card-black">
                <div><div class="kpi-title">TỔNG KH THEO DÕI</div><div class="kpi-val v-black">{len(all_doitac)}</div></div>
                <div class="kpi-sub">Lấy trực tiếp từ ma_doitac</div>
            </div>
            <div class="kpi-card card-green">
                <div><div class="kpi-title" style="color: #1b5e20;">ỔN ĐỊNH (XANH)</div><div class="kpi-val v-green">20</div></div>
                <div class="kpi-sub">Đạt mục tiêu</div>
            </div>
            <div class="kpi-card card-yellow">
                <div><div class="kpi-title" style="color: #b78103;">CẢNH BÁO (VÀNG)</div><div class="kpi-val v-yellow">7</div></div>
                <div class="kpi-sub">Cần theo dõi sát</div>
            </div>
            <div class="kpi-card card-red">
                <div><div class="kpi-title" style="color: #c62828;">RỦI RO (ĐỎ)</div><div class="kpi-val v-red">3</div></div>
                <div class="kpi-sub">Cần xử lý ngay</div>
            </div>
        </div>

        <div class="bracket-wrapper">
            <div class="bracket-box"><span class="bracket-text">Thực hiện trung bình 7 ngày gần nhất</span></div>
        </div>

        <table class="tbl-main">
            <thead>
                <tr>
                    <th style="width: 12%;">Mã Khách hàng</th>
                    <th style="width: 10%;">Doanh thu<br>mục tiêu FM</th>
                    <th style="width: 9%;">Doanh thu<br>D</th>
                    <th style="width: 9%;">Doanh thu<br>MTD</th>
                    <th style="width: 10%;">% Doanh thu<br>MTD/mục tiêu</th>
                    <th style="width: 9%;">Doanh thu<br>Δ WTD</th>
                    <th style="width: 9.9%;">OPR (%)</th>
                    <th style="width: 9.9%;">ODR (%)</th>
                    <th style="width: 10%;">FD (%)</th>
                    <th class="th-red" style="width: 11.2%;">Sức khỏe Khách hàng</th>
                </tr>
            </thead>
            <tbody>
                {table_rows_html}
            </tbody>
        </table>

        <div class="legend-wrapper">
            <table class="tbl-legend">
                <thead><tr><th style="width: 30%;">CẢNH BÁO</th><th style="width: 70%;">RULE</th></tr></thead>
                <tbody>
                    <tr class="bg-green"><td class="c-green">Xanh - tốt</td><td>Chỉ số thực hiện lớn hơn so với mục tiêu</td></tr>
                    <tr class="bg-yellow"><td class="c-yellow">Vàng – cảnh báo</td><td>Chỉ số thực hiện thực hiện ở mức 80 – 99.99% so với mục tiêu</td></tr>
                    <tr class="bg-red"><td class="c-red">Đỏ - rủi ro</td><td>Chỉ số thực hiện thực hiện dưới mức 80% so với mục tiêu</td></tr>
                </tbody>
            </table>
            <table class="tbl-legend">
                <thead><tr><th style="width: 25%;">CẢNH BÁO</th><th style="width: 75%;">RULE</th></tr></thead>
                <tbody>
                    <tr class="bg-green"><td class="c-green">TỐT</td><td>Cả 4 chỉ số (Doanh thu, OPR, ODR, FD) đều ở mức Xanh</td></tr>
                    <tr class="bg-yellow"><td class="c-yellow">CẢNH BÁO</td><td>Có ít nhất 1 chỉ số ở mức Vàng, và không có chỉ số nào ở mức Đỏ</td></tr>
                    <tr class="bg-red"><td class="c-red">RỦI RO</td><td>Có ít nhất 1 chỉ số ở mức Đỏ (worst-of theo bảng ngưỡng RAG)</td></tr>
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    components.html(html_overview, height=620, scrolling=False)

    st.markdown("<br>", unsafe_allow_html=True)

    preset_positions = [
        {"x": 0.35,  "y": 0.85,  "color": "#1b5e20"}, 
        {"x": -0.12, "y": 0.15,  "color": "#c66900"}, 
        {"x": -0.80, "y": -0.65, "color": "#c62828"}, 
        {"x": 0.60,  "y": 0.90,  "color": "#1b5e20"}, 
        {"x": 0.30,  "y": 0.20,  "color": "#c66900"}, 
        {"x": -0.55, "y": -0.90, "color": "#c62828"}, 
        {"x": -0.05, "y": 0.00,  "color": "#c66900"}, 
        {"x": 0.15,  "y": 0.28,  "color": "#c66900"}, 
        {"x": 0.78,  "y": 0.95,  "color": "#1b5e20"}, 
        {"x": 0.10,  "y": -0.75, "color": "#c62828"}, 
    ]

    x_coords, y_coords, text_labels, point_colors = [], [], [], []

    for idx, dt_name in enumerate(all_doitac):
        pos = preset_positions[idx % len(preset_positions)]
        x_coords.append(pos["x"])
        y_coords.append(pos["y"])
        text_labels.append(dt_name)
        point_colors.append(pos["color"])

    fig = go.Figure()

    fig.add_shape(type="rect", x0=0, y0=0, x1=1, y1=1, fillcolor="#edf7ed", layer="below", line_width=0)
    fig.add_shape(type="rect", x0=-1, y0=0, x1=0, y1=1, fillcolor="#f4fbf4", layer="below", line_width=0)
    fig.add_shape(type="rect", x0=-1, y0=-1, x1=0, y1=0, fillcolor="#fdebed", layer="below", line_width=0)
    fig.add_shape(type="rect", x0=0, y0=-1, x1=1, y1=0, fillcolor="#fff8ec", layer="below", line_width=0)

    fig.add_shape(type="line", x0=0, y0=-1, x1=0, y1=1, line=dict(color="#999999", width=1.5, dash="dash"))
    fig.add_shape(type="line", x0=-1, y0=0, x1=1, y1=0, line=dict(color="#999999", width=1.5, dash="dash"))

    fig.add_annotation(x=0.5, y=0.92, text="<b>KHÁCH HÀNG KHỎE MẠNH</b>", showarrow=False, font=dict(color="#1b5e20", size=13))
    fig.add_annotation(x=-0.5, y=0.92, text="<b>THEO DÕI — CHỜ PHỤC HỒI</b>", showarrow=False, font=dict(color="#1b5e20", size=13))
    fig.add_annotation(x=-0.5, y=-0.15, text="<b>ƯU TIÊN XỬ LÝ NGAY</b>", showarrow=False, font=dict(color="#c62828", size=13))
    fig.add_annotation(x=0.5, y=-0.15, text="<b>CƠ HỘI CẢI THIỆN DỊCH VỤ</b>", showarrow=False, font=dict(color="#b78103", size=13))

    fig.add_trace(go.Scatter(
        x=x_coords,
        y=y_coords,
        mode='markers+text',
        text=text_labels,
        textposition='bottom center',
        textfont=dict(size=10, color='black', family='Arial Black'),
        marker=dict(
            size=22,
            color=point_colors,
            line=dict(color='white', width=1)
        ),
        hoverinfo='text'
    ))

    fig.update_layout(
        xaxis=dict(
            title="<b>BIẾN ĐỘNG DOANH THU MTD vs CÙNG KỲ THÁNG TRƯỚC (MoM)</b>",
            range=[-1, 1],
            showgrid=False,
            zeroline=False,
            showticklabels=False
        ),
        yaxis=dict(
            title="<b>ĐIỂM CL (OPR 20% · ODR 50% · FD 30%)</b>",
            range=[-1, 1],
            showgrid=False,
            zeroline=False,
            showticklabels=False
        ),
        margin=dict(l=40, r=40, t=20, b=40),
        height=540,
        plot_bgcolor="white",
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

# =======================================================================================================================================
# TAB 2: DASHBOARD DOANH THU
# =======================================================================================================================================
with tab_doanh_thu:
    st.markdown('<div style="height: 3px; background-color: #c62828; margin-bottom: 20px;"></div>', unsafe_allow_html=True)
    
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
        SELECT COALESCE(SUM(tong_cuoc), 0) / 1e9, COUNT(ma_phieugui)
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

    st.subheader("📊 BÁO CÁO MA TRẬN DOANH THU & SẢN LƯỢNG")

    days_data_dt = con.execute(f"""
        SELECT clean_date, SUM(tong_cuoc)/1e9 as dt, COUNT(ma_phieugui) as sl 
        FROM orders WHERE {where_sql_dt} AND clean_date IS NOT NULL 
        GROUP BY clean_date ORDER BY clean_date DESC LIMIT 7
    """).fetchall()

    days_dt_dict = {row[0].strftime('%d/%m'): (row[1], row[2]) for row in days_data_dt}
    sorted_days_dt = sorted(list(days_dt_dict.keys()))
    while len(sorted_days_dt) < 7:
        sorted_days_dt.insert(0, "--/--")
    d_dt_vals = [days_dt_dict.get(d, (0, 0))[0] for d in sorted_days_dt]
    d_sl_vals = [days_dt_dict.get(d, (0, 0))[1] for d in sorted_days_dt]

    tree_raw_data = con.execute(f"""
        SELECT 
            COALESCE(ma_doitac, 'Khác') as dt,
            COALESCE(ma_khgui, 'Khác') as kh,
            COALESCE(tinh_phat, 'Khác') as tinh,
            COALESCE(ma_buucuc_phat, 'Khác') as bc,
            SUM(tong_cuoc)/1e9 as tong_dt,
            COUNT(ma_phieugui) as tong_sl
        FROM orders 
        WHERE {where_sql_dt}
        GROUP BY ma_doitac, ma_khgui, tinh_phat, ma_buucuc_phat
        ORDER BY dt, tong_dt DESC
    """).fetchall()

    dt_structure = {}
    for dt, kh, tinh, bc, dt_val, sl_val in tree_raw_data:
        if dt not in dt_structure:
            dt_structure[dt] = {'dt': 0, 'sl': 0, 'khs': {}, 'tinhs': {}}
        dt_structure[dt]['dt'] += dt_val
        dt_structure[dt]['sl'] += sl_val

        if kh not in dt_structure[dt]['khs']:
            dt_structure[dt]['khs'][kh] = {'dt': 0, 'sl': 0}
        dt_structure[dt]['khs'][kh]['dt'] += dt_val
        dt_structure[dt]['khs'][kh]['sl'] += sl_val

        if tinh not in dt_structure[dt]['tinhs']:
            dt_structure[dt]['tinhs'][tinh] = {'dt': 0, 'sl': 0, 'bcs': {}}
        dt_structure[dt]['tinhs'][tinh]['dt'] += dt_val
        dt_structure[dt]['tinhs'][tinh]['sl'] += sl_val

        dt_structure[dt]['tinhs'][tinh]['bcs'][bc] = {'dt': dt_val, 'sl': sl_val}

    tinh_raw_data = con.execute(f"""
        SELECT 
            COALESCE(tinh_phat, 'Khác') as tinh,
            COALESCE(ma_buucuc_phat, 'Khác') as bc,
            SUM(tong_cuoc)/1e9 as tong_dt,
            COUNT(ma_phieugui) as tong_sl
        FROM orders 
        WHERE {where_sql_dt}
        GROUP BY tinh_phat, ma_buucuc_phat
        ORDER BY tong_dt DESC
    """).fetchall()

    tinh_independent_struct = {}
    for tinh, bc, dt_val, sl_val in tinh_raw_data:
        if tinh not in tinh_independent_struct:
            tinh_independent_struct[tinh] = {'dt': 0, 'sl': 0, 'bcs': {}}
        tinh_independent_struct[tinh]['dt'] += dt_val
        tinh_independent_struct[tinh]['sl'] += sl_val
        tinh_independent_struct[tinh]['bcs'][bc] = {'dt': dt_val, 'sl': sl_val}

    def generate_matrix_rows(is_doanh_thu=True):
        rows_html = ""
        prefix = "dt_sec" if is_doanh_thu else "sl_sec"
        fmt = lambda v: f"{v:.2f}" if is_doanh_thu else f"{v//1:,.0f}"

        for idx_dt, (dt_name, dt_data) in enumerate(dt_structure.items()):
            val_dt = dt_data['dt'] if is_doanh_thu else dt_data['sl']
            dt_clean_id = f"{prefix}_{idx_dt}"

            rows_html += f"""
            <tr class="sub-row-1 group_{prefix}_root" style="display:none; background-color: #f4f6f8; font-weight:600;" onclick="toggleRow('{dt_clean_id}', event, 'btn_{dt_clean_id}')">
                <td style="padding-left: 20px;"><span class="toggle-btn" id="btn_{dt_clean_id}">[+]</span> Đối tác: <b>{dt_name}</b></td>
                <td>10</td><td>100.00</td>
                <td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td class="text-green">+6.8%</td>
                <td>{fmt(val_dt)}</td><td>{fmt(val_dt)}</td><td>{fmt(val_dt)}</td><td>{fmt(val_dt)}</td><td>{fmt(val_dt)}</td><td class="text-green">+6.8%</td>
                <td>{fmt(val_dt)}</td><td>{fmt(val_dt)}</td><td class="text-green">+6.8%</td>
                <td>{"10" if is_doanh_thu else "-"}</td><td class="text-green">{"Wait" if is_doanh_thu else "-"}</td>
            </tr>
            """

            kh_group_id = f"{dt_clean_id}_kh_grp"
            rows_html += f"""
            <tr class="sub-row-2 {dt_clean_id}" style="display:none; background-color: #ffffff; font-weight:600; color: #1565c0;" onclick="toggleRow('{kh_group_id}', event, 'btn_{kh_group_id}')">
                <td style="padding-left: 40px;"><span class="toggle-btn" id="btn_{kh_group_id}">[+]</span> <b>THEO MÃ KHÁCH HÀNG</b></td>
                <td>-</td><td>-</td>
                <td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td class="text-green">+6.8%</td>
                <td>{fmt(val_dt)}</td><td>{fmt(val_dt)}</td><td>{fmt(val_dt)}</td><td>{fmt(val_dt)}</td><td>{fmt(val_dt)}</td><td class="text-green">+6.8%</td>
                <td>{fmt(val_dt)}</td><td>{fmt(val_dt)}</td><td class="text-green">+6.8%</td>
                <td>-</td><td>-</td>
            </tr>
            """
            for kh_name, kh_data in dt_data['khs'].items():
                val_kh = kh_data['dt'] if is_doanh_thu else kh_data['sl']
                rows_html += f"""
                <tr class="sub-row-3 {kh_group_id}" style="display:none; background-color: #ffffff; color: #333;">
                    <td style="padding-left: 60px;">• Mã KH: <b>{kh_name}</b></td>
                    <td>10</td><td>100.00</td>
                    <td>{fmt(val_kh/7)}</td><td>{fmt(val_kh/7)}</td><td>{fmt(val_kh/7)}</td><td>{fmt(val_kh/7)}</td><td>{fmt(val_kh/7)}</td><td>{fmt(val_kh/7)}</td><td>{fmt(val_kh/7)}</td><td class="text-green">+6.8%</td>
                    <td>{fmt(val_kh)}</td><td>{fmt(val_kh)}</td><td>{fmt(val_kh)}</td><td>{fmt(val_kh)}</td><td>{fmt(val_kh)}</td><td class="text-green">+6.8%</td>
                    <td>{fmt(val_kh)}</td><td>{fmt(val_kh)}</td><td class="text-green">+6.8%</td>
                    <td>{"10" if is_doanh_thu else "-"}</td><td class="text-green">{"Wait" if is_doanh_thu else "-"}</td>
                </tr>
                """

            tinh_group_id = f"{dt_clean_id}_tinh_grp"
            rows_html += f"""
            <tr class="sub-row-2 {dt_clean_id}" style="display:none; background-color: #ffffff; font-weight:600; color: #2e7d32;" onclick="toggleRow('{tinh_group_id}', event, 'btn_{tinh_group_id}')">
                <td style="padding-left: 40px;"><span class="toggle-btn" id="btn_{tinh_group_id}">[+]</span> <b>THEO TỈNH PHÁT</b></td>
                <td>-</td><td>-</td>
                <td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td class="text-green">+6.8%</td>
                <td>{fmt(val_dt)}</td><td>{fmt(val_dt)}</td><td>{fmt(val_dt)}</td><td>{fmt(val_dt)}</td><td>{fmt(val_dt)}</td><td class="text-green">+6.8%</td>
                <td>{fmt(val_dt)}</td><td>{fmt(val_dt)}</td><td class="text-green">+6.8%</td>
                <td>-</td><td>-</td>
            </tr>
            """
            for idx_tinh, (tinh_name, tinh_data) in enumerate(dt_data['tinhs'].items()):
                val_tinh = tinh_data['dt'] if is_doanh_thu else tinh_data['sl']
                tinh_sub_id = f"{tinh_group_id}_tinh_{idx_tinh}"

                rows_html += f"""
                <tr class="sub-row-3 {tinh_group_id}" style="display:none; background-color: #fcfcfc; color: #2e7d32;" onclick="toggleRow('{tinh_sub_id}', event, 'btn_{tinh_sub_id}')">
                    <td style="padding-left: 60px;"><span class="toggle-btn" id="btn_{tinh_sub_id}">[+]</span> Tỉnh phát: <b>{tinh_name}</b></td>
                    <td>10</td><td>100.00</td>
                    <td>{fmt(val_tinh/7)}</td><td>{fmt(val_tinh/7)}</td><td>{fmt(val_tinh/7)}</td><td>{fmt(val_tinh/7)}</td><td>{fmt(val_tinh/7)}</td><td>{fmt(val_tinh/7)}</td><td>{fmt(val_tinh/7)}</td><td class="text-green">+6.8%</td>
                    <td>{fmt(val_tinh)}</td><td>{fmt(val_tinh)}</td><td>{fmt(val_tinh)}</td><td>{fmt(val_tinh)}</td><td>{fmt(val_tinh)}</td><td class="text-green">+6.8%</td>
                    <td>{fmt(val_tinh)}</td><td>{fmt(val_tinh)}</td><td class="text-green">+6.8%</td>
                    <td>{"10" if is_doanh_thu else "-"}</td><td class="text-green">{"Wait" if is_doanh_thu else "-"}</td>
                </tr>
                """

                for bc_name, bc_data in tinh_data['bcs'].items():
                    val_bc = bc_data['dt'] if is_doanh_thu else bc_data['sl']
                    rows_html += f"""
                    <tr class="sub-row-4 {tinh_sub_id}" style="display:none; background-color: #fafafa; font-style: italic; color: #555;">
                        <td style="padding-left: 80px;">• Bưu cục phát: <b>{bc_name}</b></td>
                        <td>10</td><td>100.00</td>
                        <td>{fmt(val_bc/7)}</td><td>{fmt(val_bc/7)}</td><td>{fmt(val_bc/7)}</td><td>{fmt(val_bc/7)}</td><td>{fmt(val_bc/7)}</td><td>{fmt(val_bc/7)}</td><td>{fmt(val_bc/7)}</td><td class="text-green">+6.8%</td>
                        <td>{fmt(val_bc)}</td><td>{fmt(val_bc)}</td><td>{fmt(val_bc)}</td><td>{fmt(val_bc)}</td><td>{fmt(val_bc)}</td><td class="text-green">+6.8%</td>
                        <td>{fmt(val_bc)}</td><td>{fmt(val_bc)}</td><td class="text-green">+6.8%</td>
                        <td>{"10" if is_doanh_thu else "-"}</td><td class="text-green">{"Wait" if is_doanh_thu else "-"}</td>
                    </tr>
                    """

        tinh_root_id = f"{prefix}_tinh_independent_root"
        tot_tinh_val = sum(t['dt'] if is_doanh_thu else t['sl'] for t in tinh_independent_struct.values())
        rows_html += f"""
        <tr class="sub-row-1 group_{prefix}_root" style="display:none; background-color: #e8f5e9; font-weight:bold; color: #2e7d32;" onclick="toggleRow('{tinh_root_id}', event, 'btn_{tinh_root_id}')">
            <td style="padding-left: 20px;"><span class="toggle-btn" id="btn_{tinh_root_id}">[+]</span> <b>TỈNH PHÁT</b></td>
            <td>-</td><td>-</td>
            <td>{fmt(tot_tinh_val/7)}</td><td>{fmt(tot_tinh_val/7)}</td><td>{fmt(tot_tinh_val/7)}</td><td>{fmt(tot_tinh_val/7)}</td><td>{fmt(tot_tinh_val/7)}</td><td>{fmt(tot_tinh_val/7)}</td><td>{fmt(tot_tinh_val/7)}</td><td class="text-green">+6.8%</td>
            <td>{fmt(tot_tinh_val)}</td><td>{fmt(tot_tinh_val)}</td><td>{fmt(tot_tinh_val)}</td><td>{fmt(tot_tinh_val)}</td><td>{fmt(tot_tinh_val)}</td><td class="text-green">+6.8%</td>
            <td>{fmt(tot_tinh_val)}</td><td>{fmt(tot_tinh_val)}</td><td class="text-green">+6.8%</td>
            <td>-</td><td>-</td>
        </tr>
        """

        for idx_tinh, (tinh_name, tinh_data) in enumerate(tinh_independent_struct.items()):
            val_tinh = tinh_data['dt'] if is_doanh_thu else tinh_data['sl']
            tinh_ind_clean_id = f"{tinh_root_id}_t_{idx_tinh}"

            rows_html += f"""
            <tr class="sub-row-2 {tinh_root_id}" style="display:none; background-color: #ffffff; color: #2e7d32;" onclick="toggleRow('{tinh_ind_clean_id}', event, 'btn_{tinh_ind_clean_id}')">
                <td style="padding-left: 40px;"><span class="toggle-btn" id="btn_{tinh_ind_clean_id}">[+]</span> Tỉnh phát: <b>{tinh_name}</b></td>
                <td>10</td><td>100.00</td>
                <td>{fmt(val_tinh/7)}</td><td>{fmt(val_tinh/7)}</td><td>{fmt(val_tinh/7)}</td><td>{fmt(val_tinh/7)}</td><td>{fmt(val_tinh/7)}</td><td>{fmt(val_tinh/7)}</td><td>{fmt(val_tinh/7)}</td><td class="text-green">+6.8%</td>
                <td>{fmt(val_tinh)}</td><td>{fmt(val_tinh)}</td><td>{fmt(val_tinh)}</td><td>{fmt(val_tinh)}</td><td>{fmt(val_tinh)}</td><td class="text-green">+6.8%</td>
                <td>{fmt(val_tinh)}</td><td>{fmt(val_tinh)}</td><td class="text-green">+6.8%</td>
                <td>{"10" if is_doanh_thu else "-"}</td><td class="text-green">{"Wait" if is_doanh_thu else "-"}</td>
            </tr>
            """

            for bc_name, bc_data in tinh_data['bcs'].items():
                val_bc = bc_data['dt'] if is_doanh_thu else bc_data['sl']
                rows_html += f"""
                <tr class="sub-row-3 {tinh_ind_clean_id}" style="display:none; background-color: #fafafa; font-style: italic; color: #555;">
                    <td style="padding-left: 60px;">• Bưu cục phát: <b>{bc_name}</b></td>
                    <td>10</td><td>100.00</td>
                    <td>{fmt(val_bc/7)}</td><td>{fmt(val_bc/7)}</td><td>{fmt(val_bc/7)}</td><td>{fmt(val_bc/7)}</td><td>{fmt(val_bc/7)}</td><td>{fmt(val_bc/7)}</td><td>{fmt(val_bc/7)}</td><td class="text-green">+6.8%</td>
                    <td>{fmt(val_bc)}</td><td>{fmt(val_bc)}</td><td>{fmt(val_bc)}</td><td>{fmt(val_bc)}</td><td>{fmt(val_bc)}</td><td class="text-green">+6.8%</td>
                    <td>{"10" if is_doanh_thu else "-"}</td><td class="text-green">{"Wait" if is_doanh_thu else "-"}</td>
                </tr>
                """

        return rows_html

    rows_html_sl_section = generate_matrix_rows(is_doanh_thu=False)
    rows_html_dt_section = generate_matrix_rows(is_doanh_thu=True)

    matrix_dt_html = f"""
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
            padding: 7px 4px;
            border: 1px solid #444444;
            font-weight: 600;
            font-size: 11px;
        }}
        .matrix-table td {{
            padding: 6px 8px;
            border: 1px solid #dddddd;
            vertical-align: middle;
            text-align: right;
        }}
        .matrix-table td:first-child {{ text-align: left; }}
        .row-group {{ font-weight: bold; background-color: #f8f9fa; cursor: pointer; }}
        .toggle-btn {{
            display: inline-block; width: 16px; height: 16px; line-height: 14px;
            text-align: center; border: 1px solid #333; background: #fff;
            color: #333; font-weight: bold; font-size: 10px; cursor: pointer;
            margin-right: 5px; border-radius: 2px;
        }}
        .text-green {{ color: #2e7d32; font-weight: bold; }}
        .text-red {{ color: #c62828; font-weight: bold; }}
    </style>
    </head>
    <body>

    <table class="matrix-table">
        <thead>
            <tr>
                <th rowspan="2" style="width: 25%;">Phân loại Đối tác / Tỉnh phát</th>
                <th rowspan="2" style="width: 4%;">Mục tiêu</th>
                <th rowspan="2" style="width: 5%;">Kết quả thực hiện</th>
                <th colspan="8" style="background-color: #2a2a2a;">7 ngày gần nhất</th>
                <th colspan="6" style="background-color: #333333;">5 tuần gần nhất</th>
                <th colspan="5" style="background-color: #2a2a2a;">Tháng</th>
            </tr>
            <tr>
                <th>{sorted_days_dt[0]}</th><th>{sorted_days_dt[1]}</th><th>{sorted_days_dt[2]}</th><th>{sorted_days_dt[3]}</th><th>{sorted_days_dt[4]}</th><th>{sorted_days_dt[5]}</th><th>{sorted_days_dt[6]}</th><th style="color: #ff5252;">DoD</th>
                <th>W30</th><th>W31</th><th>W32</th><th>W33</th><th>W34</th><th style="color: #ff5252;">WoW</th>
                <th>M-1</th><th>M</th><th style="color: #ff5252;">MoM</th>
                <th>Dự kiến FM doanh thu (Tỷ)</th><th>Dự kiến doanh thu (Δ vs Mục tiêu)</th>
            </tr>
        </thead>
        <tbody>
            <tr class="row-group" onclick="toggleRow('group_sl_sec_root', event, 'btn_sl_sec_root')">
                <td><span class="toggle-btn" id="btn_sl_sec_root">[+]</span> <b>SẢN LƯỢNG</b></td>
                <td style="text-align: center;">-</td>
                <td style="text-align: center;">100%</td>
                <td>{d_sl_vals[0]:,.0f}</td><td>{d_sl_vals[1]:,.0f}</td><td>{d_sl_vals[2]:,.0f}</td><td>{d_sl_vals[3]:,.0f}</td><td>{d_sl_vals[4]:,.0f}</td><td>{d_sl_vals[5]:,.0f}</td><td><b>{d_sl_vals[6]:,.0f}</b></td><td class="text-green">+5.22%</td>
                <td>{d_sl_vals[0]*5:,.0f}</td><td>{d_sl_vals[1]*5:,.0f}</td><td>{d_sl_vals[2]*5:,.0f}</td><td>{d_sl_vals[3]*5:,.0f}</td><td>{d_sl_vals[6]*5:,.0f}</td><td class="text-green">+5.22%</td>
                <td>{tong_sl:,.0f}</td><td><b>{tong_sl:,.0f}</b></td><td class="text-green">+5.22%</td>
                <td>-</td><td>-</td>
            </tr>
            {rows_html_sl_section}

            <tr class="row-group" onclick="toggleRow('group_dt_sec_root', event, 'btn_dt_sec_root')">
                <td><span class="toggle-btn" id="btn_dt_sec_root">[+]</span> <b>DOANH THU (TỶ ĐỒNG)</b></td>
                <td style="text-align: center;">-</td>
                <td style="text-align: center;">100%</td>
                <td>{d_dt_vals[0]:,.2f}</td><td>{d_dt_vals[1]:,.2f}</td><td>{d_dt_vals[2]:,.2f}</td><td>{d_dt_vals[3]:,.2f}</td><td>{d_dt_vals[4]:,.2f}</td><td>{d_dt_vals[5]:,.2f}</td><td><b>{d_dt_vals[6]:,.2f}</b></td><td class="text-green">+6.81%</td>
                <td>{d_dt_vals[0]*5:,.2f}</td><td>{d_dt_vals[1]*5:,.2f}</td><td>{d_dt_vals[2]*5:,.2f}</td><td>{d_dt_vals[3]*5:,.2f}</td><td>{d_dt_vals[6]*5:,.2f}</td><td class="text-green">+6.81%</td>
                <td>{tong_dt:,.2f}</td><td><b>{tong_dt:,.2f}</b></td><td class="text-green">+6.81%</td>
                <td>{(tong_dt*1.1):,.2f}</td><td class="text-green">+6.81%</td>
            </tr>
            {rows_html_dt_section}
        </tbody>
    </table>

    <script>
        function toggleRow(className, event, btnId) {{
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

    components.html(matrix_dt_html, height=480, scrolling=True)


# ============================================================================================================================================
# TAB 3: DASHBOARD OPR
# ============================================================================================================================================
with tab_opr:
    st.markdown('<div style="height: 3px; background-color: #c62828; margin-bottom: 20px;"></div>', unsafe_allow_html=True)

    # 1. BỘ LỌC DÀN NGANG PHÍA TRÊN
    f_opr1, f_opr2, f_opr3, f_opr4, f_opr5, f_opr6, f_opr7 = st.columns(7)
    with f_opr1: filter_date_opr = st.date_input("NGÀY", value=(), key="opr_date")
    with f_opr2: filter_kh_opr = st.selectbox("MÃ KHÁCH HÀNG", kh_list, key="opr_kh")
    with f_opr3: filter_dt_opr = st.selectbox("MÃ ĐỐI TÁC", dt_list, key="opr_dt")
    with f_opr4: filter_kh2_opr = st.selectbox("MÃ KHÁCH HÀNG (2)", kh_list, key="opr_kh2")
    with f_opr5: filter_ld_opr = st.selectbox("LOẠI ĐƠN", ["Tất cả"], key="opr_ld")
    with f_opr6: filter_tep_opr = st.selectbox("TỆP ĐƠN (YCT TTC PTC)", ["Tất cả"], key="opr_tep")
    with f_opr7: filter_tl_opr = st.selectbox("TRỌNG LƯỢNG", ["Tất cả", "< 500g", "500g - 2kg", "> 2kg"], key="opr_tl")

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

    # 2. 6 THẺ KPI DÀN NGANG TOÀN MÀN HÌNH
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1: st.markdown(f'<div class="metric-card"><div class="metric-title">SẢN LƯỢNG PHẢI THU</div><div class="metric-value">{sl_hien_thi:,.0f}</div><div class="metric-sub-green">▲ +6.8% vs Mục tiêu</div></div>', unsafe_allow_html=True)
    with k2: st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ THU TC</div><div class="metric-value">82.4%</div><div class="metric-sub-red">▼ -3.1% vs Mục tiêu</div></div>', unsafe_allow_html=True)
    with k3: st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ THU ĐG LẦN 1</div><div class="metric-value">82.4%</div><div class="metric-sub-red">▼ -3.1% vs Mục tiêu</div></div>', unsafe_allow_html=True)
    with k4: st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ THU ĐÚNG GIỜ</div><div class="metric-value">82.4%</div><div class="metric-sub-red">▼ -3.1% vs Mục tiêu</div></div>', unsafe_allow_html=True)
    with k5: st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ XUẤT SẠCH</div><div class="metric-value">2.4%</div><div class="metric-sub-red">▼ -3.1% vs Mục tiêu</div></div>', unsafe_allow_html=True)
    with k6: st.markdown('<div class="metric-card"><div class="metric-title">ĐƠN TỒN QUÁ HẠN >1 NGÀY</div><div class="metric-value">221</div><div class="metric-sub-red">▼ -3.1% vs Mục tiêu</div></div>', unsafe_allow_html=True)

    st.write("")

    # 3. BIỂU ĐỒ XU HƯỚNG & TOP 10 DÀN NGANG
    c_opr_left, c_opr_right = st.columns([1.1, 1])

    with c_opr_left:
        st.markdown('<p class="section-red-title">XU HƯỚNG TỶ LỆ THU THÀNH CÔNG ĐÚNG GIỜ (%)</p>', unsafe_allow_html=True)
        
        days_opr = ["06/08", "07/08", "08/08", "09/08", "10/08", "11/08", "12/08"]
        val_thuc_te = [87.5, 85.0, 83.8, 79.8, 78.9, 81.0, 82.4]
        val_muc_tieu = [90.0, 90.0, 90.0, 90.0, 90.0, 90.0, 90.0]

        fig_opr = go.Figure()
        fig_opr.add_trace(go.Scatter(x=days_opr, y=val_thuc_te, mode='lines+markers', name='Thực tế', line=dict(color='#c62828', width=3), marker=dict(size=6)))
        fig_opr.add_trace(go.Scatter(x=days_opr, y=val_muc_tieu, mode='lines+markers', name='Mục tiêu', line=dict(color='#888888', width=2), marker=dict(size=5)))

        fig_opr.update_layout(
            height=300, margin=dict(l=10, r=10, t=10, b=10),
            yaxis=dict(range=[70, 95], ticksuffix="%"),
            legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_opr, use_container_width=True)

    with c_opr_right:
        st.markdown('<p class="section-red-title">TOP 10 ĐỐI TÁC TỒN THU CUỐI NGÀY CAO NHẤT</p>', unsafe_allow_html=True)
        
        top_dt_data = con.execute(f"""
            SELECT COALESCE(ma_doitac, 'Khác') as dt, COUNT(ma_phieugui) as sl
            FROM orders WHERE {where_sql_opr} AND ma_doitac IS NOT NULL
            GROUP BY ma_doitac ORDER BY sl DESC LIMIT 10
        """).fetchall()

        top_kh_data = con.execute(f"""
            SELECT COALESCE(ma_khgui, 'Khác') as kh, COUNT(ma_phieugui) as sl
            FROM orders WHERE {where_sql_opr} AND ma_khgui IS NOT NULL
            GROUP BY ma_khgui ORDER BY sl DESC LIMIT 10
        """).fetchall()

        rows_top_html = ""
        for i in range(max(len(top_dt_data), len(top_kh_data))):
            dt_name = top_dt_data[i][0] if i < len(top_dt_data) else "-"
            dt_sl = f"{top_dt_data[i][1]:,.0f}" if i < len(top_dt_data) else "-"
            kh_name = top_kh_data[i][0] if i < len(top_kh_data) else "-"
            kh_sl = f"{top_kh_data[i][1]:,.0f}" if i < len(top_kh_data) else "-"

            rows_top_html += f"""
            <tr>
                <td><b>{dt_name}</b></td><td class="val-red">{dt_sl}</td>
                <td><b>{kh_name}</b></td><td class="val-red">{kh_sl}</td>
            </tr>
            """

        html_top10_opr = f"""
        <style>
            .tbl-top10 {{ 
                width: 100%; 
                border-collapse: collapse; 
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                font-size: 11.5px; 
                background: #fafafa; 
                border: 1px solid #e0e0e0; 
            }}
            .tbl-top10 th {{ background: #f0f0f0; color: #333; padding: 6px; text-align: center; font-weight: bold; border-bottom: 1px solid #ccc; }}
            .tbl-top10 td {{ padding: 5px 10px; border-bottom: 1px solid #eee; text-align: center; color: #111; }}
            .val-red {{ color: #c62828; font-weight: bold; }}
            .table-container-top {{ max-height: 250px; overflow-y: auto; }}
        </style>
        <div class="table-container-top">
            <table class="tbl-top10">
                <thead>
                    <tr>
                        <th style="width: 30%;">MÃ ĐỐI TÁC</th>
                        <th style="width: 20%;">SẢN LƯỢNG</th>
                        <th style="width: 30%;">MÃ KH</th>
                        <th style="width: 20%;">SẢN LƯỢNG</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_top_html if rows_top_html else "<tr><td colspan='4'>Không có dữ liệu</td></tr>"}
                </tbody>
            </table>
        </div>
        """
        components.html(html_top10_opr, height=290, scrolling=False)

    st.divider()

    # 4. DANH SÁCH CHI NHÁNH & BƯU CỤC THỰC HIỆN
    st.markdown('<p class="section-red-title">DANH SÁCH CHI NHÁNH & BƯU CỤC THU (BẤM CHỌN DÒNG CHI NHÁNH BÊN TRÁI ĐỂ LỌC BƯU CỤC BÊN PHẢI)</p>', unsafe_allow_html=True)

    cn_data_raw = con.execute(f"""
        SELECT tinh_phat AS cn
        FROM orders 
        WHERE {where_sql_opr} AND tinh_phat IS NOT NULL
        GROUP BY tinh_phat 
        ORDER BY tinh_phat ASC
    """).fetchall()

    bc_data_raw = con.execute(f"""
        SELECT 
            ma_buucuc_phat AS bc, 
            tinh_phat AS cn
        FROM orders 
        WHERE {where_sql_opr} AND tinh_phat IS NOT NULL AND ma_buucuc_phat IS NOT NULL
        GROUP BY ma_buucuc_phat, tinh_phat 
        ORDER BY ma_buucuc_phat ASC
    """).fetchall()

    rows_cn_html = ""
    for item in cn_data_raw:
        cn_code = item[0]
        rows_cn_html += f"""
        <tr class="cn-row" data-cn="{cn_code}" onclick="filterBC('{cn_code}', this)">
            <td style="font-weight: bold; cursor: pointer;">{cn_code}</td>
            <td>76.2%</td>
            <td class="text-red">-4.8%</td>
            <td style="background-color: #f9f9f9;">88.1%</td>
            <td class="text-red" style="background-color: #f9f9f9;">-2.1%</td>
        </tr>
        """

    rows_bc_html = ""
    for item in bc_data_raw:
        bc_code = item[0]
        cn_code = item[1]
        rows_bc_html += f"""
        <tr class="bc-row" data-cn="{cn_code}">
            <td style="font-weight: bold;">{bc_code}</td>
            <td style="font-weight: bold;">{cn_code}</td>
            <td>76.2%</td>
            <td class="text-red">-4.8%</td>
            <td style="background-color: #f9f9f9;">88.1%</td>
            <td class="text-red" style="background-color: #f9f9f9;">-2.1%</td>
        </tr>
        """

    interactive_tables_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
            margin: 0; padding: 0; background: transparent; 
        }}
        .grid-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }}
        .table-title {{
            font-size: 12px; font-weight: bold; color: #333; margin-bottom: 6px;
        }}
        .table-scroll {{
            max-height: 360px;
            overflow-y: auto;
            border: 1px solid #d3d3d3;
            border-radius: 4px;
            background: #fff;
        }}
        table {{
            width: 100%; border-collapse: separate; border-spacing: 0; font-size: 11.5px;
        }}
        th {{
            position: sticky; top: 0; z-index: 10;
            background-color: #222222; color: #ffffff;
            text-align: center; padding: 7px 4px;
            border-bottom: 1px solid #444; border-right: 1px solid #444;
            font-weight: bold;
        }}
        td {{
            padding: 6px 4px; border-bottom: 1px solid #eee; border-right: 1px solid #eee;
            text-align: center; color: #111;
        }}
        tr.cn-row:hover {{
            background-color: #ffebee !important;
            cursor: pointer;
        }}
        tr.selected-cn {{
            background-color: #ffcdd2 !important;
        }}
        .text-red {{ color: #c62828; font-weight: bold; background-color: #fff5f5; }}
        .btn-reset {{
            display: inline-block; padding: 2px 8px; font-size: 11px;
            background: #eee; border: 1px solid #ccc; border-radius: 3px;
            cursor: pointer; margin-left: 8px; font-weight: normal;
        }}
    </style>
    </head>
    <body>

    <div class="grid-container">
        <div>
            <div class="table-title">
                Bảng Chi Nhánh Thu <span style="font-weight:normal; color:#666;">(Bấm chọn dòng để lọc Bưu cục)</span>
                <span class="btn-reset" onclick="resetFilter()">Xóa lọc</span>
            </div>
            <div class="table-scroll">
                <table>
                    <thead>
                        <tr>
                            <th>Chi nhánh</th>
                            <th>Tỷ lệ thu thành công đúng giờ</th>
                            <th>SS cùng kỳ</th>
                            <th>Tỷ lệ xuất sạch</th>
                            <th>SS cùng kỳ</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_cn_html if rows_cn_html else "<tr><td colspan='5'>Không có dữ liệu</td></tr>"}
                    </tbody>
                </table>
            </div>
        </div>

        <div>
            <div class="table-title">
                Bưu Cục Thu <span id="bc-title-status" style="color: #c62828; font-weight: bold;">(Toàn Quốc)</span>
            </div>
            <div class="table-scroll">
                <table>
                    <thead>
                        <tr>
                            <th>Bưu cục</th>
                            <th>Chi nhánh</th>
                            <th>Tỷ lệ thu thành công đúng giờ</th>
                            <th>SS cùng kỳ</th>
                            <th>Tỷ lệ xuất sạch</th>
                            <th>SS cùng kỳ</th>
                        </tr>
                    </thead>
                    <tbody id="bc-tbody">
                        {rows_bc_html if rows_bc_html else "<tr><td colspan='6'>Không có dữ liệu</td></tr>"}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        function filterBC(cnCode, rowElem) {{
            var cnRows = document.getElementsByClassName('cn-row');
            for (var i = 0; i < cnRows.length; i++) {{
                cnRows[i].classList.remove('selected-cn');
            }}
            if (rowElem) rowElem.classList.add('selected-cn');

            var bcRows = document.getElementsByClassName('bc-row');
            var count = 0;
            for (var j = 0; j < bcRows.length; j++) {{
                if (bcRows[j].getAttribute('data-cn') === cnCode) {{
                    bcRows[j].style.display = 'table-row';
                    count++;
                }} else {{
                    bcRows[j].style.display = 'none';
                }}
            }}
            document.getElementById('bc-title-status').innerText = '(Chi nhánh: ' + cnCode + ')';
        }}

        function resetFilter() {{
            var cnRows = document.getElementsByClassName('cn-row');
            for (var i = 0; i < cnRows.length; i++) {{
                cnRows[i].classList.remove('selected-cn');
            }}
            var bcRows = document.getElementsByClassName('bc-row');
            for (var j = 0; j < bcRows.length; j++) {{
                bcRows[j].style.display = 'table-row';
            }}
            document.getElementById('bc-title-status').innerText = '(Toàn Quốc)';
        }}
    </script>
    </body>
    </html>
    """

    components.html(interactive_tables_html, height=410, scrolling=False)

    st.divider()

    # 5. BÁO CÁO MA TRẬN CHẤT LƯỢNG KHÂU THU (THÊM VÀO CUỐI TAB 2)
    st.markdown('<p class="section-red-title">MA TRẬN CHẤT LƯỢNG KHÂU THU (DRILL-DOWN DỮ LIỆU)</p>', unsafe_allow_html=True)

    days_data_matrix_opr = con.execute(f"""
        SELECT clean_date, COUNT(*) as sl 
        FROM orders WHERE {where_sql_opr} AND clean_date IS NOT NULL 
        GROUP BY clean_date ORDER BY clean_date DESC LIMIT 7
    """).fetchall()

    days_dict_matrix_opr = {row[0].strftime('%d/%m'): row[1] for row in days_data_matrix_opr}
    sorted_days_matrix_opr = sorted(list(days_dict_matrix_opr.keys()))
    while len(sorted_days_matrix_opr) < 7:
        sorted_days_matrix_opr.insert(0, "--/--")
    d_vals_matrix_opr = [days_dict_matrix_opr.get(d, 0) for d in sorted_days_matrix_opr]

    m_current_matrix_opr = con.execute(f"SELECT COUNT(*) FROM orders WHERE {where_sql_opr}").fetchone()[0]

    all_tree_matrix_opr = con.execute(f"""
        SELECT 
            COALESCE(ma_doitac, 'Khác') as dt,
            COALESCE(tinh_phat, 'Khác') as tinh,
            COALESCE(ma_buucuc_phat, 'Khác') as bc,
            COUNT(*) as sl
        FROM orders 
        WHERE {where_sql_opr} 
        GROUP BY ma_doitac, tinh_phat, ma_buucuc_phat
        ORDER BY dt, tinh, sl DESC
    """).fetchall()

    tree_struct_matrix_opr = {}
    for dt, tinh, bc, sl in all_tree_matrix_opr:
        if dt not in tree_struct_matrix_opr: tree_struct_matrix_opr[dt] = {'sl': 0, 'tinhs': {}}
        tree_struct_matrix_opr[dt]['sl'] += sl
        if tinh not in tree_struct_matrix_opr[dt]['tinhs']: tree_struct_matrix_opr[dt]['tinhs'][tinh] = {'sl': 0, 'bcs': {}}
        tree_struct_matrix_opr[dt]['tinhs'][tinh]['sl'] += sl
        tree_struct_matrix_opr[dt]['tinhs'][tinh]['bcs'][bc] = sl

    matrix_rows_opr_html = ""
    for idx_dt, (dt_name, dt_data) in enumerate(tree_struct_matrix_opr.items()):
        dt_sl = dt_data['sl']
        dt_clean_id = f"opr_dt_{idx_dt}"

        matrix_rows_opr_html += f"""
        <tr class="sub-row-1 group_root_opr" style="display:none; background-color: #f4f6f8; font-weight:600;" onclick="toggleRow('{dt_clean_id}', event, 'btn_{dt_clean_id}')">
            <td style="padding-left: 20px;"><span class="toggle-btn" id="btn_{dt_clean_id}">[+]</span> Đối tác: <b>{dt_name}</b></td>
            <td>-</td><td>-</td>
            <td>{dt_sl//7}</td><td>{dt_sl//7}</td><td>{dt_sl//7}</td><td>{dt_sl//7}</td><td>{dt_sl//7}</td><td>{dt_sl//7}</td><td>{dt_sl//7}</td><td class="text-green">+5.22%</td>
            <td>{dt_sl}</td><td>{dt_sl}</td><td>{dt_sl}</td><td>{dt_sl}</td><td>{dt_sl}</td><td class="text-green">+5.22%</td>
            <td>{dt_sl}</td><td>{dt_sl}</td><td class="text-green">+5.22%</td>
        </tr>
        """

        for idx_tinh, (tinh_name, tinh_data) in enumerate(dt_data['tinhs'].items()):
            tinh_sl = tinh_data['sl']
            tinh_clean_id = f"{dt_clean_id}_tinh_{idx_tinh}"

            matrix_rows_opr_html += f"""
            <tr class="sub-row-2 {dt_clean_id}" style="display:none; background-color: #ffffff; color: #1565c0;" onclick="toggleRow('{tinh_clean_id}', event, 'btn_{tinh_clean_id}')">
                <td style="padding-left: 40px;"><span class="toggle-btn" id="btn_{tinh_clean_id}">[+]</span> Tỉnh thu: <b>{tinh_name}</b></td>
                <td>-</td><td>-</td>
                <td>{tinh_sl//7}</td><td>{tinh_sl//7}</td><td>{tinh_sl//7}</td><td>{tinh_sl//7}</td><td>{tinh_sl//7}</td><td>{tinh_sl//7}</td><td>{tinh_sl//7}</td><td class="text-green">+5.22%</td>
                <td>{tinh_sl}</td><td>{tinh_sl}</td><td>{tinh_sl}</td><td>{tinh_sl}</td><td>{tinh_sl}</td><td class="text-green">+5.22%</td>
                <td>{tinh_sl}</td><td>{tinh_sl}</td><td class="text-green">+5.22%</td>
            </tr>
            """

            for bc_name, bc_sl in tinh_data['bcs'].items():
                matrix_rows_opr_html += f"""
                <tr class="sub-row-3 {tinh_clean_id}" style="display:none; background-color: #fafafa; font-style: italic; color: #555;">
                    <td style="padding-left: 60px;">• Bưu cục thu: <b>{bc_name}</b></td>
                    <td>-</td><td>-</td>
                    <td>{bc_sl//7}</td><td>{bc_sl//7}</td><td>{bc_sl//7}</td><td>{bc_sl//7}</td><td>{bc_sl//7}</td><td>{bc_sl//7}</td><td>{bc_sl//7}</td><td class="text-green">+5.22%</td>
                    <td>{bc_sl}</td><td>{bc_sl}</td><td>{bc_sl}</td><td>{bc_sl}</td><td>{bc_sl}</td><td class="text-green">+5.22%</td>
                    <td>{bc_sl}</td><td>{bc_sl}</td><td class="text-green">+5.22%</td>
                </tr>
                """

    matrix_opr_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 0; }}
        .matrix-table {{ width: 100%; border-collapse: collapse; font-size: 11.5px; background-color: #ffffff; color: #111111; border: 1px solid #222222; }}
        .matrix-table th {{ background-color: #222222; color: #ffffff; text-align: center; padding: 7px 4px; border: 1px solid #444444; font-weight: 600; font-size: 11px; }}
        .matrix-table td {{ padding: 6px 8px; border: 1px solid #dddddd; vertical-align: middle; text-align: right; }}
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
                <th rowspan="2" style="width: 26%;">Chỉ tiêu khâu Thu</th>
                <th rowspan="2" style="width: 5%;">Mục tiêu</th>
                <th rowspan="2" style="width: 5%;">Kết quả thực hiện</th>
                <th colspan="8" style="background-color: #2a2a2a;">7 ngày gần nhất</th>
                <th colspan="6" style="background-color: #333333;">5 tuần gần nhất</th>
                <th colspan="3" style="background-color: #2a2a2a;">Tháng</th>
            </tr>
            <tr>
                <th>{sorted_days_matrix_opr[0]}</th><th>{sorted_days_matrix_opr[1]}</th><th>{sorted_days_matrix_opr[2]}</th><th>{sorted_days_matrix_opr[3]}</th><th>{sorted_days_matrix_opr[4]}</th><th>{sorted_days_matrix_opr[5]}</th><th>{sorted_days_matrix_opr[6]}</th><th style="color: #ff5252;">DoD</th>
                <th>W28</th><th>W31</th><th>W32</th><th>W33</th><th>W34</th><th style="color: #ff5252;">WoW</th>
                <th>M-1</th><th>M</th><th style="color: #ff5252;">MoM</th>
            </tr>
        </thead>
        <tbody>
            <tr class="row-group" onclick="toggleRow('group_root_opr', event, 'btn_root_opr')">
                <td><span class="toggle-btn" id="btn_root_opr">[+]</span> <b>Sản lượng phải thu</b></td>
                <td style="text-align: center;">-</td>
                <td style="text-align: center;">100%</td>
                <td>{d_vals_matrix_opr[0]:,.0f}</td><td>{d_vals_matrix_opr[1]:,.0f}</td><td>{d_vals_matrix_opr[2]:,.0f}</td><td>{d_vals_matrix_opr[3]:,.0f}</td><td>{d_vals_matrix_opr[4]:,.0f}</td><td>{d_vals_matrix_opr[5]:,.0f}</td><td><b>{d_vals_matrix_opr[6]:,.0f}</b></td><td class="text-green">+5.22%</td>
                <td>{d_vals_matrix_opr[0]*5:,.0f}</td><td>{d_vals_matrix_opr[1]*5:,.0f}</td><td>{d_vals_matrix_opr[2]*5:,.0f}</td><td>{d_vals_matrix_opr[3]*5:,.0f}</td><td>{d_vals_matrix_opr[6]*5:,.0f}</td><td class="text-green">+5.22%</td>
                <td>{m_current_matrix_opr:,.0f}</td><td><b>{m_current_matrix_opr:,.0f}</b></td><td class="text-green">+5.22%</td>
            </tr>

            {matrix_rows_opr_html}

            <tr class="row-group">
                <td><b>Sản lượng thu thành công</b></td>
                <td style="text-align: center;">-</td>
                <td style="text-align: center;">98%</td>
                <td>{d_vals_matrix_opr[0]*0.9:,.0f}</td><td>{d_vals_matrix_opr[1]*0.9:,.0f}</td><td>{d_vals_matrix_opr[2]*0.9:,.0f}</td><td>{d_vals_matrix_opr[3]*0.9:,.0f}</td><td>{d_vals_matrix_opr[4]*0.9:,.0f}</td><td>{d_vals_matrix_opr[5]*0.9:,.0f}</td><td><b>{d_vals_matrix_opr[6]*0.9:,.0f}</b></td><td class="text-red">-2.10%</td>
                <td>{d_vals_matrix_opr[0]*4:,.0f}</td><td>{d_vals_matrix_opr[1]*4:,.0f}</td><td>{d_vals_matrix_opr[2]*4:,.0f}</td><td>{d_vals_matrix_opr[3]*4:,.0f}</td><td>{d_vals_matrix_opr[6]*4:,.0f}</td><td class="text-red">-1.50%</td>
                <td>{m_current_matrix_opr*0.95:,.0f}</td><td><b>{m_current_matrix_opr*0.95:,.0f}</b></td><td class="text-red">-1.20%</td>
            </tr>

            <tr>
                <td style="font-weight: bold;">% Thu thành công</td>
                <td style="text-align: center;">99.00</td>
                <td style="text-align: center;">100.00</td>
                <td>88.42</td><td>87.42</td><td>85.96</td><td>79.36</td><td>83.26</td><td>82.42</td><td>88.79</td><td class="text-green">+3.05</td>
                <td>84.89</td><td>83.99</td><td>85.81</td><td>82.91</td><td>86.96</td><td class="text-green">+2.05</td>
                <td>82.59</td><td>82.32</td><td class="text-green">+1.05</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">% Thu thành công đg lần 1</td>
                <td style="text-align: center;">98.00</td>
                <td style="text-align: center;">100.00</td>
                <td>85.15</td><td>80.17</td><td>85.94</td><td>85.08</td><td>89.14</td><td>88.11</td><td>87.75</td><td class="text-green">+1.93</td>
                <td>86.80</td><td>81.11</td><td>86.22</td><td>86.40</td><td>81.90</td><td class="text-green">+1.93</td>
                <td>86.29</td><td>82.93</td><td class="text-green">+1.93</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">% Thu thành công đúng giờ</td>
                <td style="text-align: center;">99.00</td>
                <td style="text-align: center;">100.00</td>
                <td>85.15</td><td>80.17</td><td>85.94</td><td>85.08</td><td>89.14</td><td>88.11</td><td>87.75</td><td class="text-red">-1.05</td>
                <td>86.80</td><td>81.11</td><td>86.22</td><td>86.40</td><td>81.90</td><td class="text-red">-1.05</td>
                <td>86.29</td><td>82.93</td><td class="text-red">-1.05</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">% Xuất sạch khâu thu</td>
                <td style="text-align: center;">95.00</td>
                <td style="text-align: center;">100.00</td>
                <td>98.42</td><td>97.42</td><td>95.96</td><td>99.36</td><td>93.26</td><td>92.42</td><td>98.79</td><td class="text-green">+1.93</td>
                <td>94.89</td><td>93.99</td><td>95.81</td><td>92.91</td><td>96.96</td><td class="text-green">+1.93</td>
                <td>92.59</td><td>92.32</td><td class="text-green">+1.93</td>
            </tr>

            <tr class="row-group" onclick="toggleRow('group_ton_opr', event, 'btn_ton_opr')">
                <td><span class="toggle-btn" id="btn_ton_opr">[+]</span> <b>% Tồn thu quá hạn 1 ngày</b></td>
                <td>-</td><td>-</td>
                <td>2.1</td><td>2.3</td><td>1.2</td><td>1.2</td><td>2.3</td><td>1.2</td><td>1.2</td><td class="text-green">-0.22</td>
                <td>2.3</td><td>2.3</td><td>1.2</td><td>1.2</td><td>2.3</td><td class="text-green">-0.22</td>
                <td>1.2</td><td>2.3</td><td class="text-green">-0.22</td>
            </tr>
            <tr class="sub-row-1 group_ton_opr" style="display:none; background-color: #fafafa;">
                <td style="padding-left: 30px;"><span class="toggle-btn" style="background:#f0f0f0;">-</span> % Tồn thu quá hạn trên 2 ngày</td>
                <td>-</td><td>-</td>
                <td>1.0</td><td>2.0</td><td>1.0</td><td>1.0</td><td>2.0</td><td>1.0</td><td>1.0</td><td class="text-green">-0.15</td>
                <td>2.0</td><td>2.0</td><td>1.0</td><td>1.0</td><td>2.0</td><td class="text-green">-0.15</td>
                <td>1.0</td><td>2.0</td><td class="text-green">-0.15</td>
            </tr>
            <tr class="sub-row-1 group_ton_opr" style="display:none; background-color: #fafafa;">
                <td style="padding-left: 30px;"><span class="toggle-btn" style="background:#f0f0f0;">-</span> % Tồn thu quá hạn trên 3 ngày</td>
                <td>-</td><td>-</td>
                <td>1.0</td><td>2.0</td><td>1.0</td><td>1.0</td><td>2.0</td><td>1.0</td><td>1.0</td><td class="text-green">-0.15</td>
                <td>2.0</td><td>2.0</td><td>1.0</td><td>1.0</td><td>2.0</td><td class="text-green">-0.15</td>
                <td>1.0</td><td>2.0</td><td class="text-green">-0.15</td>
            </tr>
            <tr class="sub-row-1 group_ton_opr" style="display:none; background-color: #fafafa;">
                <td style="padding-left: 30px;"><span class="toggle-btn" style="background:#f0f0f0;">-</span> % Tồn thu quá hạn trên 4 ngày</td>
                <td>-</td><td>-</td>
                <td>1.0</td><td>2.0</td><td>1.0</td><td>1.0</td><td>2.0</td><td>1.0</td><td>1.0</td><td class="text-green">-0.15</td>
                <td>2.0</td><td>2.0</td><td>1.0</td><td>1.0</td><td>2.0</td><td class="text-green">-0.15</td>
                <td>1.0</td><td>2.0</td><td class="text-green">-0.15</td>
            </tr>
        </tbody>
    </table>

    <script>
        function toggleRow(className, event, btnId) {{
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

    components.html(matrix_opr_html, height=480, scrolling=True)

# 6. TỒN THU TOÀN QUỐC (CÓ THỂ XUẤT CHI TIẾT)
    st.divider()
    st.markdown('<p class="section-red-title">TỒN THU TOÀN QUỐC (Có thể xuất chi tiết)</p>', unsafe_allow_html=True)

    # Truy vấn lấy danh sách Chi nhánh & Bưu cục thực tế từ DuckDB
    ton_raw_db = con.execute(f"""
        SELECT 
            COALESCE(tinh_phat, 'Khác') as cn,
            COALESCE(ma_buucuc_phat, 'Khác') as bc
        FROM orders 
        WHERE {where_sql_opr} AND tinh_phat IS NOT NULL
        GROUP BY tinh_phat, ma_buucuc_phat
        ORDER BY tinh_phat ASC, ma_buucuc_phat ASC
    """).fetchall()

    # Gom nhóm theo Chi nhánh -> Danh sách Bưu cục
    ton_structure = {}
    for cn, bc in ton_raw_db:
        if cn not in ton_structure:
            ton_structure[cn] = []
        ton_structure[cn].append(bc)

    rows_ton_thu_html = ""
    for idx_cn, (cn_code, bc_list) in enumerate(ton_structure.items()):
        cn_row_id = f"ton_cn_{idx_cn}"

        # Dòng Chi nhánh (Level 1)
        rows_ton_thu_html += f"""
        <tr class="ton-cn-row" onclick="toggleTonRow('{cn_row_id}', event, 'btn_{cn_row_id}')">
            <td style="text-align: left; padding-left: 8px;">
                <span class="toggle-btn-small" id="btn_{cn_row_id}">+</span>
                <b>{cn_code}</b>
            </td>
            <td class="text-red">2</td>
            <td class="text-orange">3</td>
            <td>45</td>
            <td>6</td>
            <td>5</td>
            <td class="text-red">7</td>
            <td class="text-orange">8</td>
            <td>9</td>
            <td>11</td>
            <td>10</td>
        </tr>
        """

        # Các dòng Bưu cục thực tế thuộc Chi nhánh đó (Level 2 - Thu gọn mặc định)
        for bc_code in bc_list:
            rows_ton_thu_html += f"""
            <tr class="ton-bc-row {cn_row_id}" style="display: none;">
                <td style="text-align: left; padding-left: 28px; color: #333; font-style: italic;">
                    • Bưu cục thu: <b>{bc_code}</b>
                </td>
                <td class="text-red">2</td>
                <td class="text-orange">3</td>
                <td>45</td>
                <td>6</td>
                <td>5</td>
                <td class="text-red">7</td>
                <td class="text-orange">8</td>
                <td>9</td>
                <td>11</td>
                <td>10</td>
            </tr>
            """

    ton_thu_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0; padding: 0; background: transparent;
        }}
        .table-scroll-ton {{
            max-height: 380px;
            overflow-y: auto;
            border: 1px solid #111111;
            background: #ffffff;
        }}
        .tbl-ton {{
            width: 100%;
            border-collapse: collapse;
            font-size: 11.5px;
            color: #111111;
        }}
        .tbl-ton th {{
            position: sticky; top: 0; z-index: 10;
            background-color: #262626; color: #ffffff;
            text-align: center; padding: 7px 4px;
            border-bottom: 1px solid #444; border-right: 1px solid #444;
            font-weight: bold; font-size: 11px;
        }}
        .tbl-ton td {{
            padding: 6px 4px; border-bottom: 1px solid #ddd; border-right: 1px solid #eee;
            text-align: center;
        }}
        .tr-total-ton {{
            background-color: #ffffff; font-weight: bold;
        }}
        .ton-cn-row {{
            cursor: pointer; background-color: #ffffff;
        }}
        .ton-cn-row:hover {{
            background-color: #f0f4f8;
        }}
        .ton-bc-row {{
            background-color: #fafafa;
        }}
        .toggle-btn-small {{
            display: inline-block; width: 12px; height: 12px; line-height: 10px;
            text-align: center; border: 1px solid #333; background: #fff;
            color: #333; font-weight: bold; font-size: 10px; margin-right: 4px;
        }}
        .text-red {{ color: #c62828; font-weight: bold; }}
        .text-orange {{ color: #ef6c00; font-weight: bold; }}
    </style>
    </head>
    <body>

    <div class="table-scroll-ton">
        <table class="tbl-ton">
            <thead>
                <tr>
                    <th style="width: 16%;">Chi nhánh</th>
                    <th style="width: 8.4%;">Còn 1 ngày</th>
                    <th style="width: 8.4%;">Còn 2 ngày</th>
                    <th style="width: 8.4%;">Còn 3 ngày</th>
                    <th style="width: 8.4%;">Còn 4 ngày</th>
                    <th style="width: 8.4%;">Còn 5 ngày</th>
                    <th style="width: 9.4%;">Tỷ lệ >1 ngày</th>
                    <th style="width: 9.4%;">Tỷ lệ >2 ngày</th>
                    <th style="width: 9.4%;">Tỷ lệ >3 ngày</th>
                    <th style="width: 9.4%;">Tỷ lệ >4 ngày</th>
                    <th style="width: 9.4%;">Tỷ lệ >5 ngày</th>
                </tr>
            </thead>
            <tbody>
                <tr class="tr-total-ton">
                    <td style="text-align: center;">TOTAL</td>
                    <td class="text-red">111</td>
                    <td class="text-orange">111</td>
                    <td>111</td>
                    <td>111</td>
                    <td>111</td>
                    <td class="text-red">111</td>
                    <td class="text-orange">111</td>
                    <td>200</td>
                    <td>300</td>
                    <td>305</td>
                </tr>
                {rows_ton_thu_html if rows_ton_thu_html else "<tr><td colspan='11'>Không có dữ liệu</td></tr>"}
            </tbody>
        </table>
    </div>

    <script>
        function toggleTonRow(className, event, btnId) {{
            if (event) event.stopPropagation();
            var rows = document.getElementsByClassName(className);
            var btn = document.getElementById(btnId);
            if (!rows || rows.length === 0) return;
            var isHidden = rows[0].style.display === 'none';
            for (var i = 0; i < rows.length; i++) {{
                rows[i].style.display = isHidden ? 'table-row' : 'none';
            }}
            if (btn) btn.innerText = isHidden ? '-' : '+';
        }}
    </script>
    </body>
    </html>
    """

    components.html(ton_thu_html, height=380, scrolling=False)


# ==========================================
# TAB 4: DASHBOARD ODR
# ==========================================
with tab_odr:
    st.markdown('<div style="height: 3px; background-color: #c62828; margin-bottom: 20px;"></div>', unsafe_allow_html=True)

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

    st.markdown('<p class="section-red-title">DANH SÁCH CHI NHÁNH & BƯU CỤC PHÁT (BẤM CHỌN DÒNG CHI NHÁNH BÊN TRÁI ĐỂ LỌC BƯU CỤC BÊN PHẢI)</p>', unsafe_allow_html=True)

    cn_data_raw = con.execute(f"""
        SELECT 
            tinh_phat AS cn,
            COUNT(*) AS tong_don,
            ROUND(SUM(tong_cuoc)/1e6, 1) AS doanh_thu
        FROM orders 
        WHERE {where_sql_odr} AND tinh_phat IS NOT NULL
        GROUP BY tinh_phat 
        ORDER BY tong_don DESC
    """).fetchall()

    bc_data_raw = con.execute(f"""
        SELECT 
            ma_buucuc_phat AS bc, 
            tinh_phat AS cn,
            COUNT(*) AS tong_don,
            ROUND(SUM(tong_cuoc)/1e6, 1) AS doanh_thu
        FROM orders 
        WHERE {where_sql_odr} AND tinh_phat IS NOT NULL AND ma_buucuc_phat IS NOT NULL
        GROUP BY ma_buucuc_phat, tinh_phat 
        ORDER BY tong_don DESC
    """).fetchall()

    rows_cn_html = ""
    for item in cn_data_raw:
        cn_code = item[0]
        tong_don = f"{item[1]:,}" if item[1] else "0"
        doanh_thu = f"{item[2]:,.1f}" if item[2] else "0.0"
        rows_cn_html += f"""
        <tr class="cn-row" data-cn="{cn_code}" onclick="filterBC('{cn_code}', this)">
            <td style="font-weight: bold; cursor: pointer; text-align: left; padding-left: 10px;">{cn_code}</td>
            <td style="text-align: right; padding-right: 10px;">{tong_don}</td>
            <td style="text-align: right; padding-right: 10px;">{doanh_thu}</td>
        </tr>
        """

    rows_bc_html = ""
    for item in bc_data_raw:
        bc_code = item[0]
        cn_code = item[1]
        tong_don = f"{item[2]:,}" if item[2] else "0"
        doanh_thu = f"{item[3]:,.1f}" if item[3] else "0.0"
        rows_bc_html += f"""
        <tr class="bc-row" data-cn="{cn_code}">
            <td style="font-weight: bold; text-align: left; padding-left: 10px;">{bc_code}</td>
            <td style="font-weight: bold; text-align: center;">{cn_code}</td>
            <td style="text-align: right; padding-right: 10px;">{tong_don}</td>
            <td style="text-align: right; padding-right: 10px;">{doanh_thu}</td>
        </tr>
        """

    interactive_tables_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
            margin: 0; padding: 0; background: transparent; 
        }}
        .grid-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }}
        .table-title {{
            font-size: 12px; font-weight: bold; color: #333; margin-bottom: 6px;
        }}
        .table-scroll {{
            max-height: 360px;
            overflow-y: auto;
            border: 1px solid #d3d3d3;
            border-radius: 4px;
            background: #fff;
        }}
        table {{
            width: 100%; border-collapse: separate; border-spacing: 0; font-size: 11.5px;
        }}
        th {{
            position: sticky; top: 0; z-index: 10;
            background-color: #222222; color: #ffffff;
            text-align: center; padding: 7px 8px;
            border-bottom: 1px solid #444; border-right: 1px solid #444;
            font-weight: bold;
        }}
        td {{
            padding: 6px 8px; border-bottom: 1px solid #eee; border-right: 1px solid #eee;
            color: #111;
        }}
        tr.cn-row:hover {{
            background-color: #ffebee !important;
            cursor: pointer;
        }}
        tr.selected-cn {{
            background-color: #ffcdd2 !important;
        }}
        .btn-reset {{
            display: inline-block; padding: 2px 8px; font-size: 11px;
            background: #eee; border: 1px solid #ccc; border-radius: 3px;
            cursor: pointer; margin-left: 8px; font-weight: normal;
        }}
    </style>
    </head>
    <body>

    <div class="grid-container">
        <div>
            <div class="table-title">
                Bảng Tỉnh Phát <span style="font-weight:normal; color:#666;">(Bấm chọn dòng để lọc Bưu cục)</span>
                <span class="btn-reset" onclick="resetFilter()">Xóa lọc</span>
            </div>
            <div class="table-scroll">
                <table>
                    <thead>
                        <tr>
                            <th style="text-align: left; padding-left: 10px;">Tỉnh phát</th>
                            <th style="text-align: right; padding-right: 10px;">Tổng đơn</th>
                            <th style="text-align: right; padding-right: 10px;">Doanh thu (Tr)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_cn_html if rows_cn_html else "<tr><td colspan='3' style='text-align:center;'>Không có dữ liệu</td></tr>"}
                    </tbody>
                </table>
            </div>
        </div>

        <div>
            <div class="table-title">
                Bưu Cục Phát <span id="bc-title-status" style="color: #c62828; font-weight: bold;">(Toàn Quốc)</span>
            </div>
            <div class="table-scroll">
                <table>
                    <thead>
                        <tr>
                            <th style="text-align: left; padding-left: 10px;">Mã bưu cục phát</th>
                            <th>Tỉnh phát</th>
                            <th style="text-align: right; padding-right: 10px;">Sản lượng đơn</th>
                            <th style="text-align: right; padding-right: 10px;">Doanh thu (Tr)</th>
                        </tr>
                    </thead>
                    <tbody id="bc-tbody">
                        {rows_bc_html if rows_bc_html else "<tr><td colspan='4' style='text-align:center;'>Không có dữ liệu</td></tr>"}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        function filterBC(cnCode, rowElem) {{
            var cnRows = document.getElementsByClassName('cn-row');
            for (var i = 0; i < cnRows.length; i++) {{
                cnRows[i].classList.remove('selected-cn');
            }}
            if (rowElem) rowElem.classList.add('selected-cn');

            var bcRows = document.getElementsByClassName('bc-row');
            for (var j = 0; j < bcRows.length; j++) {{
                if (bcRows[j].getAttribute('data-cn') === cnCode) {{
                    bcRows[j].style.display = 'table-row';
                }} else {{
                    bcRows[j].style.display = 'none';
                }}
            }}
            document.getElementById('bc-title-status').innerText = '(Tỉnh: ' + cnCode + ')';
        }}

        function resetFilter() {{
            var cnRows = document.getElementsByClassName('cn-row');
            for (var i = 0; i < cnRows.length; i++) {{
                cnRows[i].classList.remove('selected-cn');
            }}
            var bcRows = document.getElementsByClassName('bc-row');
            for (var j = 0; j < bcRows.length; j++) {{
                bcRows[j].style.display = 'table-row';
            }}
            document.getElementById('bc-title-status').innerText = '(Toàn Quốc)';
        }}
    </script>
    </body>
    </html>
    """

    components.html(interactive_tables_html, height=410, scrolling=False)

    st.divider()

    st.subheader("📊 BÁO CÁO MA TRẬN CHẤT LƯỢNG VẬN HÀNH")

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

    all_tree_data = con.execute(f"""
        SELECT 
            COALESCE(ma_doitac, 'Khác') as dt,
            COALESCE(tinh_phat, 'Khác') as tinh,
            COALESCE(ma_buucuc_phat, 'Khác') as bc,
            COUNT(*) as sl
        FROM orders 
        WHERE {where_sql_odr} 
        GROUP BY ma_doitac, tinh_phat, ma_buucuc_phat
        ORDER BY dt, tinh, sl DESC
    """).fetchall()

    tree_struct = {}
    for dt, tinh, bc, sl in all_tree_data:
        if dt not in tree_struct: tree_struct[dt] = {'sl': 0, 'tinhs': {}}
        tree_struct[dt]['sl'] += sl
        if tinh not in tree_struct[dt]['tinhs']: tree_struct[dt]['tinhs'][tinh] = {'sl': 0, 'bcs': {}}
        tree_struct[dt]['tinhs'][tinh]['sl'] += sl
        tree_struct[dt]['tinhs'][tinh]['bcs'][bc] = sl

    matrix_rows_html = ""
    for idx_dt, (dt_name, dt_data) in enumerate(tree_struct.items()):
        dt_sl = dt_data['sl']
        dt_clean_id = f"dt_{idx_dt}"

        matrix_rows_html += f"""
        <tr class="sub-row-1 group_root" style="display:none; background-color: #f4f6f8; font-weight:600;" onclick="toggleRow('{dt_clean_id}', event, 'btn_{dt_clean_id}')">
            <td style="padding-left: 20px;"><span class="toggle-btn" id="btn_{dt_clean_id}">[+]</span> Đối tác: <b>{dt_name}</b></td>
            <td>-</td><td>-</td>
            <td>{dt_sl//7}</td><td>{dt_sl//7}</td><td>{dt_sl//7}</td><td>{dt_sl//7}</td><td>{dt_sl//7}</td><td>{dt_sl//7}</td><td>{dt_sl//7}</td><td class="text-green">+5.22%</td>
            <td>{dt_sl}</td><td>{dt_sl}</td><td>{dt_sl}</td><td>{dt_sl}</td><td>{dt_sl}</td><td class="text-green">+5.22%</td>
            <td>{dt_sl}</td><td>{dt_sl}</td><td class="text-green">+5.22%</td>
        </tr>
        """

        for idx_tinh, (tinh_name, tinh_data) in enumerate(dt_data['tinhs'].items()):
            tinh_sl = tinh_data['sl']
            tinh_clean_id = f"{dt_clean_id}_tinh_{idx_tinh}"

            matrix_rows_html += f"""
            <tr class="sub-row-2 {dt_clean_id}" style="display:none; background-color: #ffffff; color: #1565c0;" onclick="toggleRow('{tinh_clean_id}', event, 'btn_{tinh_clean_id}')">
                <td style="padding-left: 40px;"><span class="toggle-btn" id="btn_{tinh_clean_id}">[+]</span> Tỉnh: <b>{tinh_name}</b></td>
                <td>-</td><td>-</td>
                <td>{tinh_sl//7}</td><td>{tinh_sl//7}</td><td>{tinh_sl//7}</td><td>{tinh_sl//7}</td><td>{tinh_sl//7}</td><td>{tinh_sl//7}</td><td>{tinh_sl//7}</td><td class="text-green">+5.22%</td>
                <td>{tinh_sl}</td><td>{tinh_sl}</td><td>{tinh_sl}</td><td>{tinh_sl}</td><td>{tinh_sl}</td><td class="text-green">+5.22%</td>
                <td>{tinh_sl}</td><td>{tinh_sl}</td><td class="text-green">+5.22%</td>
            </tr>
            """

            for bc_name, bc_sl in tinh_data['bcs'].items():
                matrix_rows_html += f"""
                <tr class="sub-row-3 {tinh_clean_id}" style="display:none; background-color: #fafafa; font-style: italic; color: #555;">
                    <td style="padding-left: 60px;">• Bưu cục: <b>{bc_name}</b></td>
                    <td>-</td><td>-</td>
                    <td>{bc_sl//7}</td><td>{bc_sl//7}</td><td>{bc_sl//7}</td><td>{bc_sl//7}</td><td>{bc_sl//7}</td><td>{bc_sl//7}</td><td>{bc_sl//7}</td><td class="text-green">+5.22%</td>
                    <td>{bc_sl}</td><td>{bc_sl}</td><td>{bc_sl}</td><td>{bc_sl}</td><td>{bc_sl}</td><td class="text-green">+5.22%</td>
                    <td>{bc_sl}</td><td>{bc_sl}</td><td class="text-green">+5.22%</td>
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
            padding: 7px 4px;
            border: 1px solid #444444;
            font-weight: 600;
            font-size: 11px;
        }}
        .matrix-table td {{
            padding: 6px 8px;
            border: 1px solid #dddddd;
            vertical-align: middle;
            text-align: right;
        }}
        .matrix-table td:first-child {{ text-align: left; }}
        .row-group {{ font-weight: bold; background-color: #f8f9fa; cursor: pointer; }}
        .toggle-btn {{
            display: inline-block; width: 16px; height: 16px; line-height: 14px;
            text-align: center; border: 1px solid #333; background: #fff;
            color: #333; font-weight: bold; font-size: 10px; cursor: pointer;
            margin-right: 5px; border-radius: 2px;
        }}
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
                <th>{sorted_days[0]}</th><th>{sorted_days[1]}</th><th>{sorted_days[2]}</th><th>{sorted_days[3]}</th><th>{sorted_days[4]}</th><th>{sorted_days[5]}</th><th>{sorted_days[6]}</th><th style="color: #ff5252;">DoD</th>
                <th>W28</th><th>W31</th><th>W32</th><th>W33</th><th>W34</th><th style="color: #ff5252;">WoW</th>
                <th>M-1</th><th>M</th><th style="color: #ff5252;">MoM</th>
            </tr>
        </thead>
        <tbody>
            <tr class="row-group" onclick="toggleRow('group_root', event, 'btn_root')">
                <td><span class="toggle-btn" id="btn_root">[+]</span> <b>Sản lượng phải phát</b></td>
                <td style="text-align: center;">-</td>
                <td style="text-align: center;">100%</td>
                <td>{d_vals[0]:,.0f}</td><td>{d_vals[1]:,.0f}</td><td>{d_vals[2]:,.0f}</td><td>{d_vals[3]:,.0f}</td><td>{d_vals[4]:,.0f}</td><td>{d_vals[5]:,.0f}</td><td><b>{d_vals[6]:,.0f}</b></td><td class="text-green">+5.22%</td>
                <td>{d_vals[0]*5:,.0f}</td><td>{d_vals[1]*5:,.0f}</td><td>{d_vals[2]*5:,.0f}</td><td>{d_vals[3]*5:,.0f}</td><td>{d_vals[6]*5:,.0f}</td><td class="text-green">+5.22%</td>
                <td>{m_current:,.0f}</td><td><b>{m_current:,.0f}</b></td><td class="text-green">+5.22%</td>
            </tr>

            {matrix_rows_html}

            <tr class="row-group">
                <td><b>Sản lượng phát thành công</b></td>
                <td style="text-align: center;">-</td>
                <td style="text-align: center;">98%</td>
                <td>{d_vals[0]*0.9:,.0f}</td><td>{d_vals[1]*0.9:,.0f}</td><td>{d_vals[2]*0.9:,.0f}</td><td>{d_vals[3]*0.9:,.0f}</td><td>{d_vals[4]*0.9:,.0f}</td><td>{d_vals[5]*0.9:,.0f}</td><td><b>{d_vals[6]*0.9:,.0f}</b></td><td class="text-red">-2.10%</td>
                <td>{d_vals[0]*4:,.0f}</td><td>{d_vals[1]*4:,.0f}</td><td>{d_vals[2]*4:,.0f}</td><td>{d_vals[3]*4:,.0f}</td><td>{d_vals[6]*4:,.0f}</td><td class="text-red">-1.50%</td>
                <td>{m_current*0.95:,.0f}</td><td><b>{m_current*0.95:,.0f}</b></td><td class="text-red">-1.20%</td>
            </tr>

            <tr>
                <td style="font-weight: bold;">% Phát thành công</td>
                <td style="text-align: center;">99.00</td>
                <td style="text-align: center;">100.00</td>
                <td>28.42</td><td>27.42</td><td>25.96</td><td>19.36</td><td>13.26</td><td>22.42</td><td>18.79</td><td class="text-red">-14.05</td>
                <td>14.89</td><td>13.99</td><td>25.81</td><td>12.91</td><td>26.96</td><td class="text-red">-14.05</td>
                <td>22.59</td><td>12.32</td><td class="text-red">-14.05</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">% Phát thành công đg lần 1</td>
                <td style="text-align: center;">98.00</td>
                <td style="text-align: center;">100.00</td>
                <td>18.15</td><td>10.17</td><td>15.94</td><td>25.08</td><td>19.14</td><td>28.11</td><td>27.75</td><td class="text-green">+11.93</td>
                <td>16.80</td><td>21.11</td><td>16.22</td><td>26.40</td><td>11.90</td><td class="text-green">+11.93</td>
                <td>26.29</td><td>22.93</td><td class="text-green">+11.93</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">% Phát thành công đg</td>
                <td style="text-align: center;">99.00</td>
                <td style="text-align: center;">100.00</td>
                <td>18.15</td><td>10.17</td><td>15.94</td><td>25.08</td><td>19.14</td><td>28.11</td><td>27.75</td><td class="text-red">-14.05</td>
                <td>16.80</td><td>21.11</td><td>16.22</td><td>26.40</td><td>11.90</td><td class="text-red">-14.05</td>
                <td>26.29</td><td>22.93</td><td class="text-red">-14.05</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">% PTC in-day</td>
                <td style="text-align: center;">80.00</td>
                <td style="text-align: center;">100.00</td>
                <td>28.42</td><td>27.42</td><td>25.96</td><td>19.36</td><td>13.26</td><td>22.42</td><td>18.79</td><td class="text-green">+11.93</td>
                <td>14.89</td><td>13.99</td><td>25.81</td><td>12.91</td><td>26.96</td><td class="text-green">+11.93</td>
                <td>22.59</td><td>12.32</td><td class="text-green">+11.93</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">% PTC Next – day</td>
                <td style="text-align: center;">80.00</td>
                <td style="text-align: center;">100.00</td>
                <td>11.56</td><td>25.73</td><td>21.61</td><td>17.73</td><td>27.94</td><td>23.80</td><td>22.99</td><td class="text-red">-2.22</td>
                <td>21.62</td><td>26.19</td><td>28.47</td><td>25.42</td><td>13.49</td><td class="text-red">-2.22</td>
                <td>21.65</td><td>21.07</td><td class="text-red">-2.22</td>
            </tr>

            <tr class="row-group" onclick="toggleRow('group_ton', event, 'btn_ton')">
                <td><span class="toggle-btn" id="btn_ton">[+]</span> <b>% Tồn quá hạn 1 ngày</b></td>
                <td>-</td><td>-</td>
                <td>12</td><td>23</td><td>12</td><td>12</td><td>23</td><td>12</td><td>12</td><td class="text-green">+5.22</td>
                <td>23</td><td>23</td><td>12</td><td>12</td><td>23</td><td class="text-green">+5.22</td>
                <td>12</td><td>23</td><td class="text-green">+5.22</td>
            </tr>
            <tr class="sub-row-1 group_ton" style="display:none; background-color: #fafafa;">
                <td style="padding-left: 30px;"><span class="toggle-btn" style="background:#f0f0f0;">-</span> % Tồn quá hạn trên 2 ngày</td>
                <td>-</td><td>-</td>
                <td>10</td><td>20</td><td>10</td><td>10</td><td>20</td><td>10</td><td>10</td><td class="text-green">+4.15</td>
                <td>20</td><td>20</td><td>10</td><td>10</td><td>20</td><td class="text-green">+4.15</td>
                <td>10</td><td>20</td><td class="text-green">+4.15</td>
            </tr>
            <tr class="sub-row-1 group_ton" style="display:none; background-color: #fafafa;">
                <td style="padding-left: 30px;"><span class="toggle-btn" style="background:#f0f0f0;">-</span> % Tồn quá hạn trên 3 ngày</td>
                <td>-</td><td>-</td>
                <td>8</td><td>15</td><td>8</td><td>8</td><td>15</td><td>8</td><td>8</td><td class="text-green">+3.10</td>
                <td>15</td><td>15</td><td>8</td><td>8</td><td>15</td><td class="text-green">+3.10</td>
                <td>8</td><td>15</td><td class="text-green">+3.10</td>
            </tr>
            <tr class="sub-row-1 group_ton" style="display:none; background-color: #fafafa;">
                <td style="padding-left: 30px;"><span class="toggle-btn" style="background:#f0f0f0;">-</span> % Tồn quá hạn trên 4 ngày</td>
                <td>-</td><td>-</td>
                <td>5</td><td>10</td><td>5</td><td>5</td><td>10</td><td>5</td><td>5</td><td class="text-green">+2.05</td>
                <td>10</td><td>10</td><td>5</td><td>5</td><td>10</td><td class="text-green">+2.05</td>
                <td>5</td><td>10</td><td class="text-green">+2.05</td>
            </tr>
            <tr class="sub-row-1 group_ton" style="display:none; background-color: #fafafa;">
                <td style="padding-left: 30px;"><span class="toggle-btn" style="background:#f0f0f0;">-</span> % Tồn quá hạn trên 5 ngày</td>
                <td>-</td><td>-</td>
                <td>2</td><td>5</td><td>2</td><td>2</td><td>5</td><td>2</td><td>2</td><td class="text-green">+1.01</td>
                <td>5</td><td>5</td><td>2</td><td>2</td><td>5</td><td class="text-green">+1.01</td>
                <td>2</td><td>5</td><td class="text-green">+1.01</td>
            </tr>
        </tbody>
    </table>

    <script>
        function toggleRow(className, event, btnId) {{
            if (event) event.stopPropagation();
            var rows = document.getElementsByClassName(className);
            var btn = document.getElementById(btnId);
            if (!rows || rows.length === 0) return;
            var isHidden = rows[0].style.display === 'none';
            for (var i = 0; i < rows.length; i++) {{
                rows[i].style.display = isHidden ? 'table-row' : 'none';
                if (!isHidden) {{
                    var childClasses = rows[i].className.split(' ');
                    for (var j = 0; j < childClasses.length; j++) {{
                        if (childClasses[j].startsWith('dt_')) {{
                            var subRows = document.getElementsByClassName(childClasses[j]);
                            for (var k = 0; k < subRows.length; k++) subRows[k].style.display = 'none';
                        }}
                    }}
                }}
            }}
            if (btn) btn.innerText = isHidden ? '[-]' : '[+]';
        }}
    </script>
    </body>
    </html>
    """

    components.html(matrix_full_html, height=480, scrolling=True)

    # 3. BA BẢNG TỒN KHÂU
    ton_tree_data = con.execute(f"""
        SELECT 
            COALESCE(tinh_phat, 'Khác') as tinh,
            COALESCE(ma_buucuc_phat, 'Khác') as bc,
            COUNT(*) as sl
        FROM orders 
        WHERE {where_sql_odr}
        GROUP BY tinh_phat, ma_buucuc_phat
        ORDER BY tinh, sl DESC
    """).fetchall()

    tinh_tree = {}
    for tinh, bc, sl in ton_tree_data:
        if tinh not in tinh_tree: tinh_tree[tinh] = {'sl': 0, 'bcs': {}}
        tinh_tree[tinh]['sl'] += sl
        tinh_tree[tinh]['bcs'][bc] = sl

    base_style = """
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 0; background-color: transparent; }
        .table-container {
            max-height: 380px;
            overflow-y: auto;
            border: 1px solid #d3d3d3;
            border-radius: 4px;
        }
        table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 11.5px; background: #fff; }
        th {
            position: sticky; top: 0; z-index: 10;
            background-color: #c62828; color: #ffffff;
            text-align: center; padding: 7px 4px;
            border-bottom: 2px solid #b71c1c; border-right: 1px solid #b71c1c;
            font-weight: bold;
        }
        tr.total-row td {
            position: sticky; top: 31px; z-index: 9;
            background-color: #f5f5f5; font-weight: bold;
            border-bottom: 2px solid #ccc;
        }
        td { padding: 6px 6px; border-bottom: 1px solid #e0e0e0; border-right: 1px solid #e0e0e0; text-align: center; }
        td.col-branch { text-align: left; padding-left: 10px; }
        .ton-btn {
            display: inline-block; width: 14px; height: 14px; line-height: 12px;
            text-align: center; border: 1px solid #555; background: #fff;
            color: #333; font-weight: bold; font-size: 9px; cursor: pointer;
            margin-right: 5px; border-radius: 2px;
        }
        .ton-highlight-red { color: #c62828; font-weight: bold; }
        .ton-highlight-orange { color: #e65100; font-weight: bold; }
    </style>
    <script>
        function toggleTonRow(className, event, btnId) {
            if (event) event.stopPropagation();
            var rows = document.getElementsByClassName(className);
            var btn = document.getElementById(btnId);
            if (!rows || rows.length === 0) return;
            var isHidden = rows[0].style.display === 'none';
            for (var i = 0; i < rows.length; i++) {
                rows[i].style.display = isHidden ? 'table-row' : 'none';
            }
            if (btn) btn.innerText = isHidden ? '[-]' : '[+]';
        }
    </script>
    """

    # BẢNG 1: FM
    st.markdown('<p style="font-size: 13px; font-weight: bold; color: #111; border-left: 4px solid #c62828; padding-left: 8px; margin-top: 10px; margin-bottom: 6px;">TỒN KHÂU FM CÁC BƯU GỬI CHƯA XUẤT SẠCH – CÓ THỂ XUẤT CHI TIẾT THEO ĐƠN</p>', unsafe_allow_html=True)
    
    fm_rows_html = ""
    for idx_t, (t_name, t_data) in enumerate(tinh_tree.items()):
        t_sl = t_data['sl']
        t_id = f"fm_tinh_{idx_t}"
        fm_rows_html += f"""
        <tr style="cursor:pointer;" onclick="toggleTonRow('{t_id}', event, 'btn_{t_id}')">
            <td class="col-branch"><span class="ton-btn" id="btn_{t_id}">[+]</span> <b>{t_name}</b></td>
            <td>{t_sl:,.0f}</td>
            <td>{int(t_sl*0.03):,.0f}</td>
            <td>3.0%</td>
            <td class="ton-highlight-red">{int(t_sl*0.005):,.0f}</td>
            <td class="ton-highlight-orange">{int(t_sl*0.002):,.0f}</td>
            <td class="ton-highlight-red">1.50%</td>
            <td class="ton-highlight-orange">0.65%</td>
        </tr>
        """
        for b_name, b_sl in t_data['bcs'].items():
            fm_rows_html += f"""
            <tr class="{t_id}" style="display:none; background-color:#fafafa;">
                <td class="col-branch" style="padding-left: 32px; color: #555;">• Bưu cục: {b_name}</td>
                <td>{b_sl:,.0f}</td>
                <td>{int(b_sl*0.03):,.0f}</td>
                <td>3.0%</td>
                <td class="ton-highlight-red">{int(b_sl*0.005):,.0f}</td>
                <td class="ton-highlight-orange">{int(b_sl*0.002):,.0f}</td>
                <td class="ton-highlight-red">1.50%</td>
                <td class="ton-highlight-orange">0.65%</td>
            </tr>
            """

    html_fm = f"""
    <!DOCTYPE html><html><head>{base_style}</head><body>
    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th style="width: 20%;">Chi Nhánh</th>
                    <th style="width: 14%;">Sản lượng đã thu thành công</th>
                    <th style="width: 10%;">Tổng tồn</th>
                    <th style="width: 10%;">Tỷ lệ tồn</th>
                    <th style="width: 11%;">Tồn quá 1 ngày</th>
                    <th style="width: 11%;">Tồn quá 2 ngày</th>
                    <th style="width: 12%;">Tỷ lệ tồn quá 1 ngày</th>
                    <th style="width: 12%;">Tỷ lệ tồn quá 2 ngày</th>
                </tr>
            </thead>
            <tbody>
                <tr class="total-row">
                    <td class="col-branch">TOTAL</td>
                    <td>{tong_sl_odr:,.0f}</td>
                    <td>{int(tong_sl_odr*0.03):,.0f}</td>
                    <td>3.0%</td>
                    <td class="ton-highlight-red">{int(tong_sl_odr*0.005):,.0f}</td>
                    <td class="ton-highlight-orange">{int(tong_sl_odr*0.002):,.0f}</td>
                    <td class="ton-highlight-red">1.50%</td>
                    <td class="ton-highlight-orange">0.65%</td>
                </tr>
                {fm_rows_html}
            </tbody>
        </table>
    </div>
    </body></html>
    """
    components.html(html_fm, height=390, scrolling=False)

    # BẢNG 2: MM
    st.markdown('<p style="font-size: 13px; font-weight: bold; color: #111; border-left: 4px solid #c62828; padding-left: 8px; margin-top: 10px; margin-bottom: 6px;">TỒN KHÂU MM CÁC BƯU GỬI CHƯA KẾT NỐI – CÓ THỂ XUẤT CHI TIẾT THEO ĐƠN</p>', unsafe_allow_html=True)
    html_mm = f"""
    <!DOCTYPE html><html><head>{base_style}</head><body>
    <div class="table-container" style="max-height: 220px;">
        <table>
            <thead>
                <tr>
                    <th style="width: 20%;">Đơn vị kết nối</th>
                    <th style="width: 14%;">Sản lượng đã nhận bàn giao</th>
                    <th style="width: 10%;">Tổng tồn</th>
                    <th style="width: 10%;">Tỷ lệ tồn</th>
                    <th style="width: 11%;">Quá 6H</th>
                    <th style="width: 11%;">Quá 12H</th>
                    <th style="width: 12%;">Quá 24H</th>
                    <th style="width: 12%;">Quá 48H</th>
                </tr>
            </thead>
            <tbody>
                <tr class="total-row">
                    <td class="col-branch">TOTAL</td>
                    <td class="ton-highlight-red">222</td>
                    <td>1,381</td>
                    <td>1.12%</td>
                    <td class="ton-highlight-red">111</td>
                    <td class="ton-highlight-orange">111</td>
                    <td>13</td>
                    <td>23</td>
                </tr>
                <tr><td class="col-branch">TTKT3</td><td class="ton-highlight-red">5</td><td>381</td><td>4.2%</td><td class="ton-highlight-red">2</td><td class="ton-highlight-orange">3</td><td>1</td><td>2</td></tr>
                <tr><td class="col-branch">HNIVC</td><td class="ton-highlight-red">5</td><td>381</td><td>4.2%</td><td class="ton-highlight-red">2</td><td class="ton-highlight-orange">3</td><td>1</td><td>2</td></tr>
                <tr><td class="col-branch">DVVC</td><td class="ton-highlight-red">5</td><td>381</td><td>4.2%</td><td class="ton-highlight-red">2</td><td class="ton-highlight-orange">3</td><td>1</td><td>2</td></tr>
                <tr><td class="col-branch">DVVTNN3</td><td class="ton-highlight-red">5</td><td>381</td><td>4.2%</td><td class="ton-highlight-red">2</td><td class="ton-highlight-orange">3</td><td>1</td><td>2</td></tr>
            </tbody>
        </table>
    </div>
    </body></html>
    """
    components.html(html_mm, height=230, scrolling=False)

    # BẢNG 3: LM
    st.markdown('<p style="font-size: 13px; font-weight: bold; color: #111; border-left: 4px solid #c62828; padding-left: 8px; margin-top: 10px; margin-bottom: 6px;">TỒN KHÂU LM CÁC BƯU GỬI CHƯA PHÁT – CÓ THỂ XUẤT CHI TIẾT THEO ĐƠN</p>', unsafe_allow_html=True)
    
    lm_rows_html = ""
    for idx_t, (t_name, t_data) in enumerate(tinh_tree.items()):
        t_sl = t_data['sl']
        t_id = f"lm_tinh_{idx_t}"
        lm_rows_html += f"""
        <tr style="cursor:pointer;" onclick="toggleTonRow('{t_id}', event, 'btn_{t_id}')">
            <td class="col-branch"><span class="ton-btn" id="btn_{t_id}">[+]</span> <b>{t_name}</b></td>
            <td>{t_sl:,.0f}</td>
            <td>{int(t_sl*0.04):,.0f}</td>
            <td>4.0%</td>
            <td class="ton-highlight-red">{int(t_sl*0.008):,.0f}</td>
            <td class="ton-highlight-orange">{int(t_sl*0.003):,.0f}</td>
            <td class="ton-highlight-orange">0.80%</td>
            <td class="ton-highlight-orange">0.30%</td>
        </tr>
        """
        for b_name, b_sl in t_data['bcs'].items():
            lm_rows_html += f"""
            <tr class="{t_id}" style="display:none; background-color:#fafafa;">
                <td class="col-branch" style="padding-left: 32px; color: #555;">• Bưu cục: {b_name}</td>
                <td>{b_sl:,.0f}</td>
                <td>{int(b_sl*0.04):,.0f}</td>
                <td>4.0%</td>
                <td class="ton-highlight-red">{int(b_sl*0.008):,.0f}</td>
                <td class="ton-highlight-orange">{int(b_sl*0.003):,.0f}</td>
                <td class="ton-highlight-orange">0.80%</td>
                <td class="ton-highlight-orange">0.30%</td>
            </tr>
            """

    html_lm = f"""
    <!DOCTYPE html><html><head>{base_style}</head><body>
    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th style="width: 20%;">Chi nhánh</th>
                    <th style="width: 14%;">Sản lượng đã phát thành công</th>
                    <th style="width: 10%;">Tổng tồn</th>
                    <th style="width: 10%;">Tỷ lệ tồn</th>
                    <th style="width: 11%;">Tồn quá 1 ngày</th>
                    <th style="width: 11%;">Tồn quá 2 ngày</th>
                    <th style="width: 12%;">Tồn quá 3 ngày</th>
                    <th style="width: 12%;">Tồn quá 4 ngày</th>
                </tr>
            </thead>
            <tbody>
                <tr class="total-row">
                    <td class="col-branch">TOTAL</td>
                    <td>{tong_sl_odr:,.0f}</td>
                    <td>{int(tong_sl_odr*0.04):,.0f}</td>
                    <td>4.0%</td>
                    <td class="ton-highlight-red">{int(tong_sl_odr*0.008):,.0f}</td>
                    <td class="ton-highlight-orange">{int(tong_sl_odr*0.003):,.0f}</td>
                    <td class="ton-highlight-orange">0.80%</td>
                    <td class="ton-highlight-orange">0.30%</td>
                </tr>
                {lm_rows_html}
            </tbody>
        </table>
    </div>
    </body></html>
    """
    components.html(html_lm, height=390, scrolling=False)

# ==============================================================================================================================
# TAB 4: DASHBOARD QUÁ HẠN SLA
# ==============================================================================================================================
with tab_sla:
st.markdown('<div style="height: 3px; background-color: #c62828; margin-bottom: 20px;"></div>', unsafe_allow_html=True)

    # 1. METRIC CARDS
    m_sla1, m_sla2, m_sla3 = st.columns(3)
    with m_sla1:
        st.markdown('''
            <div class="metric-card">
                <div class="metric-title">ĐƠN QUÁ HẠN SLA</div>
                <div class="metric-value">1,876 đơn</div>
                <div class="metric-sub-red">▲ Tăng 2.1 lần WoW</div>
            </div>
        ''', unsafe_allow_html=True)
        
    with m_sla2:
        st.markdown('''
            <div class="metric-card">
                <div class="metric-title">TỶ LỆ ĐƠN QUÁ HẠN</div>
                <div class="metric-value">3.4%</div>
                <div class="metric-sub-red">▲ +2.2% vs Mục tiêu</div>
            </div>
        ''', unsafe_allow_html=True)
        
    with m_sla3:
        st.markdown('''
            <div class="metric-card">
                <div class="metric-title">SỐ TIỀN DỰ KIẾN ĐỀN BÙ</div>
                <div class="metric-value">184 triệu</div>
                <div class="metric-sub-red">▲ +62% so với tuần trước</div>
            </div>
        ''', unsafe_allow_html=True)

    st.write("")

    # 2. BIỂU ĐỒ XU HƯỚNG TỶ LỆ ĐƠN QUÁ HẠN SLA (%) - DUCKDB MOCK DATA
    st.markdown('<p class="section-red-title" style="border-left: 4px solid #c62828; padding-left: 8px; font-weight: bold;">XU HƯỚNG TỶ LỆ ĐƠN QUÁ HẠN SLA (%)</p>', unsafe_allow_html=True)
    
    # Fake dữ liệu xu hướng 7 ngày bằng DuckDB
    df_sla_chart = con.execute("""
        SELECT * FROM (VALUES 
            ('06/08', 1.1, 1.2),
            ('07/08', 1.4, 1.2),
            ('08/08', 1.8, 1.2),
            ('09/08', 2.2, 1.2),
            ('10/08', 2.6, 1.2),
            ('11/08', 3.0, 1.2),
            ('12/08', 3.4, 1.2)
        ) AS t("Ngày", "Thực tế", "Mục tiêu")
    """).fetchdf()

    fig_sla = px.line(
        df_sla_chart, 
        x="Ngày", 
        y=["Thực tế", "Mục tiêu"], 
        markers=True,
        color_discrete_map={"Thực tế": "#c62828", "Mục tiêu": "#888888"}
    )
    fig_sla.update_traces(line=dict(width=2.5), marker=dict(size=6))
    fig_sla.update_layout(
        height=300,
        margin=dict(l=10, r=10, t=10, b=10),
        yaxis=dict(title=None, gridcolor="#eee", range=[0, 4]),
        xaxis=dict(title=None, showgrid=False),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
            title=None
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_sla, use_container_width=True)

    st.write("")

    # 3. DANH SÁCH CHI NHÁNH & BƯU CỤC CÓ TỶ LỆ QUÁ HẠN SLA (SORT: TIỀN ĐỀN BÙ -> TỶ LỆ QUÁ HẠN)
    st.markdown('<p class="section-red-title" style="border-left: 4px solid #c62828; padding-left: 8px; font-weight: bold;">DANH SÁCH CHI NHÁNH & BƯU CỤC CÓ TỶ LỆ QUÁ HẠN SLA</p>', unsafe_allow_html=True)

    # 1. Query danh sách Mã Tỉnh (Chi nhánh) thật từ DuckDB
    try:
        cn_real = con.execute(f"""
            SELECT DISTINCT tinh_phat AS cn 
            FROM orders 
            WHERE {where_sql_odr} AND tinh_phat IS NOT NULL AND tinh_phat != ''
            ORDER BY tinh_phat
        """).fetchall()
    except Exception:
        cn_real = []

    if not cn_real:
        cn_list = ['HNI', 'HCM', 'DNI', 'GLI', 'DLK', 'HPG', 'CTO']
    else:
        cn_list = [r[0] for r in cn_real]

    # 2. Query danh sách Bưu cục + Mã Tỉnh thật từ DuckDB
    try:
        bc_real = con.execute(f"""
            SELECT DISTINCT ma_buucuc_phat AS bc, tinh_phat AS cn 
            FROM orders 
            WHERE {where_sql_odr} AND tinh_phat IS NOT NULL AND ma_buucuc_phat IS NOT NULL AND ma_buucuc_phat != ''
            ORDER BY ma_buucuc_phat
        """).fetchall()
    except Exception:
        bc_real = []

    if not bc_real:
        bc_list = [
            ('HNI01', 'HNI'), ('HNI02', 'HNI'), ('HCM01', 'HCM'), ('HCM02', 'HCM'),
            ('DNI01', 'DNI'), ('DNI02', 'DNI'), ('GLI01', 'GLI'), ('GLI02', 'GLI')
        ]
    else:
        bc_list = [(r[0], r[1]) for r in bc_real]

    # Tạo dữ liệu fake kèm theo chỉ số cho Chi nhánh
    cn_data_items = []
    for idx, cn_code in enumerate(cn_list):
        mock_rate = max(1.5, round(5.8 - (idx % 5) * 0.4, 1))
        mock_diff = f"+{round(max(0.1, 2.4 - (idx % 5) * 0.3), 1)}%"
        mock_denbu = round(max(5.0, 42.0 - idx * 4.5), 1)
        cn_data_items.append({
            'cn': cn_code,
            'rate': mock_rate,
            'diff': mock_diff,
            'denbu': mock_denbu
        })

    # Sort Chi nhánh: Ưu tiên Tiền đền bù DESC -> Tỷ lệ quá hạn DESC
    cn_data_items = sorted(cn_data_items, key=lambda x: (x['denbu'], x['rate']), reverse=True)

    # Render HTML Chi nhánh
    rows_cn_sla_html = ""
    for item in cn_data_items:
        rows_cn_sla_html += f"""
        <tr class="cn-row" data-cn="{item['cn']}" onclick="filterBC('{item['cn']}', this)">
            <td style="font-weight: bold; cursor: pointer; text-align: left; padding-left: 10px;">{item['cn']}</td>
            <td style="text-align: center;">{item['rate']:.1f}%</td>
            <td class="text-red-bold" style="text-align: center;">{item['diff']}</td>
            <td style="text-align: right; padding-right: 10px;">{item['denbu']:.1f}</td>
        </tr>
        """

    # Tạo dữ liệu fake kèm theo chỉ số cho Bưu cục
    bc_data_items = []
    for idx, (bc_code, cn_code) in enumerate(bc_list):
        mock_rate = max(1.2, round(6.2 - (idx % 8) * 0.3, 1))
        mock_diff = f"+{round(max(0.1, 2.8 - (idx % 8) * 0.3), 1)}%"
        mock_denbu = round(max(3.0, 24.0 - (idx % 8) * 2.0), 1)
        bc_data_items.append({
            'bc': bc_code,
            'cn': cn_code,
            'rate': mock_rate,
            'diff': mock_diff,
            'denbu': mock_denbu
        })

    # Sort Bưu cục: Ưu tiên Tiền đền bù DESC -> Tỷ lệ quá hạn DESC
    bc_data_items = sorted(bc_data_items, key=lambda x: (x['denbu'], x['rate']), reverse=True)

    # Render HTML Bưu cục
    rows_bc_sla_html = ""
    for item in bc_data_items:
        rows_bc_sla_html += f"""
        <tr class="bc-row" data-cn="{item['cn']}">
            <td style="font-weight: bold; text-align: left; padding-left: 10px;">{item['bc']}</td>
            <td style="font-weight: bold; text-align: center;">{item['cn']}</td>
            <td style="text-align: center;">{item['rate']:.1f}%</td>
            <td class="text-red-bold" style="text-align: center;">{item['diff']}</td>
            <td style="text-align: right; padding-right: 10px;">{item['denbu']:.1f}</td>
        </tr>
        """

    interactive_sla_tables_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
            margin: 0; padding: 0; background: transparent; 
        }}
        .grid-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }}
        .table-title {{
            font-size: 12px; font-weight: bold; color: #333; margin-bottom: 6px;
        }}
        .table-scroll {{
            max-height: 360px;
            overflow-y: auto;
            border: 1px solid #d3d3d3;
            border-radius: 4px;
            background: #fff;
        }}
        table {{
            width: 100%; border-collapse: separate; border-spacing: 0; font-size: 11.5px;
        }}
        th {{
            position: sticky; top: 0; z-index: 10;
            background-color: #111111; color: #ffffff;
            text-align: center; padding: 7px 6px;
            border-bottom: 1px solid #444; border-right: 1px solid #444;
            font-weight: bold;
        }}
        td {{
            padding: 6px 6px; border-bottom: 1px solid #eee; border-right: 1px solid #eee;
            color: #111;
        }}
        tr.cn-row:hover {{
            background-color: #ffebee !important;
            cursor: pointer;
        }}
        tr.selected-cn {{
            background-color: #ffcdd2 !important;
        }}
        .text-red-bold {{ color: #c62828; font-weight: bold; background-color: #fff5f5; }}
        .btn-reset {{
            display: inline-block; padding: 2px 8px; font-size: 11px;
            background: #eee; border: 1px solid #ccc; border-radius: 3px;
            cursor: pointer; margin-left: 8px; font-weight: normal;
        }}
    </style>
    </head>
    <body>

    <div class="grid-container">
        <div>
            <div class="table-title">
                Bảng Chi Nhánh Quá Hạn <span style="font-weight:normal; color:#666;">(Bấm chọn dòng để lọc Bưu cục)</span>
                <span class="btn-reset" onclick="resetFilter()">Xóa lọc</span>
            </div>
            <div class="table-scroll">
                <table>
                    <thead>
                        <tr>
                            <th style="text-align: left; padding-left: 10px;">Chi nhánh</th>
                            <th>Tỷ lệ quá hạn</th>
                            <th>SS cùng kỳ</th>
                            <th style="text-align: right; padding-right: 10px;">Đền bù (tr.%)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_cn_sla_html}
                    </tbody>
                </table>
            </div>
        </div>

        <div>
            <div class="table-title">
                Bưu Cục Quá Hạn <span id="bc-title-status" style="color: #c62828; font-weight: bold;">(Toàn Quốc)</span>
            </div>
            <div class="table-scroll">
                <table>
                    <thead>
                        <tr>
                            <th style="text-align: left; padding-left: 10px;">Bưu cục</th>
                            <th>Chi nhánh</th>
                            <th>Tỷ lệ quá hạn</th>
                            <th>SS cùng kỳ</th>
                            <th style="text-align: right; padding-right: 10px;">Đền bù (tr.%)</th>
                        </tr>
                    </thead>
                    <tbody id="bc-tbody">
                        {rows_bc_sla_html}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        function filterBC(cnCode, rowElem) {{
            var cnRows = document.getElementsByClassName('cn-row');
            for (var i = 0; i < cnRows.length; i++) {{
                cnRows[i].classList.remove('selected-cn');
            }}
            if (rowElem) rowElem.classList.add('selected-cn');

            var bcRows = document.getElementsByClassName('bc-row');
            for (var j = 0; j < bcRows.length; j++) {{
                if (bcRows[j].getAttribute('data-cn') === cnCode) {{
                    bcRows[j].style.display = 'table-row';
                }} else {{
                    bcRows[j].style.display = 'none';
                }}
            }}
            document.getElementById('bc-title-status').innerText = '(Chi nhánh: ' + cnCode + ')';
        }}

        function resetFilter() {{
            var cnRows = document.getElementsByClassName('cn-row');
            for (var i = 0; i < cnRows.length; i++) {{
                cnRows[i].classList.remove('selected-cn');
            }}
            var bcRows = document.getElementsByClassName('bc-row');
            for (var j = 0; j < bcRows.length; j++) {{
                bcRows[j].style.display = 'table-row';
            }}
            document.getElementById('bc-title-status').innerText = '(Toàn Quốc)';
        }}
    </script>
    </body>
    </html>
    """

    components.html(interactive_sla_tables_html, height=410, scrolling=False)
