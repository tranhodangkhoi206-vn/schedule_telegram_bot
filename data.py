# %%
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, date
import os

# %%
session = requests.Session()
session.headers.update(
    {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://sinhvien.bvu.edu.vn/lich-theo-tuan.html",
        "User-Agent": "Mozilla/5.0",
        "Cookie": "ASC.AUTH=2177467C9B3872F6A43B64A903A0AAB7DC51035EEFF3C393A8991A33AD05810C59A67B927E3BD846ED68C0B40C3F3C4E1207A6D092C3D46806EB060C235432104B994337478553BF9DB5056BFD67DA175DE1CF2EACF51F9DCDC8FDC4C3562F130B4FC377E78815CFFEE71601A10375A067C60BC407A3AF20C5D706574F57F62C",
    }
)


# %%
def get_raw_schedule_from_web(ngayhientai):
    response = session.post(
        "https://sinhvien.bvu.edu.vn/SinhVien/GetDanhSachLichTheoTuan",
        data={"pNgayHienTai": {ngayhientai}, "pLoaiLich": 0},
    )
    return response.text


def process_date(soup):
    header = soup[0].find_all("th")
    header = [th.text for th in header]
    header.pop(0)
    header = [i[-10:] for i in header]
    return header


# %%
def process_class(buoi, soup):
    body = soup[0].find_all("tr")
    body.pop(0)
    tds = body[buoi].find_all("td")
    tds = [i.text.replace(":\n", ": ").strip().split("\n") for i in tds]
    tds[0] = tds[0][0]
    for i in range(1, len(tds)):
        tds[i] = [" ".join(x.split()) for x in tds[i] if x != ""]
        if len(tds[i]) > 7:
            tds[i].insert(6 if len(tds[i]) < 13 else 7, "|")
        tds[i] = [x.split(": ") for x in tds[i]]
    return tds


raw_data = get_raw_schedule_from_web(datetime.now().date())
soup = BeautifulSoup(raw_data, "html.parser")
soup = soup.select(".table-responsive")
process_class(1, soup)
# %%


def process_data_clearly(data):
    for i in range(1, len(data)):
        for j in range(0, len(data[i])):
            if data[i][j] == "Tạm ngưng":
                continue
            if len(data[i][j]) > 1:
                tmp = data[i][j][1]
                data[i][j] = tmp
            else:
                tmp = data[i][j][0]
                data[i][j] = tmp
    return data


def create_class(data):
    danh_sach_mon_hoc = []
    tam_ngung = False
    num = 0

    if data[0] == "Tạm ngưng":
        tam_ngung = True
        num = 1
    mon_hoc = {
        "tamngung": tam_ngung,
        "tenmonhoc": data[0 + num],
        "malop": data[1 + num],
        "tiet": data[2 + num],
        "gio": data[3 + num],
        "phong": data[4 + num],
        "gv": data[5 + num],
    }
    danh_sach_mon_hoc.append(mon_hoc)
    if len(data) > 7:
        mon_hoc = {
            "tenmonhoc": data[7 + num],
            "malop": data[8 + num],
            "tiet": data[9 + num],
            "gio": data[10 + num],
            "phong": data[11 + num],
            "gv": data[12 + num],
        }
        danh_sach_mon_hoc.append(mon_hoc)
    return danh_sach_mon_hoc


def process_raw_data_to_dist(header, soup):
    schedule = []
    schedule_weekday_array = []
    for date in range(0, len(header)):
        week_day = str(date + 2)
        if week_day == "8":
            week_day = "cn"
        schedule_weekday_array = [
            {"thu": week_day, "ngay": str(header[date]), "chitietbuoihoc": []}
        ]
        for buoi in range(3):
            classes = []
            classes_session = process_data_clearly(process_class(buoi, soup))
            if classes_session[date + 1] != []:
                classes = create_class(classes_session[date + 1])
            schedule_weekday_array[0]["chitietbuoihoc"].append(
                {"buoi": classes_session[0], "monhoc": classes}
            )
        schedule.append(schedule_weekday_array[0])
    return schedule


def get_result(date_get_data):
    raw_data = get_raw_schedule_from_web(date_get_data)
    soup = BeautifulSoup(raw_data, "html.parser")
    soup = soup.select(".table-responsive")
    header = process_date(soup)
    result = process_raw_data_to_dist(header, soup)
    return result


def write_file(data):
    # Lấy đường dẫn hiện tại
    base_dir = os.path.dirname(__file__)
    # Nối đường dẫn hiện tại với đuôi là file
    data_path = os.path.join(base_dir, "schedule_data.json")
    with open(data_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False))


def read_file():
    # Lấy đường dẫn hiện tại
    base_dir = os.path.dirname(__file__)
    # Nối đường dẫn hiện tại với đuôi là file
    data_path = os.path.join(base_dir, "schedule_data.json")
    with open(data_path, "r", encoding="utf-8") as f:
        data = f.read()
    return data

#%%
def check_date_exist(date_check: date):
    date_check_str = date_check.strftime("%d/%m/%Y")
    schedule = json.loads(read_file()) if read_file() else {}
    schedule_exist = [i for i in schedule if i["ngay"] == date_check_str]
    if not schedule_exist:
        result = get_result(date_check_str)
        write_file(result)
    return json.loads(read_file())

# %%
