import disnake
from disnake.ext import commands
import requests
from utils.bot import OGIROID


class BTCCommand(commands.Cog, name="BTC"):
    """BTC Command"""

    def __init__(self, bot: OGIROID):
        self.bot = bot

    @commands.slash_command(name="btc", description="Display current price of BTC")
    async def help(self, inter):
        """Display current price of BTC"""
        response = requests.get('https://shoppy.gg/api/v1/public/ticker')
        data = response.json()
        for ticker in data.get('ticker', []):
            if ticker.get('coin') == 'BTC':
                btc_prices = ticker.get('value', {})
        btc_price_usd = btc_prices.get('USD')
      
        embbtc = disnake.Embed(
            title=f"Current BTC Price",
            description=f"Bitcoin (USD): ${btc_price_usd}",
            color=disnake.Color.random(),
        )
        await inter.send(embed=embbtc)


def setup(bot: commands.Bot):
    bot.add_cog(BTCCommand(bot))
