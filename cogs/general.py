import logging
import yaml
from os import getpid
import psutil
import disnake
from disnake.ext import commands

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

    def cog_load(self):
        self.log.info('Cog load')

    def cog_unload(self):
        self.log.info('Cog unload')

    @commands.slash_command(name='about', description='Tells you information about the bot')
    async def scmd_about(self, ia: disnake.AppCmdInter):
        embed = disnake.Embed(
            title=f'Hello, {ia.author}!',
            colour=disnake.Colour.blurple()
        )
        embed.description = f'''
        Hello, thank you for using me! I am {self.bot.user.name}.

        This bot aims to finding new posts from one or more Subreddit feeds to one or more Discord channels,
        such for text channels, news channels, threads, or even voice and stage channels (Text-in-Voice).
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


def setup(bot: DisredditBot) -> None:
    bot.add_cog(CogGeneral(bot))
