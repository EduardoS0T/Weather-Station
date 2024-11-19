import time
import lgpio
import atexit
from datetime import datetime
import signal
import sys

class RainSensor:
    def __init__(self, pin):
        """
        Inicializa el sensor de lluvia YL-83
        :param pin: Pin GPIO para la señal digital
        """
        self.pin = pin
        self.last_reading = None
        
        try:
            # Inicializar la conexión con el chip GPIO
            self.h = lgpio.gpiochip_open(0)
            # Configurar el pin digital como entrada
            lgpio.gpio_claim_input(self.h, self.pin, lgpio.SET_PULL_UP)
            
            print(f"Sensor de lluvia inicializado en GPIO{pin}")
            
        except Exception as e:
            print(f"Error al inicializar GPIO: {str(e)}")
            sys.exit(1)
        
        # Registrar función de limpieza
        atexit.register(self.cleanup)
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """
        Manejador de señales para interrupciones
        """
        print("\nSeñal recibida. Limpiando GPIO...")
        self.cleanup()
        sys.exit(0)
    
    def get_reading(self):
        """
        Obtiene una lectura del sensor
        El sensor da 0 cuando detecta lluvia y 1 cuando está seco
        :return: Diccionario con el estado de lluvia y timestamp
        """
        try:
            # Tomar varias muestras para evitar falsas lecturas
            samples = []
            for _ in range(5):  # Tomar 5 muestras
                samples.append(lgpio.gpio_read(self.h, self.pin))
                time.sleep(0.1)
            
            # Si la mayoría de las muestras son 0, está lloviendo
            is_raining = sum(samples) < len(samples)/2
            
            # Determinar el estado basado en las muestras
            if is_raining:
                rain_status = "Lluvia detectada"
                rain_code = 1
            else:
                rain_status = "Sin lluvia"
                rain_code = 0
            
            reading = {
                'timestamp': datetime.now().isoformat(),
                'is_raining': is_raining,
                'rain_status': rain_status,
                'rain_code': rain_code,
                'raw_value': samples[-1]  # Último valor leído
            }
            
            self.last_reading = reading
            return reading
            
        except Exception as e:
            print(f"Error al leer el sensor: {str(e)}")
            return None
    
    def cleanup(self):
        """
        Limpia los recursos GPIO
        """
        try:
            if hasattr(self, 'h'):
                lgpio.gpio_free(self.h, self.pin)
                lgpio.gpiochip_close(self.h)
            print("GPIO limpiado exitosamente")
        except:
            pass

def main():
    """
    Función principal para pruebas
    """
    rain_sensor = None
    try:
        # Usar GPIO27 (ajusta según tu conexión)
        rain_sensor = RainSensor(pin=27)
        
        print("\nMonitoreando lluvia. Presiona Ctrl+C para salir.")
        print("Códigos de estado:")
        print("  0 = Sin lluvia")
        print("  1 = Lluvia detectada")
        
        while True:
            reading = rain_sensor.get_reading()
            if reading:
                print(f"\nEstado: {reading['rain_status']}")
                print(f"Código: {reading['rain_code']}")
                print(f"Valor raw: {reading['raw_value']}")
                
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nPrograma interrumpido por el usuario")
    except Exception as e:
        print(f"\nError inesperado: {str(e)}")
    finally:
        if rain_sensor:
            rain_sensor.cleanup()
        print("Programa finalizado")

if __name__ == "__main__":
    main()
