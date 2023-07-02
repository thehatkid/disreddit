import logging
import asyncio
import disnake
from disnake import Option, OptionType, ChannelType
from disnake.ext import commands

from bot import DisredditBot
from bot.utils import exceptions


class CogFeed(commands.Cog):
    def __init__(self, bot: DisredditBot):
        self.bot = bot
        self.log = logging.getLogger(__name__)
        self.feeder = self.bot.feeder

    def cog_load(self):
        self.log.info('Cog load')
        self.bot.loop.create_task(self._start_feeders())

    def cog_unload(self):
        self.log.info('Cog unload')
        self.feeder.feed_stop_all()

    async def _start_feeders(self) -> None:
        if len(self.feeder.feeders) > 0:
            return

        await self.bot.wait_until_ready()

        while True:
            if not self.bot.database.is_connected:
                await asyncio.sleep(0.2)
            else:
                break

        feeds = await self.bot.database.fetch_all('SELECT channel_id, subreddit FROM feeds')
        for feed in feeds:
            self.log.info(f'Trying to start feed "{feed[1]}" for channel {feed[0]}...')
            try:
                await self.feeder.feed_start(feed[1], feed[0])
            except Exception as e:
                self.log.error(f'Failed to start feed "{feed[1]}" for channel {feed[0]}: {e}')
            else:
                self.log.info(f'Started feed "{feed[1]}" for channel {feed[0]}')

    @commands.slash_command(
        name='subscribe',
        description='Subscribes Subreddit feed to current or selected channel',
        dm_permission=False,
        default_member_permissions=disnake.Permissions(manage_channels=True),
        options=[
            Option(
                name='subreddit',
                description='The Subreddit name to subscribe the feed',
                type=OptionType.string,
                required=True
            ),
            Option(
                name='channel',
                description='The channel to start Subreddit feed subscription',
                type=OptionType.channel,
                required=False,
                channel_types=[
                    ChannelType.text,
                    ChannelType.voice,
                    ChannelType.news,
                    ChannelType.stage_voice,
                    ChannelType.public_thread,
                    ChannelType.private_thread,
                    ChannelType.news_thread
                ]
            )
        ]
    )
    async def scmd_subscribe(self, ia: disnake.AppCmdInter, subreddit: str, channel: disnake.TextChannel = None):
        if not channel:
            channel = ia.channel

        await ia.response.defer()

        try:
            guild_tasks = self.feeder.feeders[ia.guild.id]
        except KeyError:
            pass
        else:
            if len(guild_tasks) >= self.bot.config['feeders_limit']:
                await ia.edit_original_response(f':x: Reached limit of feeds (max: {self.bot.config["feeders_limit"]}) for this server')
                return

            for task in guild_tasks:
                if task.subreddit.lower() == subreddit.lower() and task.channel == channel.id:
                    await ia.edit_original_response(f':x: Already exists feed of `r/{task.subreddit}` in {channel.mention}')
                    return

        try:
            result = await self.feeder.feed_start(subreddit, channel.id)
        except exceptions.CannotSendMessages:
            await ia.edit_original_response(f':x: Bot doesn\'t have permission to send message in channel {channel.mention}')
            return
        except exceptions.SubredditNotFound:
            await ia.edit_original_response(f':x: Subreddit `r/{subreddit}` is not found')
            return
        except exceptions.SubredditIsPrivate:
            await ia.edit_original_response(f':x: Subreddit `r/{subreddit}` is private')
            return
        except exceptions.SubredditIsNSFW:
            await ia.edit_original_response(f':x: Subreddit `r/{subreddit}` is NSFW, which the channel {channel.mention} is not NSFW marked')
            return
        except exceptions.FeedExists:
            await ia.edit_original_response(f':x: Already exists feed of `r/{subreddit}` in this server')
            return
        else:
            await self.bot.database.execute(
                'INSERT INTO feeds (guild_id, channel_id, subreddit) VALUES (:guild_id, :channel_id, :subreddit)',
                {'guild_id': channel.guild.id, 'channel_id': channel.id, 'subreddit': result}
            )
            await ia.edit_original_response(f':white_check_mark: Successful subscribed feed `r/{result}` to {channel.mention}')

    @commands.slash_command(
        name='unsubscribe',
        description='Unsubscribes subreddit feed from selected channel',
        dm_permission=False,
        default_member_permissions=disnake.Permissions(manage_channels=True),
        options=[
            Option(
                name='subreddit',
                description='The Subreddit name to unsubscribe the feed',
                type=OptionType.string,
                required=True
            ),
            Option(
                name='channel',
                description='The channel to stop Subreddit feed subscription',
                type=OptionType.channel,
                required=False,
                channel_types=[
                    ChannelType.text,
                    ChannelType.voice,
                    ChannelType.news,
                    ChannelType.stage_voice,
                    ChannelType.public_thread,
                    ChannelType.private_thread,
                    ChannelType.news_thread
                ]
            )
        ]
    )
    async def scmd_unsubscribe(self, ia: disnake.AppCmdInter, subreddit: str, channel: disnake.TextChannel = None):
        if not channel:
            channel = ia.channel

        await ia.response.defer()

        result = self.feeder.feed_stop(subreddit, ia.guild.id, channel.id)
        if result:
            await self.bot.database.execute(
                'DELETE FROM feeds WHERE channel_id = :channel_id AND subreddit = :subreddit',
                {'channel_id': channel.id, 'subreddit': result}
            )
            await ia.edit_original_response(f':white_check_mark: Successful unsubscribed feed `r/{result}` from {channel.mention}')
        else:
            await ia.edit_original_response(f':x: There are no feed from `r/{subreddit}` in {channel.mention} or incorrect Subreddit/channel')

    @commands.slash_command(
        name='list',
        description='Shows an embed with current feeds on this server',
        dm_permission=False
    )
    async def scmd_list(self, ia: disnake.AppCmdInter):
        try:
            guild_tasks = self.feeder.feeders[ia.guild.id]
        except KeyError:
            await ia.response.send_message(':x: There are no feeds on this server')
            return
        else:
            if len(guild_tasks) == 0:
                await ia.response.send_message(':x: There are no feeds in this server')
                return

            embed = disnake.Embed(
                title='Server Subreddits Subscriptions',
                colour=disnake.Colour.blurple(),
                description='There\'s server subreddits subscriptions channels:'
            )

            for task in guild_tasks:
                embed.add_field(
                    name=f'Feed `r/{task.subreddit}`',
                    value=f'in <#{task.channel}>',
                    inline=False
                )

            await ia.response.send_message(embed=embed)


def setup(bot: DisredditBot) -> None:
    bot.add_cog(CogFeed(bot))
