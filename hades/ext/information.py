from __future__ import annotations
from typing import (
    Dict,
    List,
    Any,
    Union,
    Optional
)

from discord import (
    User,
    Member,
    TextChannel,
    DMChannel,
    Message,
    Forbidden,
    VoiceChannel,
    VoiceState
)
from discord.ext.commands import group, command, Cog, Command, Group
import discord

from ..managers.context import HadesContext, Flags, FlagsEmojiMapping
from ..managers.embed import Embed
from ..hades import Hades

import asyncio
import random

class Information(Cog):
    def __init__(self, bot: Hades) -> None:
        self.bot: Hades = bot
    
    # @command(
    #     name="help",
    #     description="Show the help command embed.",
    #     usage="(usage)",
    #     example="av",
    #     aliases=[
    #         "h", 
    #         "commands", 
    #         "cmds", 
    #         "cmd"
    #     ],
    # )
    # async def help(
    #     self: Information,
    #     ctx: HadesContext,
    #     *,
    #     command: Optional[str] = None
    # ) -> Message:
    #     if not command:
    #         categories = {
    #             "Moderation": ["Mod"],
    #             "Information": ["Info"],
    #             "Miscellaneous": ["Misc"],
    #         }

    #         text = "-- Categories --\n\n" + "\n".join(
    #             f"-> {category} | {', '.join(aliases)}" for category, aliases in categories.items()
    #         ) + "\n\n-----------------"

    #         return await ctx.send(f"```scala\n{text}\n```")

    #     cog = self.bot.get_cog(command.capitalize())

    #     if cog:
    #         cmds = cog.get_commands()
    #         text = f"-- {cog.qualified_name} Commands --\n\n" + "\n".join(
    #             f"-> {cmd.name} | {cmd.description}" for cmd in cmds
    #         ) + "\n\n-----------------"

    #         return await ctx.send(f"```scala\n{text}\n```")

    #     obj: Union[Command, Group] = self.bot.get_command(command)

    #     if not obj:
    #         return await ctx.do(
    #             _type=Flags.WARN,
    #             content=f"Command `{command}` does not exist!",
    #             embed=self.bot.embed,
    #         )

    #     text = (
    #         f"-- {obj.name} Command --\n\n"
    #         f"Description: {obj.description}\n"
    #         f"Usage: {obj.usage}\n"
    #         f"Example: {obj.example}\n"
    #         f"Aliases: {', '.join(obj.aliases)}\n"
    #         "\n-----------------"
    #     )

    #     return await ctx.send(f"```scala\n{text}\n```")

    @command(
        name="avatar",
        description="Get the avatar of a user.",
        aliases=["pfp", "pic", "av"],
        usage="[user]"
    )
    async def avatar(
        self, 
        ctx: HadesContext, 
        user: Union[Member, User] = None
    ) -> Message:
        await ctx.message.delete()
        
        user = user or ctx.author
        avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
        
        return await ctx.send(
            f"{user.mention}'s avatar: {avatar_url}"
        ) if avatar_url else await ctx.send(f"{user.mention} has no avatar!")

async def setup(bot: Hades) -> None:
    await bot.add_cog(Information(bot))
