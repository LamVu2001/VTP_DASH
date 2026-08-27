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
                    <td>{fmt(val_bc)}</td><td>{fmt(val_bc)}</td><td class="text-green">+6.8%</td>
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


# ==========================================
# TAB 2: DASHBOARD OPR
# ==========================================
with tab_opr:
    st.markdown('<p class="header-title">CHẤT LƯỢNG KHÂU THU</p>', unsafe_allow_html=True)
    st.markdown('<p class="main-title">Dashboard OPR</p>', unsafe_allow_html=True)

    col_kpi_area, col_filter_area = st.columns([4.2, 1.8])

    with col_filter_area:
        f_opr1, f_opr2 = st.columns(2)
        with f_opr1: 
            filter_date_opr = st.date_input("NGÀY", value=(), key="opr_date")
            filter_dt_opr = st.selectbox("MÃ ĐỐI TÁC", dt_list, key="opr_dt")
            filter_ld_opr = st.selectbox("LOẠI ĐƠN", ["Tất cả"], key="opr_ld")
            filter_tl_opr = st.selectbox("TRỌNG LƯỢNG", ["Tất cả", "< 500g", "500g - 2kg", "> 2kg"], key="opr_tl")
        with f_opr2:
            filter_kh_opr = st.selectbox("MÃ KHÁCH HÀNG", kh_list, key="opr_kh")
            filter_kh2_opr = st.selectbox("MÃ KHÁCH HÀNG (2)", kh_list, key="opr_kh2")
            filter_tep_opr = st.selectbox("TỆP ĐƠN (YCT TTC PTC)", ["Tất cả"], key="opr_tep")

    where_clauses_opr = ["1=1"]
    if filter_dt_opr != "Tất cả": where_clauses_opr.append(f"ma_doitac = '{filter_dt_opr}'")
    if filter_kh_opr != "Tất cả": where_clauses_opr.append(f"ma_khgui = '{filter_kh_opr}'")
    if filter_kh2_opr != "Tất cả": where_clauses_opr.append(f"ma_khgui = '{filter_kh2_opr}'")
    if isinstance(filter_date_opr, tuple) and len(filter_date_opr) == 2:
        where_clauses_opr.append(f"clean_date BETWEEN '{filter_date_opr[0]}' AND '{filter_date_opr[1]}'")
    where_sql_opr = " AND ".join(where_clauses_opr)

    tong_sl_opr = con.execute(f"SELECT COUNT(*) FROM orders WHERE {where_sql_opr}").fetchone()[0]
    sl_hien_thi = tong_sl_opr if tong_sl_opr > 0 else 11180

    with col_kpi_area:
        k1, k2, k3, k4, k5, k6 = st.columns(6)
        with k1: st.markdown(f'<div class="metric-card"><div class="metric-title">SẢN LƯỢNG PHẢI THU</div><div class="metric-value">{sl_hien_thi:,.0f}</div><div class="metric-sub-green">▲ +6.8% vs Mục tiêu</div></div>', unsafe_allow_html=True)
        with k2: st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ THU TC</div><div class="metric-value">82.4%</div><div class="metric-sub-red">▼ -3.1% vs Mục tiêu</div></div>', unsafe_allow_html=True)
        with k3: st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ THU ĐG LẦN 1</div><div class="metric-value">82.4%</div><div class="metric-sub-red">▼ -3.1% vs Mục tiêu</div></div>', unsafe_allow_html=True)
        with k4: st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ THU ĐÚNG GIỜ</div><div class="metric-value">82.4%</div><div class="metric-sub-red">▼ -3.1% vs Mục tiêu</div></div>', unsafe_allow_html=True)
        with k5: st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ XUẤT SẠCH</div><div class="metric-value">2.4%</div><div class="metric-sub-red">▼ -3.1% vs Mục tiêu</div></div>', unsafe_allow_html=True)
        with k6: st.markdown('<div class="metric-card"><div class="metric-title">ĐƠN TỒN QUÁ HẠN >1 NGÀY</div><div class="metric-value">221</div><div class="metric-sub-red">▼ -3.1% vs Mục tiêu</div></div>', unsafe_allow_html=True)

    st.write("")

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
        
        # Query trực tiếp dữ liệu Mã đối tác & Mã khách hàng từ DB DuckDB
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

        # Tạo danh sách 10 dòng kết hợp
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
            .tbl-top10 {{ width: 100%; border-collapse: collapse; font-size: 11px; background: #fafafa; border: 1px solid #e0e0e0; }}
            .tbl-top10 th {{ background: #f0f0f0; color: #333; padding: 6px; text-align: center; font-weight: bold; border-bottom: 1px solid #ccc; }}
            .tbl-top10 td {{ padding: 5px 10px; border-bottom: 1px solid #eee; text-align: center; }}
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

    st.subheader("📍 DANH SÁCH CHI NHÁNH THU & BƯU CỤC THU (TƯƠNG TÁC TỰ ĐỘNG LỌC)")
    st.info("💡 Mẹo: Bấm chọn vào một dòng Chi nhánh ở bảng bên trái để xem đầy đủ các bưu cục thuộc chi nhánh đó ở bảng bên phải!")

    df_cn_opr_grouped = con.execute(f"""
        SELECT 
            tinh_phat AS "Chi nhánh Thu", 
            COUNT(*) AS "Tổng đơn thu", 
            ROUND(SUM(tong_cuoc)/1e6, 1) AS "Doanh thu (Tr)"
        FROM orders 
        WHERE {where_sql_opr} AND tinh_phat IS NOT NULL
        GROUP BY tinh_phat 
        ORDER BY "Tổng đơn thu" DESC
    """).fetchdf()

    tbl_opr_col1, tbl_opr_col2 = st.columns(2)
    with tbl_opr_col1:
        st.markdown("**Bảng Chi Nhánh Thu (Bấm chọn dòng để lọc Bưu cục)**")
        event_cn_opr = st.dataframe(
            df_cn_opr_grouped, 
            use_container_width=True, 
            hide_index=True,
            selection_mode="single-row",
            on_select="rerun",
            key="table_cn_thu_select"
        )

    selected_row_indices_opr = event_cn_opr.get("selection", {}).get("rows", [])
    selected_cn_opr = None
    if selected_row_indices_opr:
        selected_idx_opr = selected_row_indices_opr[0]
        selected_cn_opr = df_cn_opr_grouped.iloc[selected_idx_opr]["Chi nhánh Thu"]

    with tbl_opr_col2:
        if selected_cn_opr:
            st.markdown(f"**Toàn bộ Bưu cục thuộc Chi nhánh: <span style='color: #c62828;'>{selected_cn_opr}</span>**", unsafe_allow_html=True)
            df_bc_opr_filtered = con.execute(f"""
                SELECT 
                    ma_buucuc_phat AS "Mã bưu cục thu", 
                    COUNT(*) AS "Sản lượng đơn thu", 
                    ROUND(SUM(tong_cuoc)/1e6, 1) AS "Doanh thu (Tr)"
                FROM orders 
                WHERE {where_sql_opr} AND tinh_phat = '{selected_cn_opr}' AND ma_buucuc_phat IS NOT NULL
                GROUP BY ma_buucuc_phat 
                ORDER BY "Sản lượng đơn thu" DESC
            """).fetchdf()
            st.dataframe(df_bc_opr_filtered, use_container_width=True, hide_index=True)
        else:
            st.markdown("**Bưu Cục Thu Toàn Quốc (Bấm chọn Chi nhánh bên trái để xem chi tiết)**")
            df_bc_opr_all = con.execute(f"""
                SELECT 
                    tinh_phat AS "Chi nhánh Thu", 
                    ma_buucuc_phat AS "Mã bưu cục thu", 
                    COUNT(*) AS "Sản lượng đơn thu"
                FROM orders 
                WHERE {where_sql_opr} AND tinh_phat IS NOT NULL AND ma_buucuc_phat IS NOT NULL
                GROUP BY tinh_phat, ma_buucuc_phat 
                ORDER BY "Sản lượng đơn thu" DESC
            """).fetchdf()
            st.dataframe(df_bc_opr_all, use_container_width=True, hide_index=True)


# ==========================================
# TAB 3: DASHBOARD ODR
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

    # 1. DANH SÁCH TỈNH PHÁT & BƯU CỤC
    st.subheader("📍 DANH SÁCH TỈNH PHÁT & BƯU CỤC (TƯƠNG TÁC TỰ ĐỘNG LỌC)")
    st.info("💡 Mẹo: Bấm chọn vào một dòng Tỉnh ở bảng bên trái để xem đầy đủ các bưu cục thuộc tỉnh đó ở bảng bên phải!")

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

    # 2. BÁO CÁO MA TRẬN CHẤT LƯỢNG VẬN HÀNH
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
