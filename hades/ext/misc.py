from __future__ import annotations
from typing import (
    Dict,
    List,
    Any,
    Union,
    Coroutine
)

from discord import (
    User,
    Member,
    TextChannel,
    DMChannel,
    Message,
    Forbidden
)
from discord.ext.commands import group, command, Cog
from discord.errors import CaptchaRequired
import discord

from ..managers.context import HadesContext, Flags, FlagsEmojiMapping
from ..managers.embed import Embed
from ..constants import PACKS
from ..hades import Hades

from xxhash import xxh32_hexdigest
import asyncio
import random

class FastRoutine:
    """
    A simple class for fast gathering, and execution of coroutines.
    """

    func: Coroutine[Any, Any, Any]
    repetitions: int

    def __init__(self, func: Coroutine[Any, Any, Any], repetitions: int = 24) -> None:
        self.func: Coroutine[Any, Any, Any] = func
        self.repetitions: int = repetitions

    async def gather_coroutines(self) -> None:
        tasks: List[asyncio.Task[Any]] = [
            asyncio.create_task(self.func()) for _ in range(self.repetitions)
        ]
        await asyncio.gather(*tasks)

class Miscellaneous(Cog):
    def __init__(self, bot: Hades) -> None:
        self.bot: Hades = bot

        self.packing: bool = False

    @Cog.listener("on_message")
    async def check_insult(self, origin: Message) -> None:
        if await self.bot.cache.get(
            f"insult:{xxh32_hexdigest(str(origin.author.id))}"
        ):
            await origin.reply(
                "# " + random.choice(PACKS)
            )

    @Cog.listener("on_message")
    async def check_outlast(self, origin: Message) -> None:
        key = f"outlast:{xxh32_hexdigest(str(origin.author.id))}"

        if await self.bot.cache.get(key):
            count = await self.bot.cache.get(f"{key}:count") or 0
            count += 1

            await self.bot.cache.set(f"{key}:count", count)
            await origin.reply(f"you're ass at outlasting {count}")

    @command(
        name="type",
        description="Send each word in a sentence sequentially.",
        usage="(sentence)"
    )
    async def type(self, ctx: HadesContext, *, sentence: str) -> None:
        await ctx.message.delete()

        words: List[str] = sentence.split()
        channel: DMChannel | TextChannel = ctx.channel

        for word in words:
            await channel.send(word)

    @command(
        name="massdm",
        description="Send a message to all your friends!",
        example="hi! 5",
        usage="(message) [timeout]"
    )
    async def massdm(
        self,
        ctx: HadesContext,
        message: str,
        *,
        timeout: int = 3
    ) -> Message:
        await ctx.message.delete()

        total: int = len(self.bot.friends)
        new: int = 0

        while new <= total:
            for friend in self.bot.friends:
                if new >= total:
                    return await ctx.do(
                        _type=Flags.APPROVE,
                        content=f"Successfully finished the mass DM to `{total}` users!",
                        embed=self.bot.embed
                    )
                    break

                try:
                    dm = getattr(friend.user, "dm_channel", None) or await friend.user.create_dm()
                    await dm.send(
                        f"{friend.user.mention}\n\n"
                        f"{message}"
                    )
                    new += 1
                except (CaptchaRequired, Forbidden):
                    self.bot.logger.error(f"Failed to send a DM to {friend.user}! (`Captcha Required / Forbidden!`)")

                await asyncio.sleep(timeout)

    @group(
        name="insult",
        description="Insult a user until stopped.",
        invoke_without_command=True
    )
    async def insult(self, ctx: HadesContext) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.do(
                _type=Flags.WARN,
                content=f"Invalid insult command passed... - `{ctx.prefix}insult begin/end`",
                embed=self.bot.embed
            )

    @insult.command(
        name="begin",
        description="Begin the insulting on a user.",
        usage="(user)",
        example="ryu"
    )
    async def begin(
        self,
        ctx: HadesContext,
        *,
        user: Union[Member, User]
    ) -> Message:
        await ctx.message.delete()

        if await self.bot.cache.get(
            f"insult:{xxh32_hexdigest(str(user.id))}"
        ):
            return await ctx.do(
                _type=Flags.WARN,
                emoji="❌",
                content="This user is already being insulted!"
            )

        await self.bot.cache.sadd(
            f"insult:{xxh32_hexdigest(str(user.id))}",
            True
        )

        return await ctx.do(
            _type=Flags.APPROVE,
            emoji="✅",
            content=f"Starting auto-insulter on **{user.name}**"
        )

    @insult.command(
        name="end",
        description="Stop the auto-insulting."
    )
    async def end(
        self,
        ctx: HadesContext,
        user: Union[User, Member]
    ) -> None:
        if await self.bot.cache.get(
            f"insult:{xxh32_hexdigest(str(user.id))}"
        ):
            await self.bot.cache.remove(
                f"insult:{xxh32_hexdigest(str(user.id))}"
            )

            await ctx.message.add_reaction("👍")

    @group(
        name="outlast",
        description="Outlast a user until stopped.",
        invoke_without_command=True
    )
    async def outlast(self, ctx: HadesContext) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.do(
                _type=Flags.WARN,
                content=f"Invalid outlast command passed... - `{ctx.prefix}outlast begin/end`",
                embed=self.bot.embed
            )

    @outlast.command(
        name="begin",
        description="Begin the outlasting on a user.",
        usage="(user)",
        example="ryu"
    )
    async def begin_outlast(
        self,
        ctx: HadesContext,
        *,
        user: Union[Member, User]
    ) -> Message:
        await ctx.message.delete()

        key = f"outlast:{xxh32_hexdigest(str(user.id))}"

        if await self.bot.cache.get(key):
            return await ctx.do(
                _type=Flags.WARN,
                emoji="❌",
                content="This user is already being outlasted!"
            )

        await self.bot.cache.sadd(key, True)
        await self.bot.cache.set(f"{key}:count", 0)

        return await ctx.do(
            _type=Flags.APPROVE,
            emoji="✅",
            content=f"Starting auto-outlasting on **{user.name}**"
        )

    @outlast.command(
        name="end",
        description="Stop the auto-outlasting."
    )
    async def end_outlast(
        self,
        ctx: HadesContext,
        user: Union[User, Member]
    ) -> None:
        key = f"outlast:{xxh32_hexdigest(str(user.id))}"

        if await self.bot.cache.get(key):
            await self.bot.cache.remove(key)
            await self.bot.cache.remove(f"{key}:count")

            await ctx.message.add_reaction("👍")

    @group(
        name="pack",
        description="Commands related to packing."
    )
    async def pack(self, ctx: HadesContext) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.do(
                _type=Flags.WARN,
                content=f"Invalid pack command passed... - `{ctx.prefix}pack start/end`",
                embed=self.bot.embed,
            )

    @pack.command(
        name="start",
        description="Start sending words from a random pack one by one in the current channel."
    )
    async def start(self, ctx: HadesContext) -> None:
        await ctx.message.delete()

        channel: Union[
            discord.DMChannel,
            discord.TextChannel,
            discord.abc.MessageableChannel
        ] = ctx.channel

        if self.packing:
            return

        self.packing: bool = True

        while self.packing:
            pack = random.choice(PACKS)
            words = pack.split()

            if not self.packing:
                break

            while len(words) >= 4:
                chunk, words = words[:4], words[4:]

                await channel.send("# " + " ".join(chunk).lower())
                await asyncio.sleep(0.9)

            if words:
                await channel.send("# " + " ".join(words).lower())

            if self.packing:
                await asyncio.sleep(1)

    @pack.command(
        name="stop",
        description="Stop the packing process.",
    )
    async def stop(self, ctx: HadesContext) -> None:
        await ctx.message.delete()

        if not self.packing:
            return

        self.packing: bool = False

    @command(
        name="afkvc",
        description="Join a voice channel and stay AFK.",
        usage="(channel)"
    )
    async def afkvc(
        self,
        ctx: HadesContext,
        channel: discord.VoiceChannel
    ) -> None:
        await ctx.message.delete()

        async def join_vc():
            try:
                if ctx.voice_client is not None:
                    await ctx.voice_client.disconnect()

                await channel.connect(self_deaf=True, self_mute=True)
                await ctx.send(f"Joined {channel.mention} and staying AFK.", delete_after=3)
            except (discord.ClientException, Forbidden) as e:
                await ctx.send(f"Failed to join the voice channel: {e}", delete_after=3)

        await join_vc()

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
        user = user or ctx.author
        avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
        
        return await ctx.send(
            f"{user.mention}'s avatar: {avatar_url}"
        )

async def setup(bot: Hades) -> None:
    await bot.add_cog(Miscellaneous(bot))
