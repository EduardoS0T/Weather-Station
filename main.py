import time
import board
import busio
import lgpio
import adafruit_dht
import adafruit_tcs34725
from datetime import datetime
import signal
import sys
import math
import threading
from collections import deque

# Configuración LCD
LCD_RS = 25
LCD_E  = 24
LCD_D4 = 23
LCD_D5 = 4
LCD_D6 = 5
LCD_D7 = 6
LCD_WIDTH = 16
LCD_CHR = True
LCD_CMD = False
LCD_LINE_1 = 0x80
LCD_LINE_2 = 0xC0

def cleanup_gpio():
    """Limpia todos los recursos GPIO antes de iniciar"""
    try:
        # Intentar abrir y cerrar chip para limpiar
        h = lgpio.gpiochip_open(0)
        # Limpiar pines LCD
        for pin in [LCD_RS, LCD_E, LCD_D4, LCD_D5, LCD_D6, LCD_D7]:
            try:
                lgpio.gpio_free(h, pin)
            except:
                pass
        # Limpiar pines de sensores
        for pin in [17, 27, 22]:  # Pines del anemómetro, lluvia y DHT11
            try:
                lgpio.gpio_free(h, pin)
            except:
                pass
        lgpio.gpiochip_close(h)
    except:
        pass
    
    # Esperar un momento para asegurar que los recursos se liberen
    time.sleep(1)

class LCD:
    def __init__(self):
        try:
            self.h = lgpio.gpiochip_open(0)
            for pin in [LCD_RS, LCD_E, LCD_D4, LCD_D5, LCD_D6, LCD_D7]:
                lgpio.gpio_claim_output(self.h, pin)
            self.lcd_init()
        except Exception as e:
            print(f"Error LCD: {e}")
            raise

    def lcd_init(self):
        self.lcd_byte(0x33, LCD_CMD)
        self.lcd_byte(0x32, LCD_CMD)
        self.lcd_byte(0x28, LCD_CMD)
        self.lcd_byte(0x0C, LCD_CMD)
        self.lcd_byte(0x06, LCD_CMD)
        self.lcd_byte(0x01, LCD_CMD)
        time.sleep(0.0005)

    def lcd_string(self, message, line):
        message = message.ljust(LCD_WIDTH," ")
        self.lcd_byte(line, LCD_CMD)
        for i in range(LCD_WIDTH):
            self.lcd_byte(ord(message[i]), LCD_CHR)

    def lcd_byte(self, bits, mode):
        lgpio.gpio_write(self.h, LCD_RS, mode)
        for pin in [LCD_D4, LCD_D5, LCD_D6, LCD_D7]:
            lgpio.gpio_write(self.h, pin, False)
        if bits&0x10==0x10: lgpio.gpio_write(self.h, LCD_D4, True)
        if bits&0x20==0x20: lgpio.gpio_write(self.h, LCD_D5, True)
        if bits&0x40==0x40: lgpio.gpio_write(self.h, LCD_D6, True)
        if bits&0x80==0x80: lgpio.gpio_write(self.h, LCD_D7, True)

        time.sleep(0.0005)
        lgpio.gpio_write(self.h, LCD_E, True)
        time.sleep(0.0005)
        lgpio.gpio_write(self.h, LCD_E, False)
        time.sleep(0.0005)

        for pin in [LCD_D4, LCD_D5, LCD_D6, LCD_D7]:
            lgpio.gpio_write(self.h, pin, False)
        if bits&0x01==0x01: lgpio.gpio_write(self.h, LCD_D4, True)
        if bits&0x02==0x02: lgpio.gpio_write(self.h, LCD_D5, True)
        if bits&0x04==0x04: lgpio.gpio_write(self.h, LCD_D6, True)
        if bits&0x08==0x08: lgpio.gpio_write(self.h, LCD_D7, True)

        time.sleep(0.0005)
        lgpio.gpio_write(self.h, LCD_E, True)
        time.sleep(0.0005)
        lgpio.gpio_write(self.h, LCD_E, False)
        time.sleep(0.0005)

