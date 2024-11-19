# Weather Station with Raspberry Pi

## Description
Real-time weather monitoring station implemented with Raspberry Pi 5 that tracks:
- Temperature and humidity
- Wind speed
- Rain detection
- Light intensity and time of day

Data is displayed both on a 16x2 LCD display and through a Streamlit web interface.

## Hardware Components
- Raspberry Pi 5
- 16x2 LCD Display
- DHT11 Sensor (temperature and humidity)
- Anemometer (3 cups, 9cm radius)
- YL-83 Rain Sensor
- TCS34725 Light Sensor
- Required cables and resistors

## Pin Connections
```
LCD:
- RS -> GPIO25
- E  -> GPIO24
- D4 -> GPIO23
- D5 -> GPIO4
- D6 -> GPIO5
- D7 -> GPIO6

Sensors:
- Anemometer -> GPIO17
- Rain Sensor -> GPIO27
- DHT11 -> GPIO22
- Light Sensor -> I2C (SDA and SCL)
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/EduardoS0T/Weather-Station
cd weather-station
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure Raspberry Pi:
```bash
# Edit /boot/config.txt
sudo nano /boot/config.txt

# Add:
dtparam=i2c_arm=on
dtparam=i2c1=on
gpio=25,24,23,4,5,6,17,27,22=op
dtoverlay=dht11,gpiopin=22
enable_uart=1
```

5. Run the program:
```bash
streamlit run main.py 
```

## Features
- Real-time weather condition monitoring
- Responsive web interface using Streamlit
- Physical LCD display with automatic data rotation
- Precise wind speed calculation using parallel processing
- Automatic time of day determination (Day/Evening/Night)
- Historical data storage
- Trend graphs and analytics

## Project Structure
```
weather-station/
├── weather_station.py   # Main program
├── requirements.txt     # Dependencies
├── README.md           # Documentation
└── venv/               # Virtual environment
```

## Required Libraries
```txt
streamlit
adafruit-circuitpython-dht
adafruit-circuitpython-tcs34725
lgpio
```

## Usage
The system provides two interfaces:

1. Physical LCD Display:
- Rotates between temperature/humidity, wind speed, and light conditions
- Updates every 3 seconds
- Shows current conditions in real-time

2. Web Interface (Streamlit):
- Real-time metrics display
- Historical trend graphs
- Weather condition indicators
- Accessible through any web browser at http://localhost:8501

## Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments
- Weather sensor integration based on Raspberry Pi GPIO
- Real-time monitoring using Streamlit
- Parallel processing for accurate wind speed calculation
- Custom LCD interface for physical display

## Authors
- FSE08 - *Initial work and development*
