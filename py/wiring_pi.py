#!/usr/bin/env python
#
# Licensed under the BSD license.  See full license in LICENSE file.
# http://www.lightshowpi.org/
#
# Author: Micah Wedemeyer
# Author: Tom Enos (tomslick.ca@gmail.com)


"""Empty wrapper module for wiringpi

This module is a placeholder for virtual hardware to run a simulated lightshow
on a PC or when running without direct hardware access.
"""

# Setup
def wiringPiSetup(*args):
    pass

wiringPiSetupPY = wiringPiSetup

def wiringPiSetupSys(*args):
    pass

wiringPiSetupSysPY = wiringPiSetupSys

def pinMode(*args):
    pass

pinModePY = pinMode

# Pin Writes
def softPwmCreate(*args):
    pass

softPwmCreatePY = softPwmCreate

def softPwmWrite(*args):
    pass

softPwmWritePY = softPwmWrite

def digitalWrite(*args):
    pass

digitalWritePY = digitalWrite

def analogWrite(*args):
    pass

analogWritePY = analogWrite

# Devices
def mcp23017Setup(*args):
    pass

mcp23017SetupPY = mcp23017Setup

def mcp23s17Setup(*args):
    pass

mcp23s17SetupPY = mcp23s17Setup

def mcp23016Setup(*args):
    pass

mcp23016SetupPY = mcp23016Setup

def mcp23008Setup(*args):
    pass

mcp23008SetupPY = mcp23008Setup

def mcp23s08Setup(*args):
    pass

mcp23s08SetupPY = mcp23s08Setup

def sr595Setup(*args):
    pass

sr595SetupPY = sr595Setup

def pcf8574Setup(*args):
    pass

pcf8574SetupPY = pcf8574Setup

