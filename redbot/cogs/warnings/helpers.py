from copy import copy
from discord.ext import commands
import asyncio
import inspect
import discord

from redbot.core import RedContext, Config, checks
from redbot.core.i18n import CogI18n

_ = CogI18n("Warnings", __file__)


async def warning_points_add_check(config: Config, ctx: RedContext, user: discord.Member, points: int):
    """Handles any action that needs to be taken or not based on the points"""
    guild = ctx.guild
    guild_settings = config.guild(guild)
    act = {}
    async with guild_settings.actions() as registered_actions:
        for a in registered_actions.keys():
            if points >= registered_actions[a]["point_count"]:
                act = registered_actions[a]
            else:
                break
    if act:  # some action needs to be taken
        await create_and_invoke_context(ctx, act["exceed_command"], user)


async def warning_points_remove_check(config: Config, ctx: RedContext, user: discord.Member, points: int):
    guild = ctx.guild
    guild_settings = config.guild(guild)
    act = {}
    async with guild_settings.actions() as registered_actions:
        for a in registered_actions.keys():
            if points >= registered_actions[a]["point_count"]:
                act = registered_actions[a]
            else:
                break
    if act:  # some action needs to be taken
        await create_and_invoke_context(ctx, act["drop_command"], user)


async def create_and_invoke_context(realctx: RedContext, command_str: str, user: discord.Member):
    m = copy(realctx.message)
    m.content = command_str.format(user=user.mention, prefix=realctx.prefix)
    fctx = await realctx.bot.get_context(m, cls=RedContext)
    try:
        await realctx.bot.invoke(fctx)
    except (commands.CheckFailure, commands.CommandOnCooldown):
        await fctx.reinvoke()


def get_command_from_input(bot, userinput: str):
    com = None
    orig = userinput
    while com is None:
        com = bot.get_command(userinput)
        if com is None:
            userinput = ' '.join(userinput.split(' ')[:-1])
        if len(userinput) == 0:
            break
    if com is None:
        return None, _("I could not find a command from that input!")

    check_str = inspect.getsource(checks.is_owner)
    if any(inspect.getsource(x) in check_str for x in com.checks):
        # command the user specified has the is_owner check
        return None, _("That command requires bot owner. I can't "
                       "allow you to use that for an action")
    return "{prefix}" + orig, None


async def get_command_for_exceeded_points(ctx: RedContext):
    """Gets the command to be executed when the user is at or exceeding
    the points threshold for the action"""
    await ctx.send(
        _("Enter the command to be run when the user exceeds the points for "
          "this action to occur.\nEnter it exactly as you would if you were "
          "actually trying to run the command, except don't put a prefix and "
          "use {user} in place of any user/member arguments\n\n"
          "WARNING: The command entered will be run without regard to checks or cooldowns. "
          "Commands requiring bot owner are not allowed for security reasons.\n\n"
          "Please wait 15 seconds before entering your response.")
    )
    await asyncio.sleep(15)

    await ctx.send(_("You may enter your response now."))

    def same_author_check(m):
        return m.author == ctx.author

    try:
        msg = await ctx.bot.wait_for("message", check=same_author_check, timeout=30)
    except asyncio.TimeoutError:
        await ctx.send(_("Ok then."))
        return None

    command, m = get_command_from_input(ctx.bot, msg.content)
    if command is None:
        await ctx.send(m)
        return None

    return command


async def get_command_for_dropping_points(ctx: RedContext):
    """
    Gets the command to be executed when the user drops below the points
    threshold

    This is intended to be used for reversal of the action that was executed
    when the user exceeded the threshold
    """
    await ctx.send(
        _("Enter the command to be run when the user returns to a value below "
          "the points for this action to occur. Please note that this is "
          "intended to be used for reversal of the action taken when the user "
          "exceeded the action's point value\nEnter it exactly as you would "
          "if you were actually trying to run the command, except don't put a prefix "
          "and use {user} in place of any user/member arguments\n\n"
          "WARNING: The command entered will be run without regard to checks or cooldowns. "
          "Commands requiring bot owner are not allowed for security reasons.\n\n"
          "Please wait 15 seconds before entering your response.")
    )
    await asyncio.sleep(15)

    await ctx.send(_("You may enter your response now."))

    def same_author_check(m):
        return m.author == ctx.author

    try:
        msg = await ctx.bot.wait_for("message", check=same_author_check, timeout=30)
    except asyncio.TimeoutError:
        await ctx.send(_("Ok then."))
        return None

    command, m = get_command_from_input(ctx.bot, msg.content)
    if command is None:
        await ctx.send(m)
        return None

    return command