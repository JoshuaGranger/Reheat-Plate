from ili9341 import color565
from xpt2046 import Touch
from machine import Pin

class LCD(object):
    # Colors
    BLACK = color565(0,0,0)
    WHITE = color565(255,255,255)
    RED = color565(255,0,0)
    LIME = color565(0,255,0)
    BLUE = color565(0,0,255)
    YELLOW = color565(255,255,0)
    CYAN = color565(0,255,255)
    MAGENTA = color565(255,0,255)
    SILVER = color565(192,192,192)
    GRAY = color565(128,128,128)
    MAROON = color565(128,0,0)
    OLIVE = color565(128,128,0)
    GREEN = color565(0,128,0)
    PURPLE = color565(128,0,128)
    TEAL = color565(0,128,128)
    NAVY = color565(0,0,128)

    def __init__(self, display, spi_touch, heaterL, heaterR):
        self.display = display
        self.touch = Touch(spi_touch, cs=Pin(13), int_pin=Pin(7),
                           int_handler=self.touchscreen_press)
        self.heaterL = heaterL
        self.heaterR = heaterR

        # Interrupts on core 1 for the touchscreen is apparently challenging or
        # impossible. As a result, the interrupt needs to remain on Core 0. This
        # interrupt has the potential to interrupt with the lock.acquire/release which
        # causes the program to lock up. To avoid/fix this problem, these "active 
        # toggle pending" bits are used to handle touchscreen toggles in the regular Core 1
        # functionality loop.
        self.heaterL_atp = False
        self.heaterR_atp = False


    def touchscreen_press(self, y, x):
        # Calibration
        x = x - 18

        # Touchscreen handling for Heater.active
        active_pressed_y = 37 < y < 70
        active_pressed_hL = active_pressed_y and (195 < x < 255)
        active_pressed_hR = active_pressed_y and (255 < x < 315)

        if active_pressed_hL:
            self.heaterL_atp = True
        
        if active_pressed_hR:
            self.heaterR_atp = True


    def heater_toggle(self):
        if self.heaterL_atp:
            new_val = not self.heaterL.active
            self.heaterL.active = new_val
            self.heaterL_atp = False

        if self.heaterR_atp:
            new_val = not self.heaterR.active
            self.heaterR.active = new_val
            self.heaterR_atp = False


    def draw_table(self, btnL, btnR, heaterL, heaterR):
        # Draw table grid
        x0y0_offset = 5
        table_col = 3
        table_row = 7
        table_col_width = [190, 60, 60]
        table_row_height = int((240 - 2 * x0y0_offset)/table_row)
        for row in range(table_row):
            for col in range(table_col):
                x = x0y0_offset + sum(table_col_width[0:col])
                y = x0y0_offset + row * table_row_height
                self.display.draw_rectangle(x, y, table_col_width[col], table_row_height, self.BLUE)


        # Draw headings (Col 0)
        table_headings = ["Button Top/Bot Pressed ",
                          "Heater Active          ",
                          "Raw Temp Setpoint      ",
                          "Raw Temp Actual        ",
                          "Heater Heating         ",
                          "At Temp or Inactive    ",
                          "Holding Time Remaining "]
        text_x_offset = 5
        text_y_offset = int((table_row_height - 8)/2)
        for row in range(table_row):
            x = x0y0_offset + text_x_offset
            y = x0y0_offset + text_y_offset + row * table_row_height
            value = table_headings[row]
            self.display.draw_text8x8(x, y, str(value), self.LIME)

        # Draw data (Col 1, 2)
        table_data = [[not bool(btnL.value()),              not bool(btnR.value())],
                     [heaterL.active,                       heaterR.active],
                     ["{:>5.0f}".format(heaterL.temp_sp),   "{:>5.0f}".format(heaterR.temp_sp)],
                     ["{:>5.0f}".format(heaterL.temp_raw),  "{:>5.0f}".format(heaterR.temp_raw)],
                     [heaterL.heating,                      heaterR.heating],
                     [heaterL.at_temp_or_inactive,          heaterR.at_temp_or_inactive],
                     [heaterL.holding_time,                 heaterR.holding_time]]
        for row in range(7):
            for col in range(1, 3):
                x = x0y0_offset + text_x_offset + sum(table_col_width[0:col])
                y = x0y0_offset + text_y_offset + row * table_row_height
                value = table_data[row][col - 1]
                self.display.draw_text8x8(x, y, "{: <6}".format(str(value)), self.YELLOW)