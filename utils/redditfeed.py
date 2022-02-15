import logging
import yaml
from utils import exceptions
import asyncio
import asyncprawcore
import asyncpraw
from asyncpraw import models
import disnake
from disnake.ext import commands


log = logging.getLogger(__name__)
cfg = yaml.safe_load(open('config.yml', 'r'))


def _handle_task_result(task: asyncio.Task) -> None:
    try:
        task.result()
    except asyncio.CancelledError:
        pass  # Task cancellation should not be logged as an error.
    except Exception:  # pylint: disable=broad-except
        logging.exception('Exception raised by task = %r', task)


class RedditFeed():
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.text_limit = 500
        self.feeders: dict[int, list[asyncio.Task]] = {}
        self.reddit = asyncpraw.Reddit(
            client_id=cfg['reddit']['client-id'],
            client_secret=cfg['reddit']['client-secret'],
            password=cfg['reddit']['password'],
            user_agent=cfg['reddit']['user-agent'],
            username=cfg['reddit']['username']
        )

    async def feed_start(self, subreddit_name: str, channel_id: int):
        """
        Starts subreddit feed to server's channel.

        Parameters
        ----------
        subreddit_name: :class:`str`
            The Subreddit name to feeding.
        channel_id: :class:`int`
            The Guild's target Channel ID for posting submissions.
        """
        channel = self.bot.get_channel(channel_id)

        # Checking channel permissions
        bot_user = channel.guild.get_member(self.bot.user.id)
        if channel.permissions_for(bot_user).send_messages is False:
            raise exceptions.CannotSendMessages()

        # If don't have guild task list in dict, putting empty list
        if not channel.guild.id in self.feeders:
            self.feeders[channel.guild.id] = []
        else:
            # Else check for existing tasks
            for task in self.feeders[channel.guild.id]:
                if task.subreddit.lower() == subreddit_name.lower() and task.channel == channel.id:
                    raise exceptions.FeedExists()

        # Searching subreddit by name
        subreddits = self.reddit.subreddits.search_by_name(subreddit_name, exact=True)
        try:
            async for sr in subreddits:
                subreddit = sr
        except asyncprawcore.exceptions.NotFound:
            raise exceptions.SubredditNotFound(subreddit_name)

        # Checking for subreddit access
        try:
            await subreddit.load()
        except asyncprawcore.exceptions.Forbidden:
            raise exceptions.SubredditIsPrivate(subreddit_name)
        except asyncprawcore.exceptions.NotFound:
            raise exceptions.SubredditNotFound(subreddit_name)

        # If subreddit is NSFW but channel not NSFW marked
        if subreddit.over18 and not channel.is_nsfw():
            raise exceptions.SubredditIsNSFW(subreddit_name)

        # Creating task for feeding
        task = self.bot.loop.create_task(
            self.subreddit_feeder(subreddit, channel),
            name=f'RedditFeed_{channel.id}_{subreddit.display_name}'
        )
        task.subreddit = subreddit.display_name
        task.channel = channel.id
        task.add_done_callback(_handle_task_result)

        # Appending task to guild task list in dict
        self.feeders[channel.guild.id].append(task)

        return subreddit.display_name

    def feed_stop(self, subreddit_name: str, guild_id: int, channel_id: int) -> bool:
        """
        Stops subreddit feeding for server's channel.

        Parameters
        ----------
        subreddit_name: :class:`str`
            The Subreddit name to stop feeding.
        guild_id: :class:`int`
            The Guild ID with working feed task(s).
        channel_id: :class:`int`
            The Guild's target Channel ID for stopping posting submissions.
        """
        # Finding task from guild task list and cancel the task and remove from list
        for task in self.feeders[guild_id]:
            task_subreddit = task.subreddit.lower()
            task_channel = task.channel
            if task_subreddit == subreddit_name.lower() and task_channel == channel_id:
                task.cancel('Stopped feeding')
                self.feeders[guild_id].remove(task)
                return task.subreddit
            continue
        return False

    def feed_stop_all(self) -> None:
        """Stops every subreddit feeding."""
        for guild_id in self.feeders:
            for task in self.feeders[guild_id]:
                task.cancel('Stopped feeding')
                self.feeders[guild_id].remove(task)

    async def subreddit_feeder(self, subreddit: models.Subreddit, channel: disnake.TextChannel):
        while True:
            try:
                async for sm in subreddit.stream.submissions(skip_existing=True):
                    content = f'*Submission on `r/{sm.subreddit}` by `u/{sm.author}`*'

                    if sm.spoiler:
                        content += ' **[Spoiler]**'

                    if sm.over_18:
                        if channel.is_nsfw():
                            content += ' **[NSFW]**'
                        else:
                            # Ignoring submission which channel is not NSFW marked
                            continue

                    content += f'\n**{sm.title}**'

                    view = disnake.ui.View()
                    view.add_item(disnake.ui.Button(label='View Submission', url=f'https://reddit.com{sm.permalink}'))

                    if sm.selftext:
                        selftext = sm.selftext.replace('&#x200B;', '')
                        selftext = selftext.replace('>!', '||').replace('!<', '||')
                        selftext = selftext.replace('<', '\\<').replace('>', '\\>')

                        # message text limit
                        if len(selftext) >= self.text_limit:
                            selftext = f'{selftext[:self.text_limit]} *[...]*'

                        if sm.spoiler:
                            selftext = selftext.replace('||', '')
                            content += f'\n\n||{selftext}||'
                        else:
                            content += f'\n\n{selftext}'

                    if sm.url.endswith(('.jpg', '.png', '.gif')):
                        embed = disnake.Embed(colour=0xff5700, type='image')
                        embed.set_image(url=sm.url)
                        try:
                            await channel.send(content=content, view=view, embeds=[embed])
                        except Exception as e:
                            log.error(f'Message was not sent: {e}')
                    elif hasattr(sm, 'secure_media') and sm.secure_media:
                        if 'reddit_video' in sm.secure_media:
                            content += '\n*[Video Attachment]*'
                        elif 'oembed' in sm.secure_media:
                            content += '\n*[Embed Attachment]*'
                        await channel.send(content=content, view=view)
                    elif hasattr(sm, 'media_metadata'):
                        embeds = []
                        for media in sm.media_metadata:
                            # if had reached embeds limit
                            if len(embeds) >= 3:
                                break

                            # if media is not valid, skipping it
                            if sm.media_metadata[media]['status'] != 'valid':
                                continue

                            # if media is image...
                            if sm.media_metadata[media]['e'] == 'Image':
                                embed = disnake.Embed(colour=0xff5700, type='image')
                                embed.set_image(url=sm.media_metadata[media]['s']['u'])
                                embeds.append(embed)

                            # if media is gif/video...
                            elif sm.media_metadata[media]['e'] == 'AnimatedImage':
                                embed = disnake.Embed(colour=0xff5700, type='image')
                                embed.set_image(url=sm.media_metadata[media]['s']['gif'])
                                embeds.append(embed)

                        await channel.send(content=content, embeds=embeds, view=view)
                    else:
                        await channel.send(content=content, view=view)
            except Exception as e:
                log.error(f'Raised exception: {e}')
                continue