class Anemometer:
    def __init__(self, pin):
        self.RADIO_METROS = 0.09
        self.CAMBIOS_POR_VUELTA = 6
        self.pin = pin
        self.wind_count = 0
        self.last_time = time.time()
        self.last_state = None
        self.running = True
        self.current_speed = 0
        self.lock = threading.Lock()
        
        try:
            self.h = lgpio.gpiochip_open(0)
            lgpio.gpio_claim_input(self.h, self.pin, lgpio.SET_PULL_UP)
            self.last_state = lgpio.gpio_read(self.h, self.pin)
            
            # Iniciar hilo de monitoreo
            self.monitor_thread = threading.Thread(target=self._monitor_rotation)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            
        except Exception as e:
            print(f"Error Anemómetro: {e}")
            raise
    
    def _monitor_rotation(self):
        last_calculation = time.time()
        local_count = 0
        
        while self.running:
            current_state = lgpio.gpio_read(self.h, self.pin)
            if current_state != self.last_state:
                with self.lock:
                    local_count += 1
                    self.wind_count += 1
                self.last_state = current_state
            
            current_time = time.time()
            if current_time - last_calculation >= 1.0:
                with self.lock:
                    vueltas = local_count / self.CAMBIOS_POR_VUELTA
                    omega = (vueltas * 2 * math.pi) / (current_time - last_calculation)
                    velocidad_ms = omega * self.RADIO_METROS
                    velocidad_kmh = velocidad_ms * 3.6
                    
                    if velocidad_kmh < 1:
                        velocidad_kmh = 0
                    
                    self.current_speed = round(velocidad_kmh, 1)
                    local_count = 0
                last_calculation = current_time
            
            time.sleep(0.001)
    
    def get_reading(self):
        with self.lock:
            return {
                'timestamp': datetime.now().isoformat(),
                'wind_speed': self.current_speed,
                'wind_speed_ms': round(self.current_speed / 3.6, 2)
            }
    
    def cleanup(self):
        self.running = False
        time.sleep(0.1)
        if hasattr(self, 'h'):
            lgpio.gpio_free(self.h, self.pin)
            lgpio.gpiochip_close(self.h)

class RainSensor:
    def __init__(self, pin):
        self.pin = pin
        try:
            self.h = lgpio.gpiochip_open(0)
            lgpio.gpio_claim_input(self.h, self.pin, lgpio.SET_PULL_UP)
        except Exception as e:
            print(f"Error Sensor de lluvia: {e}")
            raise

    def get_reading(self):
        samples = []
        for _ in range(5):
            samples.append(lgpio.gpio_read(self.h, self.pin))
            time.sleep(0.1)
        return {'is_raining': sum(samples) < len(samples)/2}

    def cleanup(self):
        if hasattr(self, 'h'):
            lgpio.gpio_free(self.h, self.pin)
            lgpio.gpiochip_close(self.h)

class DHT11:
    def __init__(self, pin):
        try:
            self.device = adafruit_dht.DHT11(getattr(board, f'D{pin}'))
            time.sleep(1)
        except Exception as e:
            print(f"Error DHT11: {e}")
            raise

    def get_reading(self):
        try:
            return {
                'temperature': self.device.temperature,
                'humidity': self.device.humidity,
                'status': 'success'
            }
        except:
            return {
                'temperature': 0,
                'humidity': 0,
                'status': 'error'
            }

    def cleanup(self):
        try:
            self.device.exit()
        except:
            pass

class LightSensor:
    def __init__(self):
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            self.sensor = adafruit_tcs34725.TCS34725(i2c)
            
            # Configuración optimizada para mejor sensibilidad
            self.sensor.gain = 60       # Máxima ganancia para mejor sensibilidad
            self.sensor.integration_time = 100  # Tiempo de integración balanceado
            self.sensor.led = False     # LED apagado
            
            time.sleep(0.5)  # Tiempo de estabilización
            
        except Exception as e:
            print(f"Error Sensor de luz: {e}")
            raise

    def get_reading(self):
        try:
            # Obtener valores RGB y Clear raw
            r, g, b, c = self.sensor.color_raw
            
            # Calcular intensidad de luz en lux (aproximada)
            lux = min(100, (c / 65535) * 100)
            
            # Calcular porcentajes RGB relativos al total
            total = r + g + b
            if total > 0:
                r_percent = (r / total) * 100
                g_percent = (g / total) * 100
                b_percent = (b / total) * 100
            else:
                r_percent = g_percent = b_percent = 0
                
            # Crear mensaje descriptivo
            intensidad = "Baja" if lux < 33 else "Media" if lux < 66 else "Alta"
            
            return {
                'light_level': round(lux, 1),
                'momento': f"Luz: {intensidad}",
                'rgb_values': {
                    'red': round(r_percent, 1),
                    'green': round(g_percent, 1),
                    'blue': round(b_percent, 1),
                    'clear': c,
                    'raw_r': r,
                    'raw_g': g,
                    'raw_b': b
                }
            }
        except Exception as e:
            print(f"Error en lectura del sensor: {e}")
            return {
                'light_level': 0,
                'momento': "Error",
                'rgb_values': {
                    'red': 0,
                    'green': 0,
                    'blue': 0,
                    'clear': 0,
                    'raw_r': 0,
                    'raw_g': 0,
                    'raw_b': 0
                }
            }

    def print_debug(self):
        """
        Imprime información detallada para debug
        """
        reading = self.get_reading()
        rgb = reading['rgb_values']
        print(f"""
Lectura del sensor:
------------------
Intensidad de luz: {reading['light_level']}%
Estado: {reading['momento']}

Valores RGB (porcentaje del total):
  Rojo:  {rgb['red']}%
  Verde: {rgb['green']}%
  Azul:  {rgb['blue']}%

Valores raw:
  Rojo:  {rgb['raw_r']}
  Verde: {rgb['raw_g']}
  Azul:  {rgb['raw_b']}
  Clear: {rgb['clear']}
""")

