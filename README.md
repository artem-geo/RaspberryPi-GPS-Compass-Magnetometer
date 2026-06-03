# Raspberry Pi GPS Compass Magnetometer

This project is an early prototype for turning an Overhauser magnetometer into an automatic, drone-ready data logger using a Raspberry Pi. The system records magnetic field measurements from the magnetometer together with GPS position and compass azimuth, so the data can be used later for geophysical survey processing or platform heading correction.

The repository contains the original Raspberry Pi acquisition scripts, example output data, Wi-Fi/SSH boot helper files, and a wiring/layout scheme.

## System Layout

![Raspberry Pi, GPS, compass, RS232-USB, buttons, LEDs, and magnetometer wiring scheme](files/scheme.jpg)

The scheme shows the main prototype wiring:

- Raspberry Pi as the onboard controller and data logger.
- u-blox GPS module connected over UART.
- HMC5883L or QMC5883L compass module connected over I2C.
- Overhauser magnetometer connected through an RS232-to-USB adapter.
- DC-DC converter for power conversion.
- LEDs and push buttons for field operation without a monitor or keyboard.

The numbered controls in the scheme correspond to:

1. Computer power/status indication.
2. GPS and compass readiness / coordinate and azimuth recording.
3. Magnetometer readiness / magnetic field recording.
4. GPS and compass start/stop, and Raspberry Pi shutdown.
5. Magnetometer start/stop.

## Hardware

The prototype was built around:

- Raspberry Pi with GPIO, UART, I2C, and USB.
- Overhauser magnetometer with RS232 output.
- RS232-to-USB adapter exposed on the Pi as `/dev/ttyUSB0`.
- u-blox GPS module exposed on the Pi as `/dev/ttyAMA0`.
- HMC5883L compass at I2C address `0x1e`, or QMC5883L compass at I2C address `0x0d`.
- Status LEDs and buttons connected to Raspberry Pi board pins.
- External power system with a 12 V to 5 V DC-DC converter.

## Raspberry Pi Pin Usage

The scripts use physical board pin numbering with `GPIO.setmode(GPIO.BOARD)`.

| Script | Pin | Purpose |
| --- | ---: | --- |
| `mag_com.py` | 31 | Magnetometer status LED |
| `mag_com.py` | 16 | Magnetometer start/stop button |
| `heading_hmc.py`, `heading_qmc.py` | 29 | Red status LED |
| `heading_hmc.py`, `heading_qmc.py` | 33 | GPS/compass status LED |
| `heading_hmc.py`, `heading_qmc.py` | 18 | GPS/compass start/stop/shutdown button |

## Software Requirements

The scripts were written for Python on Raspberry Pi OS and expect access to Raspberry Pi hardware interfaces.

Python modules used by the scripts:

- `pyserial`
- `RPi.GPIO`
- `numpy`
- `ublox`
- `hmc5883l` for the HMC5883L compass script
- `py_qmc5883l` for the QMC5883L compass script

System interfaces expected:

- UART enabled for GPS on `/dev/ttyAMA0`.
- I2C enabled for the compass.
- USB serial access for the magnetometer on `/dev/ttyUSB0`.
- Writeable data directory at `/home/pi/Documents/data/`.
- Scripts and `param` file located at `/home/pi/Documents/scripts/`.

## Parameters

The file `scripts/param` stores two acquisition settings:

```text
-1
11.83
```

The first line is the magnetometer acquisition frequency parameter passed to the Overhauser magnetometer `auto` command. The second line is the magnetic declination used by the compass scripts, in degrees.

## Acquisition Scripts

### Magnetometer Logger

`scripts/mag_com.py` connects to the Overhauser magnetometer over `/dev/ttyUSB0` at 9600 baud.

It performs the following sequence:

- Waits until the USB serial magnetometer connection is available.
- Flushes the serial buffers.
- Switches the magnetometer to text mode for setup.
- Sets magnetometer date and time from the Raspberry Pi clock.
- Sets magnetic field range to `55000`.
- Switches to binary mode.
- Reads the frequency parameter from `scripts/param`.
- Waits for the operator button.
- Starts automatic magnetic field measurements.
- Writes raw records to `/home/pi/Documents/data/YYYYMMDD_HHMMSS_MG.txt`.
- Stops when the button is pressed or the serial connection is lost.

Each raw magnetometer record is followed by Raspberry Pi timestamp bytes so the data can be converted later.

### GPS + Compass Logger

Use one of these scripts depending on the compass module:

- `scripts/heading_hmc.py` for HMC5883L.
- `scripts/heading_qmc.py` for QMC5883L.

Both scripts:

- Open the u-blox GPS on `/dev/ttyAMA0` at 9600 baud.
- Configure the GPS update rate.
- Wait for a valid `$GPRMC` message.
- Set the Raspberry Pi clock from GPS UTC time.
- Wait for the operator button.
- Record GPS time, azimuth, latitude, longitude, and height from `$GPGGA` messages.
- Write output to `/home/pi/Documents/data/YYYYMMDD_HHMMSS_AZ.txt`.
- Shut down the Raspberry Pi after logging is stopped.

Example output:

```text
GPST AZ LAT LON
1298964458.637607 251.94220415161467 5959.78019 03017.47208
```

The current scripts are written to include `HGT(MSL)` as an additional column. Some older example data in this repository contains only latitude and longitude columns.

## Converting Magnetometer Data

`scripts/MG_byte_to_str.py` converts raw binary magnetometer output into a text file with GPS time, UTC date/time, and magnetic field value.

Example converted output:

```text
GPST DATE(UTC) TIME(UTC) FIELD
1298964467.125 2021-03-05 07:27:29.125 51197.618
```

Before running the converter, update the hard-coded `filename` variable inside `MG_byte_to_str.py` so it points to the raw `*_MG.txt` file you want to convert. The converter writes a sibling file ending in `_c.txt`.

## Boot Helper Files

`files/files_exam/` contains example files for headless Raspberry Pi setup:

- `ssh` enables SSH when placed on the boot partition.
- `wpa_supplicant.conf` and `wpa_supplicant2.conf` are examples for Wi-Fi setup.

These files are examples only. Replace the SSIDs, passwords, country code, and network settings before using them on a real device.

## Notes and Limitations

- The scripts contain hard-coded Raspberry Pi paths under `/home/pi/Documents/`.
- The converter contains an old hard-coded local path and should be edited before use.
- The GPS leap second offset is hard-coded as `18`.
- The converter applies a `-10800` second local-time correction from the original test environment.
- Broad `try/except` blocks were useful for a field prototype, but they can hide hardware or parsing errors during debugging.
- This repository preserves the prototype state rather than a packaged application.

## Example Data

The `data/` folder contains a short example survey recording from 2021:

- `20210305_072720_AZ.txt`: GPS time, azimuth, and position.
- `20210305_072724_MG.txt`: raw binary magnetometer stream.
- `20210305_072724_MG_c.txt`: converted magnetic field values.

The intended post-processing key is `GPST`, which allows magnetic field samples to be aligned with position and heading samples.
