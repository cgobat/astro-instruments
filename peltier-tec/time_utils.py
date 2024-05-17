import rtc
import time
import wifi
import adafruit_ntp
import socketpool

EPOCH = time.mktime(time.struct_time((2000, 1, 1, 0, 0, 0, -1, -1, -1)))
RTC_VALID: bool = False

def isoformat(time_struct = None, doy = False) -> str:
    if time_struct is None: # if no input, use current time
        time_struct = now()
    if isinstance(time_struct, (int, float)):
        time_struct = time.localtime(time_struct)
    if doy:
        _date = f"{time_struct.tm_year:04d}-{time_struct.tm_yday:03d}"
    else:
        _date = f"{time_struct.tm_year:04d}-{time_struct.tm_mon:02d}-{time_struct.tm_mday:02d}"
    _time = f"{time_struct.tm_hour:02d}:{time_struct.tm_min:02d}:{time_struct.tm_sec:02d}"
    return f"{_date}T{_time}"

def ntp_sync():
    pool = socketpool.SocketPool(wifi.radio)
    ntp = adafruit_ntp.NTP(pool, tz_offset=0)
    RTC = rtc.RTC()
    RTC.datetime = ntp.datetime
    global RTC_VALID
    RTC_VALID = True

def now():
    global RTC_VALID
    if not RTC_VALID:
        print("Warning: time has not been synchronized!")
    return time.localtime()
