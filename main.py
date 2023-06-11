# Reheat Plate Raspberry Pi Pico W
# 2023 June 4
# Joshua Granger
# References: https://github.com/rdagger/micropython-ili9341

# Imports
from machine import idle, Pin, SPI  # type: ignore
from heater import Heater
from lcd import LCD
from ili9341 import Display
from utime import ticks_ms, ticks_diff, sleep_ms
import _thread

# Definitions
## Misc Pins
btn_top = Pin(18, Pin.IN, Pin.PULL_UP)
btn_btm = Pin(22, Pin.IN, Pin.PULL_UP)

# Semaphore (lock) handling
lock = _thread.allocate_lock()

## Heater
heaterL = Heater(20, 26)
heaterR = Heater(21, 27)

# SPI - Display
spi_display = SPI(0, baudrate=10000000, polarity=1, phase=1, bits=8,
                    firstbit=SPI.MSB, sck=Pin(2), mosi=Pin(3), miso=Pin(4))
display = Display(spi_display, dc=Pin(6), cs=Pin(5), rst=Pin(8), width=320, height=240, rotation=90)
display.clear()

# SPI - Touch
spi_touch = SPI(1, baudrate=1000000, sck=Pin(10), mosi=Pin(11), miso=Pin(12))

# Initialize LCD Object
lcd = LCD(display, spi_touch, heaterL, heaterR)

# Functions
## Disable heating
def disable_heaters():
    lock.acquire()
    heaterL.active = False
    heaterR.active = False
    heaterL.temp_sp = 70000
    heaterR.temp_sp = 70000
    lock.release()


## Set temperature and hold for time
def set_and_hold(temperature, time_ms):
    lock.acquire()
    # Display the holding time
    heaterL.holding_time = time_ms
    heaterR.holding_time = time_ms

    # Set temperature
    heaterL.temp_sp = temperature
    heaterR.temp_sp = temperature
    lock.release()

    # Wait until the target is reached
    while True:
        # Evaluate continuation
        lock.acquire()
        if (heaterL.at_temp_or_inactive and heaterR.at_temp_or_inactive):
            lock.release()
            break
        
        lock.release()

        # Check for bottom button. Return True (abort) if pressed.
        if btn_btm.value() == 0:
            disable_heaters()
            return True

    # Hold for a period of time
    timer_start = ticks_ms()
    time_left = time_ms - ticks_diff(ticks_ms(), timer_start)
    while (time_left > 0):
        # Update holding time
        time_left = time_ms - ticks_diff(ticks_ms(), timer_start)
        lock.acquire()
        heaterL.holding_time = time_left
        heaterR.holding_time = time_left
        lock.release()

        # Check for bottom button. Return True (abort) if pressed.
        if btn_btm.value() == 0:
            disable_heaters()
            return True
    
    # Set holding time to 0
    lock.acquire()
    heaterL.holding_time = 0
    heaterR.holding_time = 0
    lock.release()

    # Return False (do not abort)
    return False


## Heating Cycle
def heat_cycle():
    abort = False
    while True and not abort:
        # Verify at least one heater is active
        lock.acquire()
        heater_active = heaterL.active or heaterR.active
        lock.release()

        # Heating Steps
        if (heater_active):
            abort = set_and_hold(64500, 45000)
            if abort:
                break

            abort = set_and_hold(62500, 45000)
            if abort:
                break

            abort = set_and_hold(55000, 30000)
            if abort:
                break

            abort = set_and_hold(30000, 15000)
            if abort:
                break

            abort = set_and_hold(20000, 1000)
            if abort:
                break
        
        # At the end of the cycle, break out
        abort = True

    # Disable heaters and exit function
    disable_heaters()


## Core 1
def core1_main():
    while True:
        lock.acquire()

        # Read temperatures and update LCD display
        heaterL.read_temp()
        heaterR.read_temp()
        
        # Draw LCD Table
        lcd.draw_table(btn_top, btn_btm, heaterL, heaterR)

        # Evaluate heater L condition and heat if necessary
        if heaterL.active and (heaterL.temp_raw > heaterL.temp_sp):
            heaterL.heating = True
        
        else:
            heaterL.heating = False

        # Evaluate heater R condition and heat if necessary
        if heaterR.active and (heaterR.temp_raw > heaterR.temp_sp):
            heaterR.heating = True
        
        else:
            heaterR.heating = False

        lock.release()


# Execution
try:
    # Execute core1
    _thread.start_new_thread(core1_main, ())

    # Execute core0
    while True:
        # Update heater active status (check for heaterL/R_atp flag set)
        lock.acquire()
        lcd.heater_toggle()
        lock.release()

        # Top button pressed and heaters not already hot
        if (btn_top.value() == 0):
            lock.acquire()
            heaters_cool = heaterL.temp_raw > 60000 and heaterR.temp_raw > 60000
            lock.release()

            if heaters_cool:
                heat_cycle()
        
        # # Development Exception to allow breaking out of code
        # elif (btn_btm.value() == 0):
        #     raise KeyboardInterrupt

except KeyboardInterrupt:
    print("Interrupted")

finally:
    display.cleanup()