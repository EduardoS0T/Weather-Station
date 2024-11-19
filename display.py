import RPi.GPIO as GPIO
import time

# Configuración de pines
LCD_RS = 25
LCD_E  = 24
LCD_D4 = 23
LCD_D5 = 4
LCD_D6 = 5
LCD_D7 = 6

# Constantes LCD
LCD_WIDTH = 16
LCD_CHR = True
LCD_CMD = False
LCD_LINE_1 = 0x80
LCD_LINE_2 = 0xC0

def setup():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LCD_E, GPIO.OUT)
    GPIO.setup(LCD_RS, GPIO.OUT)
    GPIO.setup(LCD_D4, GPIO.OUT)
    GPIO.setup(LCD_D5, GPIO.OUT)
    GPIO.setup(LCD_D6, GPIO.OUT)
    GPIO.setup(LCD_D7, GPIO.OUT)
    lcd_init()

def lcd_init():
    lcd_byte(0x33,LCD_CMD)
    lcd_byte(0x32,LCD_CMD)
    lcd_byte(0x28,LCD_CMD)
    lcd_byte(0x0C,LCD_CMD)
    lcd_byte(0x06,LCD_CMD)
    lcd_byte(0x01,LCD_CMD)
    time.sleep(0.0005)

def lcd_string(message,line):
    message = message.ljust(LCD_WIDTH," ")
    lcd_byte(line, LCD_CMD)
    for i in range(LCD_WIDTH):
        lcd_byte(ord(message[i]),LCD_CHR)

def lcd_byte(bits, mode):
    GPIO.output(LCD_RS, mode)
    GPIO.output(LCD_D4, False)
    GPIO.output(LCD_D5, False)
    GPIO.output(LCD_D6, False)
    GPIO.output(LCD_D7, False)
    if bits&0x10==0x10: GPIO.output(LCD_D4, True)
    if bits&0x20==0x20: GPIO.output(LCD_D5, True)
    if bits&0x40==0x40: GPIO.output(LCD_D6, True)
    if bits&0x80==0x80: GPIO.output(LCD_D7, True)
    time.sleep(0.0005)
    GPIO.output(LCD_E, True)
    time.sleep(0.0005)
    GPIO.output(LCD_E, False)
    time.sleep(0.0005)
    GPIO.output(LCD_D4, False)
    GPIO.output(LCD_D5, False)
    GPIO.output(LCD_D6, False)
    GPIO.output(LCD_D7, False)
    if bits&0x01==0x01: GPIO.output(LCD_D4, True)
    if bits&0x02==0x02: GPIO.output(LCD_D5, True)
    if bits&0x04==0x04: GPIO.output(LCD_D6, True)
    if bits&0x08==0x08: GPIO.output(LCD_D7, True)
    time.sleep(0.0005)
    GPIO.output(LCD_E, True)
    time.sleep(0.0005)
    GPIO.output(LCD_E, False)
    time.sleep(0.0005)

if __name__ == '__main__':
    setup()
    try:
        while True:
            lcd_string("Prueba LCD 16x2",LCD_LINE_1)
            lcd_string("Raspberry Pi 3",LCD_LINE_2)
            time.sleep(3)
            lcd_string("Linea 1",LCD_LINE_1)
            lcd_string("Linea 2",LCD_LINE_2)
            time.sleep(3)
    except KeyboardInterrupt:
        GPIO.cleanup()




