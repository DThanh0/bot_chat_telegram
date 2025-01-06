import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from sheet_utils import format_so_tien, tong_ket_thu_chi

# ---- 1. Đọc cấu hình từ file JSON ----
def load_config():
    with open('config.json') as f:
        return json.load(f)

config = load_config()

TELEGRAM_TOKEN = config['TELEGRAM_TOKEN']
SERVICE_ACCOUNT_FILE = config['SERVICE_ACCOUNT_FILE']
SPREADSHEET_ID = config['SPREADSHEET_ID']  # Đây là ID của file Excel mặc định

# ---- 2. Kết nối Google Sheets ----
# Xác thực
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(credentials)

# ---- 6. Xử lý tin nhắn từ Telegram ----
async def handle_message(update, context):
    print("Received message:", update.message.text)
    text = update.message.text
    chat_id = update.effective_chat.id

    user_id = update.message.from_user.id
    username = update.message.from_user.username

    print(f"Message received from user ID: {user_id}, Username: {username}")
    # Kiểm tra nếu username là DyThanh thì vào sheet 2
    if user_id == 7150662446 or username == "phanlangthang":
        sheet_id = 1389421779  # ID của sheet 'Bảng tính tiền 2'
    elif user_id == 1340827354 or username == "DyThah":
        sheet_id = 2081460259  # ID của sheet 'Bảng tính tiền 3'
    else:
        sheet_id = 0  # ID của sheet mặc định (sheet 1)

    # Mở bảng tính theo ID của sheet
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.get_worksheet_by_id(sheet_id)  # Lấy sheet theo ID

    # Print statement to see which sheet the user is writing to
    print(f"User {username} is writing to sheet ID: {sheet_id}")

    try:
        if text.startswith('-') or text.startswith('+'):
            chi_thu = "Chi" if text.startswith('-') else "Thu"

            parts = text.split(' ', 1)
            so_tien = parts[0]
            mo_ta = parts[1] if len(parts) > 1 else ""

            # Làm sạch chuỗi số tiền và chuyển đổi sang float
            so_tien = so_tien.replace('k', '000').replace('tr', '000000').replace('.', '').replace('đ', '').strip()

            try:
                so_tien = float(so_tien)
            except ValueError:
                await update.message.reply_text("Lỗi: Không thể chuyển đổi số tiền.")
                return

            # Định dạng số tiền
            formatted_so_tien = format_so_tien(so_tien)
            ngay_gio = datetime.now().strftime('%H:%M - %d/%m/%Y ')
            last_row = len(sheet.get_all_values())
            stt = last_row

            sheet.append_row([stt, chi_thu, so_tien, ngay_gio, mo_ta])

            await update.message.reply_text(f"Thủ quỷ đã ghi: {chi_thu} {formatted_so_tien} - {mo_ta}")

            # Sau khi thêm xong, kiểm tra tổng số dòng
            if last_row % 30 == 0:
                # Nếu có đủ 30 dòng, tổng kết lại
                tong_ket_message = tong_ket_thu_chi(sheet)
                await update.message.reply_text(tong_ket_message)
        else:
            await update.message.reply_text("Vui lòng nhập đúng cú pháp: '-15k tiền ăn' hoặc '+500k lương'")
    except Exception as e:
        await update.message.reply_text(f"Lỗi: {str(e)}")

# ---- 7. Thiết lập bot Telegram ----
async def start(update, context):
    instructions = (
        "Xin chào, tôi là bot của bạn!\n\n"
        "Dưới đây là các lệnh bạn có thể sử dụng:\n"
        "/start - Hiển thị tin nhắn này\n"
        "/tong_bang - Liệt kê tất cả các bảng tính\n"
        "/tinh_tong <tiêu chí> - Tính tổng số tiền dựa trên tiêu chí (ví dụ: 'Thu' hoặc 'Chi')\n"
        "/tong_tien_cua <mô tả> - Tính tổng số tiền dựa trên mô tả\n"
        "/xoa_data - Xoá data của bảng tính\n"
        "Bạn cũng có thể gửi tin nhắn theo định dạng '-15k tiền ăn' hoặc '+500k lương' để ghi lại chi tiêu hoặc thu nhập."
    )
    await update.message.reply_text(instructions)

# ---- 8. Lấy danh sách tất cả các trang tính ----
def list_all_sheets(spreadsheet_id):
    spreadsheet = gc.open_by_key(spreadsheet_id)
    sheets = spreadsheet.worksheets()
    sheet_info = [(sheet.title, sheet.id) for sheet in sheets]
    print("All sheet names and IDs:", sheet_info)
    return sheet_info

