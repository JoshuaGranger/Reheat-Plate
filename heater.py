from machine import Pin, ADC
from math import log

class Heater(object):
    def __init__(self, heat_pin, temp_pin):
        _values_to_avg = 5
        self._active = False
        self._heat_pin = Pin(heat_pin, Pin.OUT)
        self._adc = ADC(temp_pin)
        self._temp_array = [65530] * _values_to_avg
        self._temp_raw = 65535
        self._temp_sp = 70000
        self._holding_time = 0


    # Class functions
    def read_temp(self):
        self._temp_array = self._temp_array[1:]
        self._temp_array.append(self._adc.read_u16())


    # Class Properties
    ## r/w active
    @property
    def active(self):
        return self._active
    

    @active.setter
    def active(self, value):
        self._active = bool(value)


    ## r at_temp_or_inactive
    @property
    def at_temp_or_inactive(self):
        return (not self.active or (self.active and self.temp_raw < self.temp_sp))


    ## r/w heating
    @property
    def heating(self):
        return not(bool(self._heat_pin.value()))


    @heating.setter
    def heating(self, value):
        val = not(bool(value))
        self._heat_pin.value(val)

    
    ## r/w holding_time
    @property
    def holding_time(self):
        return self._holding_time
    

    @holding_time.setter
    def holding_time(self, value):
        self._holding_time = value


    ## r temp_raw
    @property
    def temp_raw(self):
        self._temp_raw = sum(self._temp_array) / len(self._temp_array)
        return self._temp_raw
    

    ## r/w temp_sp
    @property
    def temp_sp(self):
        return self._temp_sp
    

    @temp_sp.setter
    def temp_sp(self, value):
        self._temp_sp = value