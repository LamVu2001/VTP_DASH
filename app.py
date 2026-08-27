# --- 2. BẢNG MA TRẬN VẬN HÀNH TÍCH HỢP HTML EXPAND TRỰC TIẾP ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📊 BÁO CÁO MA TRẬN PHÂN CẤP VẬN HÀNH (HTML EXPAND)")
    st.info("💡 Bấm vào dấu `[+]` ngay trên dòng của từng Tỉnh để mở rộng xem danh sách bưu cục con trực tiếp trong bảng.")

    # Lấy danh sách các tỉnh phát theo sản lượng giảm dần
    df_tins_list = con.execute(f"""
        SELECT tinh_phat, COUNT(*) as sl 
        FROM orders 
        WHERE {where_sql_odr} AND tinh_phat IS NOT NULL 
        GROUP BY tinh_phat 
        ORDER BY sl DESC 
        LIMIT 10
    """).fetchall()

    tinh_rows_html = ""
    for tinh_item, sl_tinh in df_tins_list:
        # Lấy danh sách bưu cục con của tỉnh
        df_bc_list = con.execute(f"""
            SELECT ma_buucuc_phat, COUNT(*) as sl_bc 
            FROM orders 
            WHERE {where_sql_odr} AND tinh_phat = '{tinh_item}' AND ma_buucuc_phat IS NOT NULL 
            GROUP BY ma_buucuc_phat 
            ORDER BY sl_bc DESC 
            LIMIT 5
        """).fetchall()

        sub_trs = ""
        for bc_code, bc_sl in df_bc_list:
            sub_trs += f"""
                <tr class="sub-row">
                    <td style="padding-left: 35px; border-top: 1px dashed #ddd;">↳ Bưu cục: <b>{bc_code}</b></td>
                    <td class="text-center" style="border-top: 1px dashed #ddd;">-</td>
                    <td class="text-center" style="border-top: 1px dashed #ddd;">-</td>
                    <td colspan="7" class="text-right" style="border-top: 1px dashed #ddd;">{bc_sl:,.0f} đơn</td>
                    <td class="text-center text-green" style="border-top: 1px dashed #ddd;">+2.1%</td>
                    <td colspan="5" class="text-right" style="border-top: 1px dashed #ddd;">{bc_sl:,.0f} đơn</td>
                    <td class="text-center text-green" style="border-top: 1px dashed #ddd;">+1.5%</td>
                    <td class="text-right" style="border-top: 1px dashed #ddd;">-</td>
                    <td class="text-right" style="border-top: 1px dashed #ddd;">{bc_sl:,.0f}</td>
                    <td class="text-center text-green" style="border-top: 1px dashed #ddd;">+3.2%</td>
                </tr>
            """

        # Đóng gói chuẩn xác bằng thẻ details nằm trọn trong 1 hàng colspan lớn
        tinh_rows_html += f"""
            <tr class="row-group">
                <td colspan="19" style="padding: 4px 8px;">
                    <details>
                        <summary style="cursor: pointer; font-weight: bold; color: #111;">
                            <span style="color: #c62828; font-weight: bold;">[+]</span> Khu vực Tỉnh phát: <b>{tinh_item}</b> &nbsp;&nbsp;&nbsp; (Tổng: {sl_tinh:,.0f} đơn)
                        </summary>
                        <table style="width: 100%; margin-top: 5px; border-collapse: collapse; background-color: #fafafa;">
                            {sub_trs}
                        </table>
                    </details>
                </td>
            </tr>
        """

    matrix_html = f"""
    <table class="matrix-table">
        <thead>
            <tr>
                <th rowspan="2" style="width: 22%;">Chỉ tiêu / Khu vực</th>
                <th rowspan="2" style="width: 6%;">Mục tiêu</th>
                <th rowspan="2" style="width: 6%;">Kết quả thực hiện</th>
                <th colspan="8" style="background-color: #2a2a2a;">7 ngày gần nhất</th>
                <th colspan="6" style="background-color: #333333;">5 tuần gần nhất</th>
                <th colspan="3" style="background-color: #2a2a2a;">Tháng</th>
            </tr>
            <tr>
                <th>D-6</th><th>D-5</th><th>D-4</th><th>D-3</th><th>D-2</th><th>D-1</th><th>Hôm nay</th><th style="color: #ff5252;">DoD</th>
                <th>W1</th><th>W2</th><th>W3</th><th>W4</th><th>W5</th><th style="color: #ff5252;">WoW</th>
                <th>M-1</th><th>M</th><th style="color: #ff5252;">MoM</th>
            </tr>
        </thead>
        <tbody>
            <tr class="row-group" style="background-color: #eaeaea;">
                <td><b>📦 TỔNG HỢP TOÀN HỆ THỐNG</b></td>
                <td class="text-center">-</td>
                <td class="text-center">100%</td>
                <td colspan="7" class="text-right"><b>{total_m:,.0f} đơn</b></td>
                <td class="text-center text-green">+5.22%</td>
                <td colspan="5" class="text-right"><b>{total_m:,.0f} đơn</b></td>
                <td class="text-center text-green">+5.22%</td>
                <td class="text-right">-</td>
                <td class="text-right"><b>{total_m:,.0f}</b></td>
                <td class="text-center text-green">+5.22%</td>
            </tr>
            {tinh_rows_html}
        </tbody>
    </table>
    """

    st.markdown(matrix_html, unsafe_allow_html=True)
