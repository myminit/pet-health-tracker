import calendar
from datetime import date


def get_calendar_context(request, appointment_dates=None):
    today = date.today()

    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    if appointment_dates is None:
        appointment_dates = set()

    _, days_in_month = calendar.monthrange(year, month)
    first_weekday = calendar.monthrange(year, month)[0]
    offset = (first_weekday + 1) % 7

    calendar_days = [
        {
            'date': d,
            'full_date': f"{year}-{month:02d}-{d:02d}",
            'has_dot': d in appointment_dates,
            'is_today': (today.year == year and today.month == month and today.day == d),
        }
        for d in range(1, days_in_month + 1)
    ]

    thai_months = [
        '', 'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน',
        'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'
    ]

    prev_month = month - 1 if month > 1 else 12
    prev_year  = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year  = year if month < 12 else year + 1

    return {
        'calendar_days': calendar_days,
        'calendar_offset': range(offset),
        'calendar_title': f'{thai_months[month]} {year + 543}',
        'prev_url': f'?year={prev_year}&month={prev_month}',
        'next_url': f'?year={next_year}&month={next_month}',
        'day_headers': ['อา', 'จ', 'อ', 'พ', 'พฤ', 'ศ', 'ส'],
    }