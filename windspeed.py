import time
import lgpio
import atexit
from datetime import datetime
import signal
import sys
import math

class Anemometer:
    def __init__(self, pin):
        """
        Inicializa el anemómetro para Raspberry Pi 5
        :param pin: Pin GPIO al que está conectado el anemómetro
        """
        # Configuración física del anemómetro
        self.RADIO_METROS = 0.09  # 12 cm en metros
        self.CAMBIOS_POR_VUELTA = 6  # 2 cambios × 3 copas
        
        # Variables de estado
        self.pin = pin
        self.wind_count = 0
        self.last_time = time.time()
        self.wind_speed = 0
        self.last_state = None
        self.total_count = 0
        
        try:
            # Inicializar la conexión con el chip GPIO
            self.h = lgpio.gpiochip_open(0)
            # Configurar el pin como entrada con pull-up
            lgpio.gpio_claim_input(self.h, self.pin, lgpio.SET_PULL_UP)
            # Leer estado inicial
            self.last_state = lgpio.gpio_read(self.h, self.pin)
            
            print(f"Anemómetro inicializado en GPIO{pin}")
            print(f"Radio: {self.RADIO_METROS*100} cm")
            
        except Exception as e:
            print(f"Error al inicializar GPIO: {str(e)}")
            sys.exit(1)
        
        # Registrar función de limpieza
        atexit.register(self.cleanup)
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        print("\nSeñal recibida. Limpiando GPIO...")
        self.cleanup()
        sys.exit(0)
    
    def check_rotation(self):
        """
        Verifica si hay rotación del anemómetro
        """
        current_state = lgpio.gpio_read(self.h, self.pin)
        if current_state != self.last_state:
            self.wind_count += 1
            self.total_count += 1
            self.last_state = current_state
    
    def calculate_speed(self):
        """
        Calcula la velocidad del viento usando:
        ω = θ / t [vueltas/s]
        v = ω × r [m/s]
        """
        current_time = time.time()
        time_diff = current_time - self.last_time
        
        if time_diff > 0 and self.wind_count > 0:
            # Calcular vueltas completas
            vueltas = self.wind_count / self.CAMBIOS_POR_VUELTA
            
            # Calcular velocidad angular (ω) en radianes/segundo
            omega = (vueltas * 2 * math.pi) / time_diff
            
            # Calcular velocidad tangencial en m/s
            velocidad_ms = omega * self.RADIO_METROS
            
            # Convertir a km/h
            self.wind_speed = velocidad_ms * 3.6
            
            # Debug info
            print(f"\nDatos de medición:")
            print(f"Cambios detectados: {self.wind_count}")
            print(f"Vueltas completas: {vueltas:.2f}")
            print(f"Tiempo: {time_diff:.2f} s")
            print(f"Velocidad angular: {omega:.2f} rad/s")
            print(f"Velocidad: {velocidad_ms:.2f} m/s = {self.wind_speed:.2f} km/h")
        
        self.wind_count = 0
        self.last_time = current_time
        
        return self.wind_speed
    
    def get_reading(self):
        """
        Obtiene una lectura del sensor durante un período de muestreo
        """
        # Tomar muestras durante 2 segundos
        start_sample = time.time()
        while (time.time() - start_sample) < 2:
            self.check_rotation()
            time.sleep(0.01)
            
        speed = self.calculate_speed()
        return {
            'timestamp': datetime.now().isoformat(),
            'wind_speed': round(speed, 2),
            'wind_speed_ms': round(speed / 3.6, 2),
            'units': {
                'primary': 'km/h',
                'secondary': 'm/s'
            },
            'total_cambios': self.total_count
        }
    
    def cleanup(self):
        try:
            if hasattr(self, 'h'):
                lgpio.gpio_free(self.h, self.pin)
                lgpio.gpiochip_close(self.h)
            print("GPIO limpiado exitosamente")
        except:
            pass

def main():
    anemometer = None
    try:
        anemometer = Anemometer(pin=17)
        
        print(f"\nMonitoreando velocidad del viento en GPIO{17}.")
        print("Presiona Ctrl+C para salir.")
        
        while True:
            reading = anemometer.get_reading()
            print(f"\nVelocidad del viento:")
            print(f"  {reading['wind_speed']} {reading['units']['primary']}")
            print(f"  {reading['wind_speed_ms']} {reading['units']['secondary']}")
            
    except KeyboardInterrupt:
        print("\nPrograma interrumpido por el usuario")
    except Exception as e:
        print(f"\nError inesperado: {str(e)}")
    finally:
        if anemometer:
            anemometer.cleanup()
        print("Programa finalizado")

if __name__ == "__main__":
    main()