# ---- 9. Xử lý lệnh /tong_bang từ Telegram ----
async def tong_bang(update, context):
    sheet_info = list_all_sheets(SPREADSHEET_ID)
    count_message = f"Số lượng bảng tính hiện tại: {len(sheet_info)}\nDanh sách bảng tính:\n" + "\n".join([f"{name} (ID: {id})" for name, id in sheet_info])
    await update.message.reply_text(count_message)

# ---- 10. Tính tổng tiền theo mô tả hoặc loại ----
async def tinh_tong(update, context):
    args = context.args
    if not args:
        await update.message.reply_text("Vui lòng nhập mô tả hoặc loại (ví dụ: 'Thu' hoặc 'Chi').")
        return

    criteria = args[0].lower()
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    # Kiểm tra nếu username là DyThanh thì vào sheet 2
    if user_id == 7150662446 or username == "phanlangthang":
        sheet_id = 1389421779  # ID của sheet 'Bảng tính tiền 2'
    elif user_id == 1340827354 or username == "DyThah":
        sheet_id = 2081460259  # ID của sheet 'Bảng tính tiền 3'
    else:
        sheet_id = 0  # ID của sheet mặc định (sheet 1)

    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.get_worksheet_by_id(sheet_id)  # Lấy sheet theo ID

    records = sheet.get_all_records()
    total = 0

    for record in records:
        if 'Loại' in record and 'Mô Tả' in record:
            if criteria in record['Loại'].lower() or criteria in record['Mô Tả'].lower():
                # Clean and convert the amount to float
                so_tien = record['Số Tiền'].replace('đ', '').replace('.', '').replace('-', '').strip()
                try:
                    so_tien = float(so_tien)
                except ValueError:
                    continue
                total += so_tien if record['Loại'].lower() == 'thu' else -so_tien

    formatted_total = format_so_tien(total)
    await update.message.reply_text(f"Tổng số tiền cho '{criteria}': {formatted_total}")

# ---- 11. Tính tổng tiền theo mô tả ----
async def tong_tien_cua(update, context):
    args = context.args
    if not args:
        await update.message.reply_text("Vui lòng nhập mô tả.")
        return

    description = " ".join(args).lower()  # Join all arguments to form the full description
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    # Kiểm tra nếu username là DyThanh thì vào sheet 2
    if user_id == 7150662446 or username == "phanlangthang":
        sheet_id = 1389421779  # ID của sheet 'Bảng tính tiền 2'
    elif user_id == 1340827354 or username == "DyThah":
        sheet_id = 2081460259  # ID của sheet 'Bảng tính tiền 3'
    else:
        sheet_id = 0  # ID của sheet mặc định (sheet 1)

    print(f"Using sheet ID: {sheet_id}")

    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.get_worksheet_by_id(sheet_id)  # Lấy sheet theo ID

    records = sheet.get_all_records()
    total = 0

    for record in records:
        if 'Mô Tả' in record:
            if description in record['Mô Tả'].lower():
                # Clean and convert the amount to float
                so_tien = record['Số Tiền'].replace('đ', '').replace('.', '').replace('-', '').strip()
                try:
                    so_tien = float(so_tien)
                except ValueError:
                    continue
                total += so_tien if record['Loại'].lower() == 'thu' else -so_tien

    formatted_total = format_so_tien(total)
    await update.message.reply_text(f"Tổng số tiền cho mô tả '{description}': {formatted_total}")

#--- xoá dữ liệu đã nhập theo user
async def clear_data(update, context):
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    # Kiểm tra nếu username là DyThanh thì vào sheet 2
    if user_id == 7150662446 or username == "phanlangthang":
        sheet_id = 1389421779  # ID của sheet 'Bảng tính tiền 2'
    elif user_id == 1340827354 or username == "DyThah":
        sheet_id = 2081460259  # ID của sheet 'Bảng tính tiền 3'
    else:
        sheet_id = 0  # ID của sheet mặc định (sheet 1)

    print(f"Clearing data for sheet ID: {sheet_id}")

    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.get_worksheet_by_id(sheet_id)  # Lấy sheet theo ID

    try:
        # Xóa dữ liệu trong các cột cụ thể (các cột từ A đến E)
        sheet.batch_clear(['A2:E'])  # Xóa tất cả dữ liệu từ dòng 2 trở đi trong các cột STT -> Mô tả
        await update.message.reply_text("Dữ liệu đã được xóa thành công.")
    except Exception as e:
        await update.message.reply_text(f"Lỗi khi xóa dữ liệu: {str(e)}")

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    print("Bot is starting...")
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("tong_bang", tong_bang))
    application.add_handler(CommandHandler("tinh_tong", tinh_tong))
    application.add_handler(CommandHandler("tong_tien_cua", tong_tien_cua))
    application.add_handler(CommandHandler("xoa_data", clear_data))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # List all sheets in the default spreadsheet
    list_all_sheets(SPREADSHEET_ID)

    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
