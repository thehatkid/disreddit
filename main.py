import logging
import yaml
import colorama

from bot import DisredditBot
from bot.utils import LogFormatter

# Fix ANSI colors output in Windows terminals
colorama.just_fix_windows_console()

# Setup logging
log_handler = logging.StreamHandler()
log_handler.setFormatter(LogFormatter('%(asctime)s | %(levelname)-8s | %(name)-20s: %(message)s'))
logging.basicConfig(level=logging.INFO, handlers=[log_handler])

if __name__ == '__main__':
    # Load YAML config
    with open('config.yml', 'r') as fp:
        config = yaml.safe_load(fp)

    bot = DisredditBot(database_path=config['bot']['sqlite-path'])

    # Start database connection task
    bot.loop.create_task(bot.database_connect())

    # Load cogs
    bot.load_extensions('cogs')

    # Run the bot
    bot.run(token=config['bot']['token'])
