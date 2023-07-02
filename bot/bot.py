import logging
from datetime import datetime
from databases import Database
import asyncpraw
import disnake
from disnake.ext import commands

from bot.utils import RedditFeed


class DisredditBot(commands.Bot):
    def __init__(self, database_path: str, *args, **kwargs):
        self.log = logging.getLogger('Disreddit')
        self.start_time = datetime.now()
        self.database = Database('sqlite:///{0}'.format(database_path))
        self.feeder = RedditFeed(self)
        self.config = {
            'text_limit': 1000,
            'feeders_limit': 5
        }

        self.log.info('Starting disnake {0} {1} with asyncpraw {2}...'.format(
            disnake.__version__,
            disnake.version_info.releaselevel,
            asyncpraw.__version__
        ))

        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=disnake.Intents(
                guilds=True,
                messages=True
            ),
            allowed_mentions=disnake.AllowedMentions(
                everyone=False,
                replied_user=False,
                users=False,
                roles=False
            ),
            status=disnake.Status.idle,
            activity=disnake.Activity(
                name='Starting...',
                type=disnake.ActivityType.playing
            ),
            command_sync_flags=commands.flags.CommandSyncFlags(
                allow_command_deletion=True,
                sync_commands=True,
                sync_commands_debug=True,
                sync_global_commands=True,
                sync_guild_commands=True,
                sync_on_cog_actions=True
            ),
            *args,
            **kwargs
        )

    async def database_connect(self) -> None:
        await self.database.connect()
        await self.database.execute('''
        CREATE TABLE IF NOT EXISTS "feeds" (
            "guild_id" INTEGER NOT NULL,
            "channel_id" INTEGER NOT NULL,
            "subreddit" TEXT NOT NULL
        )
        ''')
