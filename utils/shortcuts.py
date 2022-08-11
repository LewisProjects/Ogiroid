from __future__ import annotations

import asyncio
from datetime import datetime

import disnake
from disnake import Embed, ApplicationCommandInteraction


async def wait_until(timestamp):
    now = datetime.now()
    dt = datetime.fromtimestamp(timestamp)
    await asyncio.sleep((dt - now).total_seconds())


def get_expiry(time: int):
    time = int(time)
    return f"<t:{time}:R>" if str(time) != str(9999999999) else "never"

async def permsEmb(inter: ApplicationCommandInteraction, *, permissions: str):
    """@summary creates a disnake embed, so I can send it with x details easier"""
    emb = Embed(
        title=':x: You are missing permissions',
        description=f'You need the following permission(s) to use /{inter.application_command.qualified_name}:\n{permissions}',
        color=disnake.Color.red()
    )
    await inter.send(embed=emb, ephemeral=True, allowed_mentions=disnake.AllowedMentions(everyone=False, users=False, roles=False, replied_user=True))

async def errorEmb(inter, text, *args, **kwargs):
    emb = Embed(description=text, color=disnake.Color.red(), *args, **kwargs)
    await inter.send(embed=emb, ephemeral=True, allowed_mentions=disnake.AllowedMentions(everyone=False, users=False, roles=False, replied_user=True))

async def sucEmb(inter, text, ephemeral=True):
    emb = Embed(description=text, color=disnake.Color.green())
    await inter.send(embed=emb, ephemeral=ephemeral, allowed_mentions=disnake.AllowedMentions(everyone=False, users=False, roles=False, replied_user=True))


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