class WeatherStation:
    def __init__(self):
        try:
            print("Iniciando sensores...")
            self.lcd = LCD()
            self.lcd.lcd_string("Iniciando", LCD_LINE_1)
            self.lcd.lcd_string("Sensores...", LCD_LINE_2)
            
            self.anemometer = Anemometer(pin=17)
            self.rain_sensor = RainSensor(pin=27)
            self.temp_sensor = DHT11(pin=22)
            self.light_sensor = LightSensor()
            
            # Buffer para datos históricos
            self.data_buffer = deque(maxlen=1000)
            
            self.lcd.lcd_string("Estacion Meteo", LCD_LINE_1)
            self.lcd.lcd_string("Iniciada!", LCD_LINE_2)
            time.sleep(2)
            
            # Iniciar hilo de actualización de LCD
            self.lcd_thread_running = True
            self.current_readings = None
            self.lcd_thread = threading.Thread(target=self._update_lcd)
            self.lcd_thread.daemon = True
            self.lcd_thread.start()
            
        except Exception as e:
            print(f"Error iniciando estación: {e}")
            raise

    def _update_lcd(self):
        display_index = 0
        while self.lcd_thread_running:
            if self.current_readings:
                try:
                    if display_index == 0:
                        # Temperatura y Humedad
                        self.lcd.lcd_string(f"Temp: {self.current_readings['temperature']}C", LCD_LINE_1)
                        self.lcd.lcd_string(f"Hum: {self.current_readings['humidity']}%", LCD_LINE_2)
                    elif display_index == 1:
                        # Viento y Lluvia
                        self.lcd.lcd_string(f"Viento: {self.current_readings['wind_speed']}km/h", LCD_LINE_1)
                        self.lcd.lcd_string("Lluvia: " + ("Si" if self.current_readings['is_raining'] else "No"), LCD_LINE_2)
                    else:
                        # Intensidad de luz y RGB
                        if 'rgb_values' in self.current_readings and self.current_readings['rgb_values']:
                            self.lcd.lcd_string(f"Luz: {self.current_readings['light_level']}%", LCD_LINE_1)
                            rgb = self.current_readings['rgb_values']
                            self.lcd.lcd_string(f"R:{rgb['red']}% G:{rgb['green']}%", LCD_LINE_2)
                    
                    display_index = (display_index + 1) % 3
                    time.sleep(3)
                except Exception as e:
                    print(f"Error en LCD: {e}")
                    time.sleep(1)
            else:
                time.sleep(0.1)

    def get_readings(self):
        """Obtiene lecturas de todos los sensores"""
        temp_data = self.temp_sensor.get_reading()
        wind_data = self.anemometer.get_reading()
        rain_data = self.rain_sensor.get_reading()
        light_data = self.light_sensor.get_reading()
        
        readings = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'temperature': temp_data['temperature'],
            'humidity': temp_data['humidity'],
            'wind_speed': wind_data['wind_speed'],
            'is_raining': rain_data['is_raining'],
            'light_level': light_data['light_level'],
            'momento': light_data['momento'],
            'rgb_values': light_data.get('rgb_values')
        }
        
        self.current_readings = readings
        self.data_buffer.append(readings)
        return readings

    def cleanup(self):
        try:
            self.lcd_thread_running = False
            time.sleep(0.2)
            
            self.lcd.lcd_string("Apagando...", LCD_LINE_1)
            self.lcd.lcd_string("", LCD_LINE_2)
            time.sleep(1)
            
            self.anemometer.cleanup()
            self.rain_sensor.cleanup()
            self.temp_sensor.cleanup()
            lgpio.gpiochip_close(self.lcd.h)
        except:
            pass

def main():
    try:
        # Limpiar GPIO antes de iniciar
        print("Limpiando GPIO...")
        cleanup_gpio()
        
        # Inicializar estación
        station = WeatherStation()
        print("Estación iniciada correctamente")
        
        # Bucle principal
        while True:
            readings = station.get_readings()
            # Debug de valores RGB
            if readings['rgb_values']:
                rgb = readings['rgb_values']
                print(f"\nLuz: {readings['light_level']}% | R:{rgb['red']}% G:{rgb['green']}% B:{rgb['blue']}%")
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nPrograma interrumpido por el usuario")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        if 'station' in locals():
            station.cleanup()
        cleanup_gpio()
        print("Programa finalizado")

if __name__ == "__main__":
    main()
