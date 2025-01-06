import gspread
from datetime import datetime

def format_so_tien(so_tien):
    return f"{so_tien:,.0f}".replace(",", ".") + "đ"

def tong_ket_thu_chi(sheet):
    # Lấy tất cả dữ liệu trong sheet
    records = sheet.get_all_values()[1:]  # Bỏ qua dòng tiêu đề
    tong_thu = 0
    tong_chi = 0
    chi_most = {"mo_ta": "", "so_tien": 0}
    chi_theo_mo_ta = {}

    # Debug: In ra tất cả các records
    # print("Records:", records)

    for record in records:
        chi_thu = record[1]
        so_tien_str = record[2].replace('đ', '').replace('.', '').strip()
        
        # Debug: Kiểm tra dữ liệu số tiền
        # print(f"Processing record: {record}")
        # print(f"Raw amount: {so_tien_str}")
        
        try:
            so_tien = float(so_tien_str)
        except ValueError:
            print(f"Error converting amount: {so_tien_str}")
            continue  # Bỏ qua nếu không thể chuyển đổi số tiền
        mo_ta = record[4]

        if chi_thu == "Thu":
            tong_thu += so_tien
        elif chi_thu == "Chi":
            tong_chi += so_tien
            if so_tien > chi_most["so_tien"]:
                chi_most = {"mo_ta": mo_ta, "so_tien": so_tien}
            
            # Cập nhật tổng chi theo mô tả
            if mo_ta in chi_theo_mo_ta:
                chi_theo_mo_ta[mo_ta] += so_tien
            else:
                chi_theo_mo_ta[mo_ta] = so_tien

    # Debug: In ra thông tin chi theo mô tả
    # print("Chi theo mo ta:", chi_theo_mo_ta)

    # Sắp xếp các mô tả chi theo tổng chi giảm dần
    sorted_chi_theo_mo_ta = sorted(chi_theo_mo_ta.items(), key=lambda x: x[1], reverse=True)

    # Mô tả có tổng chi cao nhất
    top_mo_ta = sorted_chi_theo_mo_ta[0] if sorted_chi_theo_mo_ta else ("", 0)

    #  Debug: In ra mô tả chi tiêu có tổng chi cao nhất
    # print(f"Top chi theo mo ta: {top_mo_ta}")

    # Gửi thông báo tổng kết
    total_message = f"Tổng Thu: {format_so_tien(tong_thu)}\nTổng Chi: {format_so_tien(tong_chi)}"
    
    if chi_most["so_tien"] > 0:
        total_message += f"\nKhoản Chi Nhiều Nhất: {format_so_tien(chi_most['so_tien'])} - {chi_most['mo_ta']}"
    
    if top_mo_ta[1] > 0:
        total_message += f"\nMô tả chi tiêu có tổng chi cao nhất: {top_mo_ta[0]} - {format_so_tien(top_mo_ta[1])}"

    # print(f"Total summary: {total_message}")  
    # print(f"Total summary: {format_so_tien(top_mo_ta[1])}")

    return total_message
