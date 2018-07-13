import discord
from discord.ext import commands
import aiohttp


class AntiDupe:
    """Prevents users from spamming the same message over and over"""

    def __init__(self, bot):
        self.bot = bot
        self.errorMsg = "I don't have permission to deduplicate that message!"

    async def dedupe(self, message):
        lastmsg = None
        async for m in self.bot.logs_from(message.channel, 1, before=message):
            lastmsg = m

        # Don't do anything if there are attachments
        if not message.clean_content or \
           not lastmsg.clean_content:
            # Debugging
            print("attachments: \n" + message.attachments +
                  "\n" + lastmsg.attachments)
            return

        if lastmsg is not None and \
           lastmsg.author.display_name == message.author.display_name and \
           lastmsg.clean_content == message.clean_content:
            try:
                await self.bot.delete_message(message)
            except discord.Forbidden:
                await self.bot.say(self.errorMsg)
            except Exception as e:
                return


def setup(bot):
    n = AntiDupe(bot)
    bot.add_listener(n.dedupe, "on_message")
    bot.add_cog(n)