import disnake
from disnake.ext import commands

from utils.bot import OGIROID
from utils.exceptions import CityNotFound
from utils.shortcuts import errorEmb
from utils.wrappers.OpenWeatherMap import OpenWeatherAPI
import requests


class Info(commands.Cog):
    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.openweathermap_api_key = self.bot.config.tokens.weathermap
        self.openweather = OpenWeatherAPI(
            key=self.openweathermap_api_key, session=self.bot.session
        )

    @commands.slash_command(
        description="Get current weather for specific city",
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def weather(
        self,
        inter,
        *,
        city,
        private: bool = commands.Param(
            False, description="Send weather privately, not exposing location"
        ),
    ):
        if not self.openweather.apiKey:
            return await errorEmb(
                inter,
                "OpenWeather's API Key is not set! Please use the ``/reportbug`` command to report this issue",
            )

        try:
            weatherData = await self.openweather.get_from_city(city)
        except CityNotFound as err:
            return await errorEmb(inter, str(err))

        e = disnake.Embed(
            title=f"{weatherData.city}, {weatherData.country}",
            description=f"Feels like {round(weatherData.tempFeels.celcius)}\N{DEGREE SIGN}C, {weatherData.weatherDetail}",
            colour=disnake.Colour(0xEA6D4A),
        )
        e.set_author(
            name="OpenWeather",
            icon_url="https://openweathermap.org/themes/openweathermap/assets/vendor/owm/img/icons/logo_60x60.png",
        )
        e.add_field(
            name="Temperature",
            value=f"{round(weatherData.temp.celcius)}\N{DEGREE SIGN}C",
        )
        e.add_field(name="Humidity", value=weatherData.humidity)
        e.add_field(name="Wind", value=str(weatherData.wind))
        e.set_thumbnail(url=weatherData.iconUrl)
        if private:
            await inter.send(embed=e, ephemeral=True)
        else:
            await inter.send(embed=e)

    @commands.slash_command(description="Stats about the commands that have been ran")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def cmdstats(self, inter):
        cmdsran = self.bot.commands_ran
        sortdict = dict(sorted(cmdsran.items(), key=lambda x: x[1], reverse=True))
        value_iterator = iter(sortdict.values())
        key_iterator = iter(sortdict.keys())
        emby = disnake.Embed(
            title=f"{self.bot.user.display_name} command Stats",
            description=f"{self.bot.total_commands_ran} Commands ran this boot\n",
            color=disnake.Color.random(),
        )
        emby.add_field(
            name="Top 10 commands ran",
            value=f"🥇: /{next(key_iterator)} ({next(value_iterator)} uses)\n"
            f"🥈: /{next(key_iterator)} ({next(value_iterator)} uses)\n"
            f"🥉: /{next(key_iterator)} ({next(value_iterator)} uses)\n"
            f"🏅: /{next(key_iterator)} ({next(value_iterator)} uses)\n"
            f"🏅: /{next(key_iterator)} ({next(value_iterator)} uses)\n"
            f"🏅: /{next(key_iterator)} ({next(value_iterator)} uses)\n"
            f"🏅: /{next(key_iterator)} ({next(value_iterator)} uses)\n"
            f"🏅: /{next(key_iterator)} ({next(value_iterator)} uses)\n"
            f"🏅: /{next(key_iterator)} ({next(value_iterator)} uses)\n"
            f"🏅: /{next(key_iterator)} ({next(value_iterator)} uses)\n",
        )

        await inter.send(embed=emby)

    @commands.slash_command(description="Display current price of BTC")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def btc(self, inter):
        response = requests.get("https://shoppy.gg/api/v1/public/ticker")
        data = response.json()
        btc_prices = []
        for ticker in data.get("ticker", []):
            if ticker.get("coin") == "BTC":
                btc_prices = ticker.get("value", {})
        btc_price_usd = btc_prices.get("USD")

        embed = disnake.Embed(
            title=f"Current BTC Price",
            description=f"Bitcoin (USD): ${btc_price_usd}",
            color=self.bot.config.colors.white,
        )
        await inter.send(embed=embed)


def setup(bot):
    bot.add_cog(Info(bot))
