import streamlit as st
import duckdb
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import gdown

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

    .top-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
    }
    .top-table th {
        background-color: #f4f6f8;
        padding: 6px;
        border: 1px solid #e0e0e0;
        text-align: left;
    }
    .top-table td {
        padding: 6px;
        border: 1px solid #e0e0e0;
    }
    .val-red {
        color: #c62828;
        font-weight: bold;
        text-align: right;
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

con = get_db_connection()

@st.cache_data
def get_filter_options():
    kh_list = ["Tất cả"] + [row[0] for row in con.execute("SELECT DISTINCT ma_khgui FROM orders WHERE ma_khgui IS NOT NULL ORDER BY 1").fetchall()]
    tinh_list = ["Tất cả"] + [row[0] for row in con.execute("SELECT DISTINCT tinh_phat FROM orders WHERE tinh_phat IS NOT NULL ORDER BY 1").fetchall()]
    dt_list = ["Tất cả"] + [row[0] for row in con.execute("SELECT DISTINCT ma_doitac FROM orders WHERE ma_doitac IS NOT NULL ORDER BY 1").fetchall()]
    return kh_list, tinh_list, dt_list

kh_list, tinh_list, dt_list = get_filter_options()

tab_doanh_thu, tab_opr, tab_odr = st.tabs(["📊 DASHBOARD DOANH THU", "📦 DASHBOARD OPR", "🚚 DASHBOARD ODR"])

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
                st.plotly_chart(fig, width='stretch')
        except Exception:
            pass

    with c_top:
        st.subheader("TOP 10 KHÁCH HÀNG GIẢM DOANH THU")
        df_top = con.execute(f"""
            SELECT ma_khgui AS "MÃ KH", ROUND(SUM(tong_cuoc)/1e6, 1) AS "DOANH THU (TR)" 
            FROM orders WHERE {where_sql_dt} AND ma_khgui IS NOT NULL 
            GROUP BY ma_khgui ORDER BY "DOANH THU (TR)" DESC LIMIT 10
        """).fetchdf()
        st.dataframe(df_top, width='stretch', hide_index=True, height=380)

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

    st.html(matrix_dt_html)


# ==========================================
# TAB 2: DASHBOARD OPR
# ==========================================
with tab_opr:
    st.markdown('<p class="header-title">CHẤT LƯỢNG KHÂU THU</p>', unsafe_allow_html=True)
    st.markdown('<p class="main-title">Dashboard OPR</p>', unsafe_allow_html=True)

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
        st.plotly_chart(fig_opr, width='stretch')

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
        max_len = max(len(top_dt_data), len(top_kh_data))
        for i in range(max_len):
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

        top_table_html = f"""
        <table class="top-table">
            <thead>
                <tr>
                    <th>MÃ ĐỐI TÁC</th><th style="text-align:right;">SL TỒN</th>
                    <th>MÃ KHÁCH HÀNG</th><th style="text-align:right;">SL TỒN</th>
                </tr>
            </thead>
            <tbody>
                {rows_top_html}
            </tbody>
        </table>
        """
        st.markdown(top_table_html, unsafe_allow_html=True)

# Placeholder for TAB 3 (ODR)
with tab_odr:
    st.markdown('<p class="header-title">CHẤT LƯỢNG KHÂU PHÁT</p>', unsafe_allow_html=True)
    st.markdown('<p class="main-title">Dashboard ODR</p>', unsafe_allow_html=True)
