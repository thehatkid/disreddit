import logging
import yaml
import disnake
from disnake.ext import commands

# Setting up Logging
logging.basicConfig(
    format='[%(asctime)s][%(levelname)s][%(name)s]: %(message)s',
    level=logging.INFO
)
log = logging.getLogger('bot')

# Loading configurations
cfg = yaml.safe_load(open('config.yml', 'r'))

log.info('Starting disnake {0} {1}...'.format(
    disnake.__version__, disnake.version_info.releaselevel
))

# Initialize Bot Class
intents = disnake.Intents.none()
intents.guilds = True
intents.guild_messages = True
bot = commands.Bot(
    command_prefix=cfg['bot']['prefix'],
    help_command=None,
    intents=intents
)

# Loading Cogs
bot.load_extension('cogs.events')
bot.load_extension('cogs.commands')

# Running Bot from Bot Token
bot.run(token=cfg['bot']['token'])
