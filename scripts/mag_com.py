import serial
import time
import datetime
import RPi.GPIO as GPIO


# (xxx ms) = execution time
def cur_date(m):
    """
    Current date (300 ms)
    """
    m.write(b'date\x00')
    m.read_until(b'\x00')
    flush_cash(m)


def set_date(m, date):
    """
    Set time and date (300 ms)
    """
    date = ('date ' + date + '\x00').encode('ascii')
    m.write(date)
    m.read_until(b'\x00')
    flush_cash(m)


def cur_time(m):
    """
    Time (300 ms)
    """
    m.write(b'time\x00')
    m.read_until(b'\x00')
    flush_cash(m)


def set_time(m, time):
    """
    Set time (300 ms)
    """
    time = ('time ' + time + '\x00').encode('ascii')
    m.write(time)
    m.read_until(b'\x00')
    flush_cash(m)


def set_mode(m, t):
    """
    Set magnetometer mode (300 ms)
    """
    m.write(('mode ' + t + '\x00').encode('ascii'))
    m.read_until(b'\x00')
    flush_cash(m)


def set_range(m, d):
    """
    Set range (300 ms)
    """
    m.write(('range ' + d + '\x00').encode('ascii'))
    m.read_until(b'\x00')
    flush_cash(m)


def run(m):
    """
    Make a single measurement (4000 ms)
    """
    m.write(b'run\x00')
    m.read_until(b'\x00')
    flush_cash(m)


def auto(m, filename, freq=-2):
    """
    Start automatic measurements (5000 ms)
    m - magnetometer object
    filename - file name
    freq - frequency (default, -2 (2 Hz))
    """
    m.write(b'auto ' + to_hexadecimal(freq, 32) + b'\x00')
    # m.write(b'auto 1\x00')
    time.sleep(4)
    flush_cash(m)
    with open('/home/pi/Documents/data/' + filename, 'wb') as f:

        GPIO.output(LED_yellow, GPIO.HIGH)

        while True:
            s = m.read_until(b'\x00')

            # Stop execution when the button is pressed or connection is lost
            if len(s) == 0 or GPIO.event_detected(button):
                stop(m)
                f.close()
                m.close()

                GPIO.output(LED_yellow, GPIO.LOW)
                GPIO.cleanup()
                break
            cur_time = str(datetime.datetime.now().timestamp()).split('.')
            f.write(s + to_hexadecimal(int(cur_time[0]), 64) + to_hexadecimal(int(cur_time[1]), 64) + b'\n')


def flush_cash(m):
    """
    Flush buffer (<1000 ms)
    """
    m.reset_input_buffer()
    m.reset_output_buffer()


def about(m):
    """
    Get info about the magnetometer (300 ms)
    """
    m.write(b'about\x00')
    m.read_until(b'\x00')
    flush_cash()


def stop(m):
    """
    Terminate measurements (1500 ms)
    """
    m.write(b'\x05\x00')
    m.read_until(b'\x00')
    flush_cash(m)


def to_hexadecimal(val, nbits):
    hex_str = hex((val + (1 << nbits)) % (1 << nbits)).replace('0x', '')
    if len(hex_str) % 2 != 0:
        hex_str = '0' + hex_str
    return bytes.fromhex(hex_str)


# pins to variables
LED_yellow = 31
button = 16

GPIO.setmode(GPIO.BOARD)  # set pin numbering from 1 to 40
GPIO.setwarnings(False)

GPIO.setup(LED_yellow, GPIO.OUT, initial=GPIO.LOW)  # green_led - output channel
GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # button - input channel

# when pressed, the current measurement cycle/the program is terminated
GPIO.add_event_detect(button, GPIO.FALLING)

# waiting for the mag
while True:
    try:
        m = serial.Serial('/dev/ttyUSB0', baudrate=9600, timeout=1)
        break
    except:
        pass
# init mag params
flush_cash(m)
set_mode(m, 'text')

set_date(m, datetime.datetime.now().strftime('%m-%d-%y'))
set_time(m, datetime.datetime.now().strftime('%H:%M:%S'))

# mag field value
set_range(m, '55000')

set_mode(m, 'binary')

# read parameters from the file param
with open('/home/pi/Documents/scripts/param', 'r') as prs:
    freq = int(prs.readline()) 
    decl = float(prs.readline())
    prs.close()

while True:
    time.sleep(0.5)
    GPIO.output(LED_yellow, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(LED_yellow, GPIO.LOW)
    if GPIO.event_detected(button):
        break

time.sleep(1.5)
filename = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_MG.txt')
auto(m, filename, freq)
