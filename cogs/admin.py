import logging
from disnake.ext import commands

from bot import DisredditBot


class CogAdmin(commands.Cog):
    def __init__(self, bot: DisredditBot):
        self.bot = bot
        self.log = logging.getLogger(__name__)

    def cog_load(self):
        self.log.info('Cog load')

    def cog_unload(self):
        self.log.info('Cog unload')

    @commands.command(name='reload', description='Reloads a bot cogs', hidden=True)
    @commands.is_owner()
    async def cmd_reload(self, ctx: commands.Context):
        self.bot.reload_extension('cogs.events')
        self.bot.reload_extension('cogs.errors')
        self.bot.reload_extension('cogs.admin')
        self.bot.reload_extension('cogs.general')
        self.bot.reload_extension('cogs.feed')
        await ctx.reply(':arrows_counterclockwise: Reloaded')


def setup(bot: DisredditBot) -> None:
    bot.add_cog(CogAdmin(bot))
