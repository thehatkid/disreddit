import logging
import utils
import asyncio
from databases import Database
import disnake
from disnake.ext import commands


log = logging.getLogger(__name__)


class CogCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: Database = bot.db
        self.feeder = utils.redditfeed.RedditFeed(bot)

    def cog_load(self):
        async def run_feeders(db: Database, feeder: utils.redditfeed.RedditFeed):
            while True:
                if not db.is_connected:
                    await asyncio.sleep(0.5)
                else:
                    break
            feeds = await db.fetch_all('SELECT channel_id, subreddit FROM feeds')
            for feed in feeds:
                log.info(f'Trying to start feed "{feed[1]}" for channel {feed[0]}...')
                try:
                    await feeder.feed_start(feed[1], feed[0])
                except Exception as e:
                    log.error(f'Failed to start feed "{feed[1]}" for channel {feed[0]}: {e}')
                else:
                    log.info(f'Started feed "{feed[1]}" for channel {feed[0]}')
        self.bot.loop.create_task(run_feeders(self.db, self.feeder))

    def cog_unload(self):
        self.feeder.feed_stop_all()

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

    @commands.command(name='subscribe', description='Subscribes subreddit feed to selected server channel', aliases=['sub', 'follow', 'add'])
    async def cmd_subscribe(self, ctx: commands.Context, subreddit_name: str = '', channel: disnake.TextChannel = None):
        if not subreddit_name:
            return await ctx.send(':x: Please, provide Subreddit name to subscribe feed.')
        if not channel:
            channel = ctx.channel
        if not channel.permissions_for(ctx.author).manage_channels:
            return await ctx.send(':x: You don\'t have `Manage Channels` permission to subscribing feed.')

        try:
            guild_tasks = self.feeder.feeders[ctx.guild.id]
        except KeyError:
            # Skip if don't have guild task list in dict
            pass
        else:
            if len(guild_tasks) >= 5:
                return await ctx.send(f':x: Reached limit of feeds (max: 5) in this server.')
            for task in guild_tasks:
                if task.subreddit.lower() == subreddit_name.lower() and task.channel == channel.id:
                    return await ctx.send(f':x: Already exists feed of `r/{task.subreddit}` in {channel.mention}')

        reply = await ctx.send(':hourglass: Processing...')

        try:
            result = await self.feeder.feed_start(subreddit_name, channel.id)
        except utils.exceptions.CannotSendMessages:
            return await reply.edit(content=':x: Bot don\'t have permission to send message in channel {}'.format(channel.mention))
        except utils.exceptions.SubredditNotFound:
            return await reply.edit(content=':x: Subreddit `{}` is not found'.format(subreddit_name))
        except utils.exceptions.SubredditIsPrivate:
            return await reply.edit(content=':x: Subreddit `{}` is private'.format(subreddit_name))
        except utils.exceptions.SubredditIsNSFW:
            return await reply.edit(content=':x: Subreddit `{0}` is NSFW which channel {1} is not NSFW marked.'.format(subreddit_name, channel.mention))
        except utils.exceptions.FeedExists:
            return await reply.edit(content=':x: Already exists feed of `r/{0}` in {1}'.format(subreddit_name, channel.mention))
        else:
            await self.db.execute(
                'INSERT INTO feeds (guild_id, channel_id, subreddit) VALUES (:guild_id, :channel_id, :subreddit)',
                {'guild_id': channel.guild.id, 'channel_id': channel.id, 'subreddit': result}
            )
            await reply.edit(content=f'Successful subscribed feed `r/{result}` to {channel.mention}')

    @commands.command(name='unsubscribe', description='Unsubscribes subreddit feed from selected server channel', aliases=['unsub', 'unfollow', 'remove'])
    async def cmd_unsubscribe(self, ctx: commands.Context, subreddit_name: str = '', channel: disnake.TextChannel = None):
        if not subreddit_name:
            return await ctx.send(':x: Please, provide Subreddit name to unsubscribe feed.')
        if not channel:
            channel = ctx.channel
        if not channel.permissions_for(ctx.author).manage_channels:
            return await ctx.send(':x: You don\'t have `Manage Channels` permssion to unsubscribing feed.')

        result = self.feeder.feed_stop(subreddit_name, ctx.guild.id, channel.id)
        if result:
            await self.db.execute(
                'DELETE FROM feeds WHERE channel_id = :channel_id AND subreddit = :subreddit',
                {'channel_id': channel.id, 'subreddit': result}
            )
            await ctx.send(f'Successful unsubscribed feed `r/{result}` from {channel.mention}')
        else:
            await ctx.send(f':x: There\'s are no feed from `{subreddit_name}` in {channel.mention} or incorrect subreddit/channel.')

    @commands.command(name='sublist', description='Shows embed with current feeds in server', aliases=['list', 'subs', 'followings'])
    async def cmd_sublist(self, ctx: commands.Context):
        try:
            guild_tasks = self.feeder.feeders[ctx.guild.id]
        except KeyError:
            return await ctx.send(':x: There\'s are no feeds in this server.')
        else:
            if len(guild_tasks) < 1:
                return await ctx.send(':x: There\'s are no feeds in this server.')

            embed = disnake.Embed(
                title='Server Subreddits Subscriptions',
                colour=disnake.Colour.blurple(),
                description='There\'s server\'s subreddits subscriptions channels:'
            )
            embed.set_footer(
                text=f'Requested by {ctx.author.name}#{ctx.author.discriminator}',
                icon_url=ctx.author.display_avatar
            )
            for task in guild_tasks:
                embed.add_field(
                    name=f'Feed `r/{task.subreddit}`',
                    value=f'in <#{task.channel}>',
                    inline=False
                )
            await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(CogCommands(bot))
    log.info('Loaded cog')


def teardown(bot: commands.Bot) -> None:
    log.info('Unloaded cog')
