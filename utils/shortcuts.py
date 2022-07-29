from __future__ import annotations

import disnake

from disnake import Embed


class QuickEmb:
    def __init__(self, inter, msg, color=disnake.Color.red()):
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
