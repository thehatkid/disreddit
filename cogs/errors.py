import logging
import sys
import traceback
import disnake
from disnake.ext import commands

from bot import DisredditBot


class CogErrors(commands.Cog):
    def __init__(self, bot: DisredditBot):
        self.bot = bot
        self.log = logging.getLogger(__name__)

    def cog_load(self):
        self.log.info('Cog load')

    def cog_unload(self):
        self.log.info('Cog unload')

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if not ctx.command:
            return

        if hasattr(ctx.command, 'on_error'):
            return

        if isinstance(error, commands.errors.CommandNotFound):
            pass
        elif isinstance(error, commands.errors.DisabledCommand):
            pass
        elif isinstance(error, commands.errors.NoPrivateMessage):
            await ctx.reply(':x: This command is only available in servers')
        elif isinstance(error, commands.errors.CommandOnCooldown):
            await ctx.reply(f':x: This command is on cooldown for *{error.retry_after:.2f}* seconds')
        elif isinstance(error, commands.errors.CheckFailure):
            await ctx.reply(':x: You don\'t have access to this command')
        elif isinstance(error, commands.errors.MissingRequiredArgument):
            signature = f'{ctx.prefix}{ctx.command.name} {ctx.command.signature}'
            await ctx.reply(f':x: Required parameter is missing: `{error.param}`\nCommand usage: `{signature}`')
        elif isinstance(error, commands.errors.BadArgument):
            await ctx.reply(f':x: Failed to parse command parameters: `{error}`')
        elif isinstance(error, commands.errors.UserNotFound):
            await ctx.reply(':x: That user is not found or invalid')
        elif isinstance(error, commands.errors.CommandInvokeError):
            exc = error.original

            if isinstance(exc, disnake.errors.Forbidden):
                if ctx.guild:
                    self.log.warning(
                        f'Missing permissions ({exc.code}) on text command "{ctx.command.qualified_name}" '
                        f'(invoked by {ctx.author.id} in {ctx.guild.id}:{ctx.channel.id})'
                    )
                else:
                    self.log.warning(
                        f'Missing permissions ({exc.code}) on text command "{ctx.command.qualified_name}" '
                        f'(invoked by {ctx.author.id} in DM channel)'
                    )
                await ctx.reply(':x: Seems I have insufficient permissions for that...')
            else:
                if ctx.guild:
                    self.log.error(
                        f'Raised exception on text command "{ctx.command.name}"! '
                        f'(invoked by {ctx.author.id} in {ctx.guild.id}:{ctx.channel.id})'
                    )
                else:
                    self.log.error(
                        f'Raised exception on text command "{ctx.command.name}"! '
                        f'(invoked by {ctx.author.id} in DM channel)'
                    )
                traceback.print_exception(type(exc), exc, exc.__traceback__, file=sys.stderr)
                await ctx.reply(':x: Something went wrong while running this command... Please contact the bot developer!')

    @commands.Cog.listener()
    async def on_slash_command_error(self, ia: disnake.AppCmdInter, error: commands.CommandError):
        if hasattr(ia.application_command, 'on_error'):
            return

        if isinstance(error, commands.errors.NoPrivateMessage):
            await ia.send(':x: This command is only available in servers')
        elif isinstance(error, commands.errors.CommandOnCooldown):
            await ia.send(f':x: This command is on cooldown for *{error.retry_after:.2f}* seconds', ephemeral=True)
        elif isinstance(error, commands.errors.CheckFailure):
            await ia.send(f':x: You don\'t have access to this command', ephemeral=True)
        elif isinstance(error, commands.errors.UserNotFound):
            await ia.send(':x: That user is not found or invalid', ephemeral=True)
        elif isinstance(error, commands.errors.CommandInvokeError):
            exc = error.original
            if isinstance(exc, disnake.errors.Forbidden):
                if ia.guild:
                    self.log.warning(
                        f'Missing permissions ({exc.code}) on slash command "/{ia.application_command.qualified_name}" '
                        f'(invoked by {ia.author.id} in {ia.guild.id}:{ia.channel.id})'
                    )
                else:
                    self.log.warning(
                        f'Missing permissions ({exc.code}) on slash command "/{ia.application_command.qualified_name}" '
                        f'(invoked by {ia.author.id} in DM channel)'
                    )
                await ia.response.send_message(
                    ':x: Seems I have insufficient permissions for that...',
                    ephemeral=True
                )
            else:
                if ia.guild:
                    self.log.error(
                        f'Raised exception on slash command "/{ia.application_command.qualified_name}"! '
                        f'(invoked by {ia.author.id} in {ia.guild.id}:{ia.channel.id})'
                    )
                else:
                    self.log.error(
                        f'Raised exception on slash command "/{ia.application_command.qualified_name}"! '
                        f'(invoked by {ia.author.id} in DM channel)'
                    )
                traceback.print_exception(type(exc), exc, exc.__traceback__, file=sys.stderr)
                await ia.response.send_message(
                    ':x: Something went wrong while running this command... Please contact the bot developer!',
                    ephemeral=True
                )


def setup(bot: DisredditBot) -> None:
    bot.add_cog(CogErrors(bot))
