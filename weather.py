import aiohttp


#Замена описания погоды на эмодзи
weather_emoji_mapping = {
    'thunderstorm with light rain': '⛈️',
    'thunderstorm with rain': '⛈️',
    'thunderstorm with heavy rain': '⛈️',
    'light thunderstorm': '⛈️',
    'thunderstorm': '⛈️',
    'heavy thunderstorm': '⛈️',
    'ragged thunderstorm': '⛈️',
    'thunderstorm with light drizzle': '⛈️',
    'thunderstorm with drizzle': '⛈️',
    'thunderstorm with heavy drizzle': '⛈️',
    'light intensity drizzle': '🌧️',
    'drizzle': '🌧️',
    'heavy intensity drizzle': '🌧️',
    'light intensity drizzle rain': '🌧️',
    'drizzle rain': '🌧️',
    'heavy intensity drizzle rain': '🌧️',
    'shower rain and drizzle': '🌧️',
    'heavy shower rain and drizzle': '🌧️',
    'shower drizzle': '🌧️',
    'light rain': '🌧️',
    'moderate rain': '🌧️',
    'heavy intensity rain': '🌧️',
    'very heavy rain': '🌧️',
    'extreme rain': '🌧️',
    'freezing rain': '🌧️',
    'light intensity shower rain': '🌧️',
    'shower rain': '🌧️',
    'heavy intensity shower rain': '🌧️',
    'ragged shower rain': '🌧️',
    'light snow': '❄️',
    'snow': '❄️',
    'heavy snow': '❄️',
    'sleet': '❄️',
    'light shower sleet': '❄️',
    'shower sleet': '❄️',
    'light rain and snow': '❄️',
    'rain and snow': '❄️',
    'light shower snow': '❄️',
    'shower snow': '❄️',
    'heavy shower snow': '❄️',
    'mist': '🌫️',
    'smoke': '🌫️',
    'haze': '🌫️',
    'sand/dust whirls': '🌫️',
    'fog': '🌫️',
    'sand': '🌫️',
    'dust': '🌫️',
    'volcanic ash': '🌫️',
    'squalls': '🌫️',
    'tornado': '🌪️',
    'clear sky': '☀️',
    'few clouds: 11-25%': '🌤️',
    'scattered clouds: 25-50%': '🌥️',
    'broken clouds: 51-84%': '☁️',
    'overcast clouds: 85-100%': '☁️'
}




#Функция для получения 
async def get_weather(latitude, longitude, api_key):
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={api_key}&units=metric"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                weather_data = await response.json()
                temp = weather_data["main"]["temp"]
                description = weather_data["weather"][0]["description"]
                emoji = weather_emoji_mapping.get(description, '')  # Получаем соответствующий эмодзи или пустую строку, если сопоставление не найдено
                return f"{temp}°C {emoji}"
            else:
                return "Не удалось получить информацию о погоде."