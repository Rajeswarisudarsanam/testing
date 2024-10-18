import requests
import time
from datetime import datetime
from flask import Flask, jsonify
from sqlalchemy import create_engine, Column, Float, String, Date, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import unittest

API_KEY = 'your_api_key_here'  # Replace with your actual API key
CITIES = ['Delhi', 'Mumbai', 'Chennai', 'Bangalore', 'Kolkata', 'Hyderabad']
BASE_URL = 'https://api.openweathermap.org/data/2.5/weather'
INTERVAL = 300  # in seconds (5 minutes)

app = Flask(__name__)
Base = declarative_base()

# Database setup
engine = create_engine('sqlite:///weather.db')
Session = sessionmaker(bind=engine)
session = Session()

class WeatherSummary(Base):
    __tablename__ = 'weather_summary'
    id = Column(Integer, primary_key=True)
    date = Column(Date, unique=True)
    avg_temp = Column(Float)
    max_temp = Column(Float)
    min_temp = Column(Float)
    dominant_condition = Column(String)

Base.metadata.create_all(engine)

def fetch_weather_data(city):
    response = requests.get(BASE_URL, params={'q': city, 'appid': API_KEY})
    return response.json()

def convert_kelvin_to_celsius(kelvin):
    return kelvin - 273.15

def process_weather_data(data):
    # Extract relevant information
    main = data['main']
    weather = data['weather'][0]
    temperature = convert_kelvin_to_celsius(main['temp'])
    feels_like = convert_kelvin_to_celsius(main['feels_like'])

    return {
        'temperature': temperature,
        'feels_like': feels_like,
        'condition': weather['main'],
        'timestamp': datetime.fromtimestamp(data['dt']).date()
    }

def update_weather_summary(data):
    # Update logic for daily summary
    date = data['timestamp']
    existing_summary = session.query(WeatherSummary).filter_by(date=date).first()

    if existing_summary:
        existing_summary.avg_temp = (existing_summary.avg_temp + data['temperature']) / 2
        existing_summary.max_temp = max(existing_summary.max_temp, data['temperature'])
        existing_summary.min_temp = min(existing_summary.min_temp, data['temperature'])
    else:
        summary = WeatherSummary(
            date=date,
            avg_temp=data['temperature'],
            max_temp=data['temperature'],
            min_temp=data['temperature'],
            dominant_condition=data['condition']
        )
        session.add(summary)

    session.commit()

@app.route('/weather', methods=['GET'])
def get_weather_summary():
    summaries = session.query(WeatherSummary).all()
    return jsonify([{
        'date': s.date,
        'avg_temp': s.avg_temp,
        'max_temp': s.max_temp,
        'min_temp': s.min_temp,
        'dominant_condition': s.dominant_condition
    } for s in summaries])

class TestWeatherFunctions(unittest.TestCase):
    def test_kelvin_to_celsius(self):
        self.assertAlmostEqual(convert_kelvin_to_celsius(300), 26.85, places=2)

if __name__ == '__main__':
    # Run the Flask app in a separate thread
    import threading
    threading.Thread(target=lambda: app.run(debug=True, use_reloader=False)).start()
    
    # Run the weather data fetching loop
    while True:
        for city in CITIES:
            data = fetch_weather_data(city)
            processed_data = process_weather_data(data)
            update_weather_summary(processed_data)
            time.sleep(INTERVAL)

    # Uncomment the following line to run tests when the script is executed
    # unittest.main()
