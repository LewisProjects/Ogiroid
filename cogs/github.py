import string
from disnake.ext import commands
import disnake
import requests
from prettytable import PrettyTable


class GitHub(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

    #Command to get information about a GitHub user
    @commands.command(aliases=["githubperson","ghp"])
    async def ghperson(self, ctx):
        person = requests.get(f"https://api.github.com/users/{ctx.message.content.split(' ')[1]}")
        if person.status_code == 200:
            #Returning an Embed containing all the information:
            embed = disnake.Embed(title=f"GitHub Profile: {person.json()['login']}", description=f"**Bio:** {person.json()['bio']}", color=0xFFFFFF)
            embed.set_thumbnail(url=f"{person.json()['avatar_url']}")
            embed.add_field(name="Username 📛: ", value=f"__[{person.json()['name']}]({person.json()['html_url']})__", inline=True)
            embed.add_field(name="Email ✉: ", value=f"{person.json()['email']}", inline=True)
            embed.add_field(name="Location 📍: ", value=f"{person.json()['location']}", inline=True)
            embed.add_field(name="Company 🏢: ", value=f"{person.json()['company']}", inline=True)
            embed.add_field(name="Followers 👥: ", value=f"{person.json()['followers']}", inline=True)
            embed.add_field(name="Following 👥: ", value=f"{person.json()['following']}", inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send("User not found!")

    #Command to get search for GitHub repositories:
    @commands.command(aliases=["ghsr","githubsearchrepository","githubsr"])
    async def ghsearchrepo(self, ctx):
        query = ctx.message.content.split(' ')[1]
        pages = 1
        url = f"https://api.github.com/search/repositories?q={query}&{pages}"
        repos = requests.get(url)
        #Getting first repository from the query
        repo = repos.json()['items'][0]
        #Returning an Embed containing all the information:
        embed = disnake.Embed(title=f"GitHub Repository: {repo['name']}", description=f"**Description:** {repo['description']}", color=0xFFFFFF)
        embed.set_thumbnail(url=f"{repo['owner']['avatar_url']}")
        embed.add_field(name="Author 🖊:", value=f"__[{repo['owner']['login']}]({repo['owner']['html_url']})__", inline=True)
        embed.add_field(name="Stars ⭐:", value=f"{repo['stargazers_count']}", inline=True)
        embed.add_field(name="Forks 🍴:", value=f"{repo['forks_count']}", inline=True)
        embed.add_field(name="Language 💻:", value=f"{repo['language']}", inline=True)
        embed.add_field(name="License name 📃:", value=f"{repo['license']['name']}", inline=True)
        embed.add_field(name="URL 🔍:", value=f"[Click here!]({repo['html_url']})", inline=True)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(GitHub(bot))
