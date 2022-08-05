from __future__ import annotations

import disnake

from disnake import Embed


def get_expiry(time):
    return f"<t:{time}:R>" if str(time) != str(9999999999) else "never"


async def errorEmb(inter, text):
    emb = Embed(description=text, color=disnake.Color.red())
    await inter.send(embed=emb, ephemeral=True)


async def sucEmb(inter, text, ephemeral=True):
    emb = Embed(description=text, color=disnake.Color.green())
    await inter.send(embed=emb, ephemeral=ephemeral)


class QuickEmb:
    def __init__(self, inter, msg, color=0xFFFFFF):
        self.inter = inter
        self.msg = msg
        self.color = color

    def error(self):
        self.color = disnake.Color.red()
        return self

    def success(self):
        self.color = disnake.Color.green()
        return self

    async def send(self):
        emb = Embed(description=self.msg, color=self.color)
        await self.inter.send(embed=emb)


def manage_messages_perms(inter):
    return inter.channel.permissions_for(inter.author).manage_messages
