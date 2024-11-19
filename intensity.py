import time
import board
import busio
import adafruit_tcs34725
from datetime import datetime
import signal
import sys
from statistics import median

class LightSensor:
    def __init__(self):
        """
        Inicializa el sensor TCS34725 como sensor de luz ambiental
        """
        # Inicializar I2C
        i2c = busio.I2C(board.SCL, board.SDA)
        self.sensor = adafruit_tcs34725.TCS34725(i2c)
        
        # Configurar para lecturas estables
        self.sensor.gain = 1
        self.sensor.integration_time = 200
        
        # Buffer para promedio móvil
        self.readings_buffer = []
        self.buffer_size = 5
        
        print("Sensor de luz inicializado")
        print("Conexiones:")
        print("VIN   → 3.3V")
        print("GND   → GND")
        print("SCL   → SCL (GPIO3)")
        print("SDA   → SDA (GPIO2)")
        
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        self.calibrate()
    
    def calibrate(self):
        """
        Calibra el sensor para determinar niveles de luz
        """
        print("\nCalibrando sensor...")
        readings = []
        
        for _ in range(10):
            _, _, _, c = self.sensor.color_raw
            readings.append(c)
            time.sleep(0.1)
            
        self.light_reference = median(readings)
        print(f"Calibración completada. Valor de referencia: {self.light_reference}")
    
    def get_stable_reading(self):
        """
        Obtiene una lectura estable usando promedio móvil
        """
        _, _, _, clear = self.sensor.color_raw
        
        self.readings_buffer.append(clear)
        
        if len(self.readings_buffer) > self.buffer_size:
            self.readings_buffer.pop(0)
        
        return median(self.readings_buffer)
    
    def get_light_level(self):
        """
        Obtiene el nivel de luz actual
        """
        clear = self.get_stable_reading()
        return min(100, (clear / 1000) * 100)
    
    def get_time_of_day(self, light_level, hour=None):
        """
        Determina el momento del día basado en el nivel de luz y la hora
        """
        if hour is None:
            hour = datetime.now().hour
            
        # Primero verificar por hora del día
        if 0 <= hour < 6:
            base_time = "Noche"
        elif 6 <= hour < 12:
            base_time = "Mañana"
        elif 12 <= hour < 18:
            base_time = "Tarde"
        else:
            base_time = "Noche"
            
        # Luego ajustar según el nivel de luz
        if light_level < 10:
            if base_time == "Noche":
                return "Noche oscura"
            else:
                return f"{base_time} muy oscura"
        elif light_level < 30:
            if base_time in ["Mañana", "Tarde"]:
                return f"{base_time} nublada"
            return "Noche con luz"
        elif light_level < 50:
            return f"{base_time} normal"
        elif light_level < 70:
            return f"{base_time} clara"
        else:
            if base_time in ["Mañana", "Tarde"]:
                return f"{base_time} muy brillante"
            return "Noche iluminada"
    
    def get_reading(self):
        """
        Obtiene una lectura completa del sensor
        """
        try:
            light_level = self.get_light_level()
            hora_actual = datetime.now().hour
            momento_del_dia = self.get_time_of_day(light_level, hora_actual)
            
            # Obtener valores RGB
            r, g, b = self.sensor.color_rgb_bytes
            
            # Calcular temperatura de color aproximada
            if r > 0 and b > 0:
                temp_color = "cálida" if r > b else "fría"
            else:
                temp_color = "neutral"
            
            reading = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'hora': datetime.now().strftime('%H:%M'),
                'light_level': round(light_level, 1),
                'momento_del_dia': momento_del_dia,
                'temp_color': temp_color,
                'rgb': f"R:{r:>3} G:{g:>3} B:{b:>3}",
                'status': 'success'
            }
            
            return reading
            
        except Exception as e:
            return {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'error',
                'error_message': str(e)
            }
    
    def signal_handler(self, signum, frame):
        """
        Maneja las señales de terminación
        """
        print("\nSeñal recibida. Finalizando...")
        sys.exit(0)

def main():
    """
    Función principal para pruebas
    """
    try:
        sensor = LightSensor()
        
        print("\nMonitoreando luz ambiental. Presiona Ctrl+C para salir.")
        print("Actualizando cada segundo...")
        print("\nFecha/Hora            | Hora  | Luz % | Momento del día      | Temp Color
 | RGB")
        print("-" * 90)
        
        while True:
            reading = sensor.get_reading()
            
            if reading['status'] == 'success':
                print(f"{reading['timestamp']} | {reading['hora']} | "
                      f"{reading['light_level']:>4.1f}% | "
                      f"{reading['momento_del_dia']:<18} | "
                      f"{reading['temp_color']:<10} | "
                      f"{reading['rgb']}")
            else:
                print(f"{reading['timestamp']} | Error: {reading['error_message']}")
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nPrograma interrumpido por el usuario")
    except Exception as e:
        print(f"\nError inesperado: {str(e)}")
    finally:
        print("\nPrograma finalizado")

if __name__ == "__main__":
    main()


