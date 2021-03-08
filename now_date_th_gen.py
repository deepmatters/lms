import datetime

# Function to generate date in Thai
def gen_date_th():
    now = datetime.datetime.now()
    now_year_th = now.year + 543

    if now.month == 1:
        now_month_th = "มกราคม"
    elif now.month == 2:
        now_month_th = "กุมภาพันธ์"
    elif now.month == 3:
        now_month_th = "มีนาคม"
    elif now.month == 4:
        now_month_th = "เมษายน"
    elif now.month == 5:
        now_month_th = "พฤษภาคม"
    elif now.month == 6:
        now_month_th = "มิถุนายน"
    elif now.month == 7:
        now_month_th = "กรกฎาคม"
    elif now.month == 8:
        now_month_th = "สิงหาคม"
    elif now.month == 9:
        now_month_th = "กันยายน"
    elif now.month == 10:
        now_month_th = "ตุลาคม"
    elif now.month == 11:
        now_month_th = "พฤศจิกายน"
    elif now.month == 12:
        now_month_th = "ธันวาคม"

    now_day_th = now.day
    now_date_th = str(now_day_th) + " " + now_month_th + " " + str(now_year_th)

    return now_date_th