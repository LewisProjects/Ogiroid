import disnake
from disnake import ApplicationCommandInteraction
from disnake.ext import commands

from utils.bot import OGIROID
from utils.exceptions import CityNotFound
from utils.shortcuts import errorEmb
from utils.wrappers.OpenWeatherMap import OpenWeatherAPI
import requests
from utils.CONSTANTS import CURRENCIES


async def autocomplete_currencies(inter, user_input: str):
    return [x for x in CURRENCIES.values() if user_input.lower() in x.lower()][0:25]


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

    @commands.slash_command(description="Convert currencies to other currencies")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def exchange(
        self,
        inter: ApplicationCommandInteraction,
        base=commands.Param(
            description="Base currency to convert from",
            autocomplete=autocomplete_currencies,
        ),
        target=commands.Param(
            description="Target currency to convert to",
            autocomplete=autocomplete_currencies,
        ),
        amount=commands.Param(description="Amount of money to convert", default=1),
    ):
        await inter.response.defer()
        try:
            amount = float(amount)
        except ValueError:
            return await errorEmb(inter, "Amount must be a number")

        try:
            base = base.upper().split(" ")[0]
            target = target.upper().split(" ")[0]
        except AttributeError or IndexError:
            return await errorEmb(inter, "Currency must be a string")

        if base not in CURRENCIES.values() and base not in CURRENCIES.keys():
            return await errorEmb(inter, "Base currency not found")
        if target not in CURRENCIES.values() and target not in CURRENCIES.keys():
            return await errorEmb(inter, "Target currency not found")

        response = requests.get(
            f"https://openexchangerates.org/api/latest.json?app_id={self.bot.config.tokens.currency}&symbols={target}"
        )
        data = response.json()

        rates = data.get("rates")
        target_rate = rates.get(target)
        usd_amount = amount * target_rate
        # Since it doesn't support changing the base currency on the free tier, we have to do this math stuff
        if not base == "USD":
            response = requests.get(
                f"https://openexchangerates.org/api/latest.json?app_id={self.bot.config.tokens.currency}&symbols={base}"
            )
            data = response.json()
            rates = data.get("rates")
            base_rate = rates.get(base)
            converted_amount = usd_amount / base_rate
        else:
            converted_amount = usd_amount

        embed = disnake.Embed(
            title=f"Currency Conversion",
            description=f"{amount} {base} = {round(converted_amount, 2)} {target}",
            color=self.bot.config.colors.white,
        )
        embed.timestamp = disnake.utils.utcnow()

        await inter.send(embed=embed)


def setup(bot):
    bot.add_cog(Info(bot))
