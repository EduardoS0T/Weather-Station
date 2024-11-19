import time
import board
import adafruit_dht
import atexit
from datetime import datetime
import signal
import sys
import logging

class DHT11:
    def __init__(self, pin, temp_offset=-2):
        """
        Inicializa el sensor DHT11 (KY-015)
        :param pin: Pin GPIO para la señal de datos
        :param temp_offset: Factor de calibración de temperatura
        """
        self.pin = pin
        self.last_reading = None
        self.TEMP_OFFSET = temp_offset
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        try:
            # En Raspberry Pi, usamos el número de pin directamente
            self.device = adafruit_dht.DHT11(getattr(board, f'D{pin}'))
            logging.info(f"Sensor KY-015 inicializado en GPIO{pin}")
            logging.info("Conexiones:")
            logging.info(f"SEÑAL → GPIO{pin}")
            logging.info("VCC   → 3.3V")
            logging.info("GND   → GND")
            
            # Tiempo de estabilización inicial
            logging.info("Esperando 2 segundos para estabilizar el sensor...")
            time.sleep(2)  # Reducido a 2 segundos, suficiente para DHT11
            
        except Exception as e:
            logging.error(f"Error al inicializar sensor: {str(e)}")
            sys.exit(1)
        
        # Registrar función de limpieza
        atexit.register(self.cleanup)
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        logging.info("Señal recibida. Limpiando recursos...")
        self.cleanup()
        sys.exit(0)
    
    def calibrate_temperature(self, raw_temp):
        """
        Aplica calibración a la temperatura
        """
        return round(raw_temp + self.TEMP_OFFSET, 1)
    
    def get_reading(self, retries=3):
        """
        Obtiene una lectura del sensor con reintentos y aplica calibración
        """
        for attempt in range(retries):
            try:
                raw_temp = self.device.temperature
                humidity = self.device.humidity
                
                if raw_temp is not None and humidity is not None:
                    calibrated_temp = self.calibrate_temperature(raw_temp)
                    
                    reading = {
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'temperature': calibrated_temp,
                        'temperature_raw': raw_temp,
                        'humidity': humidity,
                        'temperature_f': round((calibrated_temp * 9/5) + 32, 1),
                        'status': 'success'
                    }
                    self.last_reading = reading
                    return reading
                    
            except RuntimeError as error:
                logging.warning(f"Intento {attempt + 1}/{retries} fallido: {error}")
                if attempt < retries - 1:
                    time.sleep(1)  # Espera 1 segundo entre intentos
                continue
                
            except Exception as error:
                logging.error(f"Error inesperado: {error}")
                self.cleanup()
                return {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'status': 'error',
                    'error_message': str(error)
                }
            
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'error',
            'error_message': 'Máximo de reintentos alcanzado'
        }
    
    def cleanup(self):
        """
        Limpia los recursos del sensor
        """
        try:
            self.device.exit()
            logging.info("Sensor liberado correctamente")
        except:
            pass

def main():
    """
    Función principal para pruebas
    """
    dht11 = None
    try:
        # Puedes cambiar el pin y el offset de temperatura según necesites
        dht11 = DHT11(pin=22, temp_offset=-2)
        
        print("\nMonitoreando temperatura y humedad. Presiona Ctrl+C para salir.")
        print("Actualizando cada 3 segundos...")
        print("\nFecha/Hora            | Temp (°C) | Temp (°F) | Humedad (%)")
        print("-" * 60)
        
        while True:
            reading = dht11.get_reading()
            
            if reading['status'] == 'success':
                print(f"{reading['timestamp']} |   {reading['temperature']:>5}°C |   {read
ing['temperature_f']:>5}°F |    {reading['humidity']}%")
            else:
                print(f"{reading['timestamp']} | Error: {reading['error_message']}")
            
            time.sleep(3)  # Intervalo entre lecturas aumentado a 3 segundos para mayor es
tabilidad
            
    except KeyboardInterrupt:
        print("\nPrograma interrumpido por el usuario")
    except Exception as e:
        logging.error(f"Error inesperado: {str(e)}")
    finally:
        if dht11:
            dht11.cleanup()
        print("\nPrograma finalizado")

if __name__ == "__main__":
    main()
