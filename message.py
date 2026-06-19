from data import *
from datetime import datetime

today = datetime.now().date()
schedule_data_from_file = read_file()

if not schedule_data_from_file:
    result = get_result(today)
    write_file(result)  # Ghi file (không cần chờ)
    schedule_data_from_file = result  # Dùng luôn dữ liệu vừa lấy
else:
    schedule_data_from_file = json.loads(schedule_data_from_file)  # Dùng dữ liệu đã đọc


# Hàm lấy lịch học 1 ngày, áp dụng cho chức năng gửi lịch học mỗi ngày
def get_schedule_daily():
    check_date_exist(today)
    week_day = today.weekday()
    schedule_today_data = schedule_data_from_file[week_day]

    if schedule_today_data and isinstance(schedule_today_data, dict):
        classes = []
        message = f"Lịch học hôm nay thứ ({schedule_today_data['thu']})\nNgày: {date.strftime(today, "%d/%m/%Y")}\n"

        for i in range(len(schedule_today_data["chitietbuoihoc"])):
            message += f"\nBuổi: {schedule_today_data["chitietbuoihoc"][i]["buoi"]}"
            classes = schedule_today_data["chitietbuoihoc"][i]["monhoc"]
            for j in range(len(classes)):
                message += (
                    f"{"\nTiết học tạm ngưng" if classes[j].get('tamngung', '') == True else ""}\n"
                    f"Tên môn học: {classes[j]['tenmonhoc']}\n"
                    f"Mã lớp: {classes[j]['malop']}\n"
                    f"Tiết: {classes[j]['tiet']}\n"
                    f"Giờ: {classes[j]['gio']}\n"
                    f"Phòng: {classes[j]['phong']}\n"
                    f"Giáo viên: {classes[j]['gv']}\n"
                )
        return message
    return "Không có lịch, có lỗi xảy ra"
