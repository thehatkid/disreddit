import logging
import yaml
from databases import Database
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

# Prepare Gateway Intents
intents = disnake.Intents.none()
intents.guilds = True
intents.guild_messages = True

# Initialize Bot Class
bot = commands.Bot(
    command_prefix=cfg['bot']['prefix'],
    help_command=None,
    intents=intents
)

# Connect SQLite Database
bot.db = Database('sqlite:///{0}'.format(cfg['bot']['sqlite-path']))

# After bot ready actions
async def after_bot_ready():
    await bot.wait_until_ready()
    # Connect Database
    await bot.db.connect()
    # Creating table if not exists
    await bot.db.execute('''
    CREATE TABLE IF NOT EXISTS "feeds" (
        "guild_id" INTEGER NOT NULL,
        "channel_id" INTEGER NOT NULL,
        "subreddit" TEXT NOT NULL
    )
    ''')

bot.loop.create_task(after_bot_ready())

# Loading Cogs
bot.load_extension('cogs.events')
bot.load_extension('cogs.commands')

# Running Bot from Bot Token
bot.run(token=cfg['bot']['token'])
