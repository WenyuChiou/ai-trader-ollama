"""
交易日检查工具
排除周末和节假日，只返回真正的交易日
"""
from datetime import date, datetime, timedelta
from typing import Optional, List


# 美国股市主要节假日（固定日期）
US_MARKET_HOLIDAYS = {
    # 固定日期节假日（每年相同）
    (1, 1): "New Year's Day",  # 元旦
    (7, 4): "Independence Day",  # 独立日
    (12, 25): "Christmas Day",  # 圣诞节
}

# 美国股市主要节假日（需要根据年份计算，如感恩节是11月第4个周四）
def get_variable_holidays(year: int) -> List[date]:
    """获取可变日期的节假日（如感恩节、劳动节等）"""
    holidays = []
    
    # 感恩节：11月第4个周四
    # 从11月1日开始，找到第一个周四，然后加3周
    nov_1 = date(year, 11, 1)
    first_thursday = nov_1 + timedelta(days=(3 - nov_1.weekday()) % 7)
    thanksgiving = first_thursday + timedelta(weeks=3)
    holidays.append(thanksgiving)
    
    # 劳动节：9月第1个周一
    sep_1 = date(year, 9, 1)
    first_monday = sep_1 + timedelta(days=(0 - sep_1.weekday()) % 7)
    labor_day = first_monday
    holidays.append(labor_day)
    
    # 阵亡将士纪念日：5月最后1个周一
    may_31 = date(year, 5, 31)
    last_monday = may_31 - timedelta(days=(may_31.weekday() - 0) % 7)
    memorial_day = last_monday
    holidays.append(memorial_day)
    
    # 马丁路德金日：1月第3个周一
    jan_1 = date(year, 1, 1)
    first_monday = jan_1 + timedelta(days=(0 - jan_1.weekday()) % 7)
    mlk_day = first_monday + timedelta(weeks=2)
    holidays.append(mlk_day)
    
    # 总统日：2月第3个周一
    feb_1 = date(year, 2, 1)
    first_monday = feb_1 + timedelta(days=(0 - feb_1.weekday()) % 7)
    presidents_day = first_monday + timedelta(weeks=2)
    holidays.append(presidents_day)
    
    # 哥伦布日：10月第2个周一
    oct_1 = date(year, 10, 1)
    first_monday = oct_1 + timedelta(days=(0 - oct_1.weekday()) % 7)
    columbus_day = first_monday + timedelta(weeks=1)
    holidays.append(columbus_day)
    
    return holidays


def is_trading_day(check_date: Optional[date] = None) -> bool:
    """
    检查指定日期是否是交易日（排除周末和节假日）
    
    参数:
    - check_date: 要检查的日期（如果为None，使用今天）
    
    返回:
    - True if trading day, False otherwise
    """
    if check_date is None:
        check_date = date.today()
    
    # 检查是否是周末（周六=5, 周日=6）
    if check_date.weekday() >= 5:
        return False
    
    # 检查是否是固定日期节假日
    month_day = (check_date.month, check_date.day)
    if month_day in US_MARKET_HOLIDAYS:
        return False
    
    # 检查是否是可变日期节假日
    variable_holidays = get_variable_holidays(check_date.year)
    if check_date in variable_holidays:
        return False
    
    return True


def get_next_trading_day(start_date: Optional[date] = None, days_ahead: int = 1) -> date:
    """
    获取下一个交易日
    
    参数:
    - start_date: 起始日期（如果为None，使用今天）
    - days_ahead: 向前查找多少天（默认1，即下一个交易日）
    
    返回:
    - 下一个交易日
    """
    if start_date is None:
        start_date = date.today()
    
    current = start_date
    found = 0
    
    while found < days_ahead:
        current += timedelta(days=1)
        if is_trading_day(current):
            found += 1
    
    return current


def is_market_open(check_datetime: Optional[datetime] = None) -> bool:
    """
    检查市场是否开盘（美股：周一至周五 9:30 AM - 4:00 PM EST，排除节假日）
    
    参数:
    - check_datetime: 要检查的日期时间（如果为None，使用当前时间）
    
    返回:
    - True if market is open, False otherwise
    """
    if check_datetime is None:
        check_datetime = datetime.now()
    
    # 检查是否是交易日（排除周末和节假日）
    check_date = check_datetime.date()
    if not is_trading_day(check_date):
        return False
    
    # 检查时间（使用本地时间，假设服务器在EST时区或用户配置的时区）
    from datetime import time as dt_time
    market_open = dt_time(9, 30)  # 9:30 AM
    market_close = dt_time(16, 0)  # 4:00 PM
    current_time = check_datetime.time()
    
    return market_open <= current_time <= market_close

