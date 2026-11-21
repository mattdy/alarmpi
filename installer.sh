#!/bin/bash

# AlarmPi installation script
# Download all the necessary libraries to run AlarmPi

# AlarmPi needs access to device-level stuff which requires root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

git clone https://github.com/adafruit/Adafruit-Raspberry-Pi-Python-Code.git
git clone https://github.com/guyc/py-gaugette.git
git clone https://github.com/seanbechhofer/raspberrypi.git seanbechhofer
git clone https://github.com/baudm/mplayer.py.git
git clone https://github.com/PDKK/RpiLcdBackpack.git

git clone https://github.com/mattdy/alarmpi.git

# LCDControl used to be fetched from projects.mattdyson.org, which no longer exists, and it
# has not been published anywhere else. A copy needs to be placed alongside this script
if [ ! -d LCDControl ]; then
   echo "WARNING: LCDControl was not found in $(pwd), the LCD will not work without it" 1>&2
fi

touch "RpiLcdBackpack/__init__.py"

cd alarmpi

python3 -m venv --system-site-packages venv
venv/bin/pip install -r requirements.txt

ln -s ../Adafruit-Raspberry-Pi-Python-Code/Adafruit_LEDBackpack/Adafruit_7Segment.py
ln -s ../Adafruit-Raspberry-Pi-Python-Code/Adafruit_I2C/Adafruit_I2C.py
ln -s ../Adafruit-Raspberry-Pi-Python-Code/Adafruit_LEDBackpack/Adafruit_LEDBackpack.py
ln -s ../py-gaugette/gaugette/
ln -s ../LCDControl/LCDControl/
ln -s ../mplayer.py/mplayer/
ln -s ../RpiLcdBackpack/
ln -s ../seanbechhofer/python/TSL2561.py

CREDFILE="CalendarCredentials.py"
touch $CREDFILE
echo -n "Enter Google Developer Client ID: "
read clientid
echo
echo -n "Enter Google Developer Client secret: "
read clientsecret
echo
echo -n "Enter Google Developer key: "
read developerkey
echo
echo -n "Enter Google Calendar address: "
read calendar
echo
echo -n "Enter OpenWeatherMap API key: "
read owmappid

echo "CLIENT_ID='$clientid'" >> $CREDFILE
echo "CLIENT_SECRET='$clientsecret'" >> $CREDFILE
echo "DEVELOPER_KEY='$developerkey'" >> $CREDFILE
echo "CALENDAR='$calendar'" >> $CREDFILE
echo "OWM_APPID='$owmappid'" >> $CREDFILE

echo
echo "Now authorise access to the calendar, either by copying a service account key to"
echo "service_account.json, or by running: venv/bin/python AlarmGatherer.py"
echo "Then start AlarmPi with: venv/bin/python alarmpi.py"
