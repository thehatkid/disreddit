import logging
import disnake
from disnake.ext import commands

from bot import DisredditBot


class CogEvents(commands.Cog):
    def __init__(self, bot: DisredditBot):
        self.bot = bot
        self.log = logging.getLogger(__name__)

    def cog_load(self):
        self.log.info('Cog load')

    def cog_unload(self):
        self.log.info('Cog unload')

    @commands.Cog.listener()
    async def on_ready(self):
        self.log.info('Bot is ready as {0} (ID: {0.id})'.format(self.bot.user))

    @commands.Cog.listener()
    async def on_guild_join(self, guild: disnake.Guild):
        self.log.info('Bot has been invited to guild: {0.name} (ID: {0.id})'.format(guild))

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: disnake.Guild):
        self.log.info('Bot has been kicked from guild: {0.name} (ID: {0.id})'.format(guild))


def setup(bot: DisredditBot) -> None:
    bot.add_cog(CogEvents(bot))
