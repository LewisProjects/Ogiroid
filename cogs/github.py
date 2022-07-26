from disnake.ext import commands
import disnake

from utils.bot import OGIROID


class GitHub(commands.Cog):
    """Commands involving GitHub! :)"""

    def __init__(self, bot: OGIROID):
        self.bot = bot

    # Command to get information about a GitHub user
    @commands.slash_command(name="ghperson", description="Gets the Profile of the github person.")
    async def ghperson(self, ctx, ghuser: str):
        person_raw = await self.bot.session.get(f"https://api.github.com/users/{ghuser}")
        if person_raw.status != 200:
            return await ctx.send("User not found!")
        else:
            person = await person_raw.json()
        # Returning an Embed containing all the information:
        embed = disnake.Embed(
            title=f"GitHub Profile: {person['login']}",
            description=f"**Bio:** {person['bio']}",
            color=0xFFFFFF,
        )
        embed.set_thumbnail(url=f"{person['avatar_url']}")
        embed.add_field(name="Username 📛: ", value=f"__[{person['name']}]({person['html_url']})__", inline=True)
        # embed.add_field(name="Email ✉: ", value=f"{person['email']}", inline=True) Commented due to github not responding with the correct email
        embed.add_field(name="Repos 📁: ", value=f"{person['public_repos']}", inline=True)
        embed.add_field(name="Location 📍: ", value=f"{person['location']}", inline=True)
        embed.add_field(name="Company 🏢: ", value=f"{person['company']}", inline=True)
        embed.add_field(name="Followers 👥: ", value=f"{person['followers']}", inline=True)
        embed.add_field(name="Following 👥: ", value=f"{person['following']}", inline=True)
        await ctx.send(embed=embed)

    # Command to get search for GitHub repositories:
    @commands.slash_command(name="ghsearchrepo", description="Searches for the specified repo.")
    async def ghsearchrepo(self, ctx, query: str):
        pages = 1
        url = f"https://api.github.com/search/repositories?q={query}&{pages}"
        repos_raw = await self.bot.session.get(url)
        if repos_raw.status != 200:
            return await ctx.send("Repo not found!")
        else:
            repos = await repos_raw.json()  # Getting first repository from the query
        repo = repos["items"][0]
        # Returning an Embed containing all the information:
        embed = disnake.Embed(
            title=f"GitHub Repository: {repo['name']}",
            description=f"**Description:** {repo['description']}",
            color=0xFFFFFF,
        )
        embed.set_thumbnail(url=f"{repo['owner']['avatar_url']}")
        embed.add_field(
            name="Author 🖊:",
            value=f"__[{repo['owner']['login']}]({repo['owner']['html_url']})__",
            inline=True,
        )
        embed.add_field(name="Stars ⭐:", value=f"{repo['stargazers_count']}", inline=True)
        embed.add_field(name="Forks 🍴:", value=f"{repo['forks_count']}", inline=True)
        embed.add_field(name="Language 💻:", value=f"{repo['language']}", inline=True)
        if repo["license"]:
            id = repo["license"]["spdx_id"]
            embed.add_field(
                name="License name 📃:",
                value=f"{id if id != 'NOASSERTION' else repo['license']['name']}",
                inline=True,
            )
        else:
            embed.add_field(name="License name 📃:", value=f"This Repo doesn't have a license", inline=True)
        embed.add_field(name="URL 🔍:", value=f"[Click here!]({repo['html_url']})", inline=True)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(GitHub(bot))
