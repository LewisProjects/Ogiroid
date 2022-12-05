import aiohttp

from utils.exceptions import CityNotFound, InvalidAPIKEY


class Temperature:
    def __init__(self, temperature):
        """Uses kelvin by default"""
        self._temperature = round(temperature, 2)

    @property
    def temperature(self):
        return self._temperature

    def __str__(self):
        return "{} K".format(round(self.temperature, 2))

    def __repr__(self):
        return "Temperature=({}, default_type=K)".format(round(self.temperature, 2))

    @property
    def kelvin(self):
        return round(self._temperature, 2)

    @property
    def fahrenheit(self):
        return round((self._temperature - 273.15) * 1.8 + 32, 2)

    @property
    def celcius(self):
        return round(self._temperature - 273.15, 2)


class Wind:
    __slots__ = ("speed", "degree")

    def __init__(self, windData):
        """Speed uses m/s by default."""
        self.speed = windData["speed"]
        self.degree = windData["deg"]

    def __str__(self):
        return "{}m/s".format(self.speed)

    def __repr__(self):
        return "<Wind(degree={}, speed={})>"


class Weather:
    __slots__ = (
        "rawData",
        "city",
        "country",
        "wind",
        "icon",
        "iconUrl",
        "temp",
        "tempMin",
        "tempMax",
        "tempFeels",
        "weather",
        "weatherDetail",
    )

    def __init__(self, data):
        self.rawData = data
        self.city = data["name"]
        self.country = data["sys"]["country"]
        self.wind = Wind(data["wind"])
        self.icon = data["weather"][0]["icon"]
        self.iconUrl = "https://openweathermap.org/img/wn/{}@2x.png".format(self.icon)
        self.temp = Temperature(data["main"]["temp"])
        self.tempMin = Temperature(data["main"]["temp_min"])
        self.tempMax = Temperature(data["main"]["temp_max"])
        self.tempFeels = Temperature(data["main"]["feels_like"])
        self.weather = data["weather"][0]["main"]
        self.weatherDetail = str(data["weather"][0]["description"]).title()

    def __str__(self):
        return self.weather

    def __repr__(self):
        return "200 - {} ({})".format(self.weather, self.temp)

    @property
    def humidity(self):
        return "{}%".format(self.rawData["main"]["humidity"])

    @property
    def temperature(self):
        return self.temp

    @property
    def feelslike(self):
        return self.feelslike


class OpenWeatherAPI:
    def __init__(self, key, session=None):
        """Wrapper for OpenWeather's API.
        Parameter
        ---------
        key = Your openweather api key
        """
        self.apiKey = key
        self.session = session or aiohttp.ClientSession()
        self.baseUrl = (
            "https://api.openweathermap.org/data/2.5/weather?{type}={query}&appid={key}"
        )

    async def get(self, _type, query):
        """Get weather report."""
        async with self.session.get(
            self.baseUrl.format(type=_type, query=query, key=self.apiKey)
        ) as res:
            weatherData = await res.json()
            if weatherData["cod"] == "404":
                raise CityNotFound(query)
            elif weatherData["cod"] == "401":
                raise InvalidAPIKEY
            return Weather(weatherData)

    async def get_from_city(self, city):
        """Get weather report from a city name."""
        return await self.get("q", city)

    async def get_from_zip(self, zipCode):
        """Get weather report from a zip code."""
        return await self.get("zip", zipCode)
