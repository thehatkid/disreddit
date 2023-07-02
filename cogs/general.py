import logging
import yaml
from typing import List, Tuple
import datetime
import itertools
import pygit2
from os import getpid
import psutil
import disnake
from disnake import ActivityType
from disnake.ext import commands
from disnake.ext import tasks

from bot import DisredditBot
from bot.utils import sizeof_fmt, uptime_to_str


class CogGeneral(commands.Cog):
    def __init__(self, bot: DisredditBot):
        self.bot = bot
        self.log = logging.getLogger(__name__)

        with open('config.yml', 'r') as fp:
            config = yaml.safe_load(fp)

        self.invite_url = config['bot']['links']['invite']
        self.support_url = config['bot']['links']['support']
        self.repos_url = config['bot']['links']['repos']

        self.presences: List[Tuple[ActivityType, str]] = [
            (ActivityType.competing, 'hat_kid\'s development'),
            (ActivityType.watching, 'for Reddit feeds'),
            (ActivityType.listening, '[TOTAL_FEEDERS] feeds'),
            (ActivityType.playing, 'Reddit'),
            (ActivityType.watching, 'for [GUILDS] servers'),
            (ActivityType.watching, 'for [USERS] users'),
            (ActivityType.competing, 'r/funny'),
            (ActivityType.playing, 'OneShot'),
            (ActivityType.watching, 'for [TOTAL_FEEDERS] feeds in [GUILD_FEEDERS] servers'),
        ]
        self.presence_iter: int = 0

    def cog_load(self):
        self.log.info('Cog load')
        self.task_presence_cycle.start()

    def cog_unload(self):
        self.log.info('Cog unload')
        self.task_presence_cycle.stop()

    def format_commit(self, commit: pygit2.Commit) -> str:
        short, _, _ = commit.message.partition('\n')
        short_sha2 = commit.hex[0:6]
        commit_tz = datetime.timezone(datetime.timedelta(minutes=commit.commit_time_offset))
        commit_time = datetime.datetime.fromtimestamp(commit.commit_time).astimezone(commit_tz)

        # [`hash`](url): summary (timestamp)
        timestamp = f'<t:{int(commit_time.astimezone(datetime.timezone.utc).timestamp())}:R>'
        return f'[`{short_sha2}`]({self.repos_url}/commit/{commit.hex}): {short} ({timestamp})'

    def get_last_commits(self, count: int = 3) -> str:
        repo = pygit2.Repository('.git')
        commits = list(itertools.islice(repo.walk(repo.head.target, pygit2.GIT_SORT_TOPOLOGICAL), count))
        return '\n'.join(self.format_commit(c) for c in commits)

    @commands.slash_command(name='about', description='Tells you information about the bot')
    async def scmd_about(self, ia: disnake.AppCmdInter):
        revision = self.get_last_commits()

        embed = disnake.Embed(
            title=f'Hello, {ia.author}!',
            colour=disnake.Colour.blurple()
        )
        embed.description = f'''
        Hello, thank you for using me! I am {self.bot.user.name}.

        This bot aims to finding new posts from one or more Subreddit feeds to one or more Discord channels, such for text channels, news channels, threads, or even voice and stage channels (Text-in-Voice).

        **Latest Changes:**
        {revision}
        '''
        embed.set_author(name=self.bot.user, icon_url=self.bot.user.avatar)

        view = disnake.ui.View()
        if self.invite_url:
            view.add_item(disnake.ui.Button(label='Invite bot', url=self.invite_url))
        if self.support_url:
            view.add_item(disnake.ui.Button(label='Support server', url=self.support_url))

        await ia.send(embed=embed, view=view)

    @commands.slash_command(name='ping', description='Checks the bot status and shows ping latency')
    async def scmd_ping(self, ia: disnake.AppCmdInter):
        embed = disnake.Embed(
            title=':ping_pong: Bot says Pong!',
            colour=disnake.Colour.blurple()
        )
        embed.add_field(
            name=':signal_strength: Latency',
            value='`{0}ms`'.format(round(self.bot.latency * 1000)),
            inline=False
        )
        await ia.response.send_message(embed=embed)

    @commands.slash_command(name='statistics', description='Checks the bot statistics')
    async def scmd_statistics(self, ia: disnake.AppCmdInter):
        uptime_str = uptime_to_str(self.bot.start_time)
        process = psutil.Process(getpid())
        cpu_percent = psutil.cpu_percent()
        ram = psutil.virtual_memory()
        ram_used = sizeof_fmt(ram.used)
        ram_total = sizeof_fmt(ram.total)
        ram_available = sizeof_fmt(ram.available)
        total_guilds = len(self.bot.guilds)
        total_users = 0
        for guild in self.bot.guilds:
            total_users += guild.member_count
        total_feed_servers = len(self.bot.feeder.feeders)
        total_feeders = 0
        for guild_id in self.bot.feeder.feeders:
            total_feeders += len(self.bot.feeder.feeders[guild_id])

        embed = disnake.Embed(
            title=':information_source: Bot statistics',
            color=disnake.Color.blurple()
        )
        embed.add_field(
            name=':clock1: Bot Uptime',
            value=f'{uptime_str} (<t:{int(self.bot.start_time.timestamp())}:R>)',
            inline=False
        )
        embed.add_field(
            name=':page_facing_up: Process PID',
            value=process.pid,
            inline=True
        )
        embed.add_field(
            name=':control_knobs: System CPU Usage',
            value=f'{cpu_percent}%',
            inline=True
        )
        embed.add_field(
            name=':file_cabinet: Bot RAM Usage',
            value=sizeof_fmt(process.memory_info().rss),
            inline=True
        )
        embed.add_field(
            name=':file_cabinet: System Total RAM',
            value=f'Using: {ram_used} ({ram.percent}%) / {ram_total}\nAvailable: {ram_available} ({ram.available * 100 / ram.total:.1f}%)',
            inline=False
        )
        embed.add_field(
            name=':mailbox: Reddit Feeders',
            value=f'Feeding {total_feeders} subreddits on {total_feed_servers} servers',
            inline=False
        )
        embed.add_field(
            name=':signal_strength: Bot latency',
            value=f'{round(self.bot.latency * 1000)}ms',
            inline=True
        )
        embed.add_field(
            name=':homes: Servers joined',
            value=f'{total_guilds} servers',
            inline=True
        )
        embed.add_field(
            name=':busts_in_silhouette: Total users in servers',
            value=f'{total_users} users',
            inline=True
        )
        await ia.response.send_message(embed=embed)

    @tasks.loop(minutes=1.0)
    async def task_presence_cycle(self):
        await self.bot.wait_until_ready()

        game_type, game_name = self.presences[self.presence_iter]

        total_users = 0
        for guild in self.bot.guilds:
            total_users += guild.member_count
        total_feed_servers = len(self.bot.feeder.feeders)
        total_feeders = 0
        for guild_id in self.bot.feeder.feeders:
            total_feeders += len(self.bot.feeder.feeders[guild_id])

        game_name = game_name.replace('[GUILD_FEEDERS]', str(total_feed_servers))
        game_name = game_name.replace('[TOTAL_FEEDERS]', str(total_feeders))
        game_name = game_name.replace('[GUILDS]', str(len(self.bot.guilds)))
        game_name = game_name.replace('[USERS]', str(total_users))

        await self.bot.change_presence(activity=disnake.Activity(name=game_name, type=game_type))

        self.presence_iter += 1
        if self.presence_iter >= len(self.presences):
            self.presence_iter = 0


def setup(bot: DisredditBot) -> None:
    bot.add_cog(CogGeneral(bot))
