import logging
import disnake
from disnake.ext import commands


log = logging.getLogger(__name__)


class CogCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='ping', description='Shows embed with bot latency')
    async def cmd_ping(self, ctx: commands.Context):
        embed = disnake.Embed(
            title=':ping_pong: Pong!',
            colour=disnake.Colour.blurple()
        )
        embed.add_field(
            name=':signal_strength: Websocket Latency',
            value='{}ms'.format(round(self.bot.latency * 1000)),
            inline=False
        )
        embed.set_footer(
            text='Requested by {0}#{1}'.format(
                ctx.author.name, ctx.author.discriminator
            ),
            icon_url=ctx.author.avatar
        )
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(CogCommands(bot))
    log.info('Loaded cog')


def teardown(bot: commands.Bot) -> None:
    log.info('Unloaded cog')
