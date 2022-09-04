from disnake import ApplicationCommandInteraction
from disnake.ext.commands import check


def is_dev():
    devs = [511724576674414600, 662656158129192961, 963860161976467498]

    def predicate(inter : ApplicationCommandInteraction):
        return inter.author.id in devs

    return check(predicate)
