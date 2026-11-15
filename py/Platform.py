# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import platform
import re

# Platform identification constants.
UNKNOWN = 0
RASPBERRY_PI = 1
BEAGLEBONE_BLACK = 2
MINNOWBOARD = 3


def _read_device_tree_model():
    """Attempt to read the device tree model string (reliable across modern 32-bit and 64-bit kernels)."""
    for path in ['/proc/device-tree/model', '/sys/firmware/devicetree/base/model']:
        try:
            with open(path, 'r') as infile:
                return infile.read().strip().replace('\x00', '')
        except (IOError, OSError):
            continue
    return None


def platform_detect():
    """Detect if running on the Raspberry Pi or Beaglebone Black and return the
    platform type.  Will return RASPBERRY_PI, BEAGLEBONE_BLACK, or UNKNOWN."""
    # Handle Raspberry Pi
    pi = pi_version()
    if pi is not None:
        return RASPBERRY_PI

    # Handle Beaglebone Black
    plat = platform.platform()
    if plat.lower().find('armv7l-with-debian') > -1:
        return BEAGLEBONE_BLACK
    elif plat.lower().find('armv7l-with-ubuntu') > -1:
        return BEAGLEBONE_BLACK
    elif plat.lower().find('armv7l-with-glibc2.4') > -1:
        return BEAGLEBONE_BLACK

    # Handle Minnowboard
    try:
        import mraa

        if mraa.getPlatformName() == 'MinnowBoard MAX':
            return MINNOWBOARD
    except ImportError:
        pass

    # Couldn't figure out the platform, just return unknown.
    return UNKNOWN


def pi_revision():
    """Detect the revision number of a Raspberry Pi, useful for changing
    functionality like default I2C bus based on revision."""
    with open('/proc/cpuinfo', 'r') as infile:
        for line in infile:
            match = re.match(r'Revision\s+:\s+.*(\w{4})$', line, flags=re.IGNORECASE)
            if match and match.group(1) in ['0000', '0002', '0003']:
                return 1
            elif match:
                return 2
        raise RuntimeError('Could not determine Raspberry Pi revision.')


def pi_version():
    """Detect the version of the Raspberry Pi.  Returns either 1, 2, 3, 4, 5 or
    None depending on the Raspberry Pi model, or None if not a Raspberry Pi.
    """
    # First check Linux device tree (works on 32-bit and 64-bit ARM kernels)
    dt_model = _read_device_tree_model()
    if dt_model and 'Raspberry Pi' in dt_model:
        if 'Raspberry Pi 5' in dt_model:
            return 5
        elif 'Raspberry Pi 4' in dt_model or 'Raspberry Pi 400' in dt_model or 'Compute Module 4' in dt_model:
            return 4
        elif 'Raspberry Pi 3' in dt_model or 'Raspberry Pi Zero 2' in dt_model:
            return 3
        elif 'Raspberry Pi 2' in dt_model:
            return 2
        else:
            return 1

    # Check /proc/cpuinfo
    try:
        with open('/proc/cpuinfo', 'r') as infile:
            cpuinfo = infile.read()
    except (IOError, OSError):
        return None

    # Check for 'Model : Raspberry Pi ...' in cpuinfo
    model_match = re.search(r'^Model\s*:\s*(.*)$', cpuinfo, flags=re.MULTILINE | re.IGNORECASE)
    if model_match and 'Raspberry Pi' in model_match.group(1):
        m = model_match.group(1)
        if 'Raspberry Pi 5' in m:
            return 5
        elif 'Raspberry Pi 4' in m or 'Raspberry Pi 400' in m or 'Compute Module 4' in m:
            return 4
        elif 'Raspberry Pi 3' in m or 'Raspberry Pi Zero 2' in m:
            return 3
        elif 'Raspberry Pi 2' in m:
            return 2
        else:
            return 1

    # Match Hardware line (legacy 32-bit ARM kernel)
    match = re.search(r'^Hardware\s+:\s+(\w+)$', cpuinfo, flags=re.MULTILINE | re.IGNORECASE)
    if match:
        hw = match.group(1).upper()
        if hw in ('BCM2708', 'BCM2835'):
            try:
                (type, header) = get_model()
                if 'Pi 2' in type:
                    return 2
                elif 'Pi 3' in type:
                    return 3
                elif 'Pi 4' in type:
                    return 4
                else:
                    return 1
            except Exception:
                return 1
        elif hw in ('BCM2709', 'BCM2836'):
            return 2
        elif hw in ('BCM2710', 'BCM2837'):
            return 3
        elif hw in ('BCM2711',):
            return 4
        elif hw in ('BCM2712',):
            return 5

    # Check Revision field as fallback
    rev_match = re.search(r'^Revision\s*:\s*([0-9a-fA-F]+)$', cpuinfo, flags=re.MULTILINE | re.IGNORECASE)
    if rev_match:
        try:
            (type, _) = get_model()
            if 'Pi 5' in type:
                return 5
            elif 'Pi 4' in type:
                return 4
            elif 'Pi 3' in type:
                return 3
            elif 'Pi 2' in type:
                return 2
            elif 'Pi' in type or 'Model' in type:
                return 1
        except Exception:
            return 1

    return None


