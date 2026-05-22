import datetime
import os
import py_qmc5883l
from math import fabs
import RPi.GPIO as GPIO
import time
from serial import Serial
from ublox import ubx


def parse_GPS_message(data):
    """
    Reads NMEA message
    Returns a list of tokens
    """
    return data[data.find(b'$'):].decode('utf-8').split(',')


def get_data_from_NMEA(s, num):
    """
    Gets data from the NMEA message
    s - message
    num = 0 -flag to return datetime from GPGRMC
    num = 1 - flag to return list of lat lon and MSL from GPGGA
    """
    s = str(s, encoding='utf-8').split(',')
    if num == 0:
        return datetime.datetime.strptime(f'{s[1]} {s[9]}', '%H%M%S.%f %d%m%y')
    elif num == 1:
        return [s[2], s[4], s[9]]


def LED_blinking(led, button):
    while True:
        time.sleep(0.5)
        GPIO.output(led, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(led, GPIO.LOW)
        if GPIO.event_detected(button):
            time.sleep(1)
            break
    time.sleep(1)


# set pins to vars
LED_red = 29
LED_green = 33
button = 18

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

GPIO.setup(LED_red, GPIO.OUT, initial=GPIO.HIGH)  # red_led - ouput channel
GPIO.setup(LED_green, GPIO.OUT, initial=GPIO.LOW)  # green_led - output channel
GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # button - input channel

GPIO.add_event_detect(button, GPIO.FALLING)

# GPS
# init GPS
ser = Serial('/dev/ttyAMA0', baudrate=9600)
gps = ubx.UbxStream(ser)
gps.cfg_rate(200)  # set sampling freq

ser.flush()

# GPST (Jan 6 1980 00:00:00.00)
gps_epoch = datetime.datetime(1980, 1, 6).timestamp()

with open('/home/pi/Documents/scripts/param', 'r') as prs:
    freq = int(prs.readline())   # magnetometer freq
    decl = float(prs.readline())  # declination (dd.mm)
    prs.close()

# COMPASS
# init magnetometer
mag = py_qmc5883l.QMC5883L(i2c_bus=1, address=0x0d)
mag.set_declination(decl)

# while writing mag readings time is taken from RP
# script will keep running when a sufficient number of satellites are seen
# if the button is pressed before sats are found, the script terminates and the RP shuts down
while True:
    if GPIO.event_detected(button):
        time.sleep(1)
        os.system('sudo shutdown now')
    try:
        s = ser.readline()
        if b'$GPRMC' in s:
            data = parse_GPS_message(s)
            if (len(data[1]) > 6) and (len(data[9]) > 5) and \
               (len(data[3]) > 3) and (len(data[5]) > 3):
                ostime = get_data_from_NMEA(s, 0).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                os.system(f'sudo date --set="{ostime}"')
                break
    except:
        pass


LED_blinking(LED_green, button)

# непрерывно горящий светодиод сигнализирует о начале записи координат и азимута
GPIO.output(LED_green, GPIO.HIGH)


# file name -  yyyymmdd_HHMMSS_AZ.txt
# y - year, m - month, d - day, H - hour, M - minute, S - second
filename = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_AZ.txt')

with open(f'/home/pi/Documents/data/{filename}', 'w') as f:

    f.write('GPST AZ LAT LON HGT(MSL)\n')

    while True:
        try:
            s = ser.readline()
            m = fabs(mag.get_bearing() - 360) 

            if b'$GPGGA' in s:

                # GPST = Epoch time - Epoch time of GPST + leap seconds
                cur_time = datetime.datetime.now().timestamp() - gps_epoch + 18
                coord = get_data_from_NMEA(s, 1)
                f.write(f'{cur_time} {m} {coord[0]} {coord[1]} {coord[2]}\n')
            else:
                continue
            if GPIO.event_detected(button):

                f.close()
                GPIO.output(LED_green, GPIO.LOW)
                break
        except:
            pass

LED_blinking(LED_green, button)

GPIO.cleanup()

os.system('sudo shutdown now')