header40 = """A+, B+ and Pi2 B, and Zero models
                         +=========+
         POWER  3.3VDC   | 1 . . 2 |  5.0VDC   POWER
      I2C SDA1  GPIO  8  | 3 . . 4 |  5.0VDC   POWER
      I2C SCL1  GPIO  9  | 5 . . 6 |  GROUND
      CPCLK0    GPIO  7  | 7 . . 8 |  GPIO 15  TxD UART
                GROUND   | 9 . . 10|  GPIO 16  RxD UART
                GPIO  0  |11 . . 12|  GPIO  1  PCM_CLK/PWM0
                GPIO  2  |13 . . 14|  GROUND
                GPIO  3  |15 . . 16|  GPIO  4
         POWER  3.3VDC   |17 . . 18|  GPIO  5
      SPI MOSI  GPIO 12  |19 .   20|  GROUND
      SPI MISO  GPIO 13  |21 . . 22|  GPIO  6
      SPI SCLK  GPIO 14  |23 . . 24|  GPIO 10  CE0 SPI
                GROUND   |25 . . 26|  GPIO 11  CE1 SPI
 I2C ID EEPROM  SDA0     |27 . . 28|  SCL0     I2C ID EEPROM
        GPCLK1  GPIO 21  |29 . . 30|  GROUND
        CPCLK2  GPIO 22  |31 . . 32|  GPIO 26  PWM0
          PWM1  GPIO 23  |33 . . 34|  GROUND
   PCM_FS/PWM1  GPIO 24  |35 . . 36|  GPIO 27
                GPIO 25  |37 . . 38|  GPIO 28  PCM_DIN
                GROUND   |39 . . 40|  GPIO 29  PCM_DOUT
                         +=========+"""

header26 = """A and B models
                         +=========+
         POWER  3.3VDC   | 1 . . 2 |  5.0VDC   POWER
      I2C SDA0  GPIO  8  | 3 . . 4 |  DNC  
      I2C SCL0  GPIO  9  | 5 . . 6 |  GROUND
                GPIO  7  | 7 . . 8 |  GPIO 15  TxD UART
                DNC      | 9 . . 10|  GPIO 16  RxD UART
                GPIO  0  |11 . . 12|  GPIO  1  PCM_CLK/PWM0
                GPIO  2  |13 . . 14|  DNC
                GPIO  3  |15 . . 16|  GPIO  4
                DNC      |17 . . 18|  GPIO  5
      SPI MOSI  GPIO 12  |19 .   20|  DNC
      SPI MISO  GPIO 13  |21 . . 22|  GPIO  6
      SPI SCLK  GPIO 14  |23 . . 24|  GPIO 10  CE0 SPI
                DNC      |25 . . 26|  GPIO 11  CE1 SPI
                         +=========+"""


def get_model():
    dt_model = _read_device_tree_model()
    if dt_model and 'Raspberry Pi' in dt_model:
        if 'Model A' in dt_model and 'Plus' not in dt_model and '+' not in dt_model:
            return dt_model, header26
        if 'Model B' in dt_model and 'Plus' not in dt_model and '+' not in dt_model and not any(x in dt_model for x in ['Pi 2', 'Pi 3', 'Pi 4', 'Pi 5']):
            return dt_model, header26
        return dt_model, header40

    try:
        with open('/proc/cpuinfo', 'r') as infile:
            cpuinfo = infile.read()
    except (IOError, OSError):
        return "Raspberry Pi (Generic)", header40

    model_match = re.search(r'^Model\s*:\s*(.*)$', cpuinfo, flags=re.MULTILINE | re.IGNORECASE)
    if model_match and 'Raspberry Pi' in model_match.group(1):
        m = model_match.group(1).strip()
        if 'Model A' in m and 'Plus' not in m and '+' not in m:
            return m, header26
        if 'Model B' in m and 'Plus' not in m and '+' not in m and not any(x in m for x in ['Pi 2', 'Pi 3', 'Pi 4', 'Pi 5']):
            return m, header26
        return m, header40

    match = re.search(r'^Revision\s+:\s+\w*(\w{2})$', cpuinfo,
                      flags=re.MULTILINE | re.IGNORECASE)
    if not match:
        return "Raspberry Pi (Generic)", header40

    model = match.group(1).lower()

    if model in ["07", "08", "09"]:
        return "Model A", header26
    elif model in ["02", "03", "04", "05", "06", "0d", "0e", "0f"]:
        return "Model B", header26
    elif model in ["12", "15"]:
        return "Model A+", header40
    elif model in ["10", "13"]:
        return "Model B+", header40
    elif model in ["40", "41", "42"]:
        return "Pi 2 Model B", header40
    elif model in ["82", "83"]:
        return "Pi 3 Model B", header40
    elif model in ["d3"]:
        return "Pi 3 Model B+", header40
    elif model in ["e0"]:
        return "Pi 3 Model A+", header40
    elif model in ["11", "14"]:
        return "Pi 4 Model B", header40
    elif model in ["92", "93", "c1", "20"]:
        return "Pi Zero", header40

    return "Raspberry Pi (Generic)", header40

