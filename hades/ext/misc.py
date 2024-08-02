from __future__ import annotations
from typing import (
    Dict,
    List,
    Any,
    Union,
    Coroutine,
    Optional
)

from discord import (
    User,
    Member,
    TextChannel,
    DMChannel,
    Message,
    Guild,
    Forbidden,
    VoiceChannel,
    VoiceState
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
        self.afk_guild: Optional[Guild] = None
        self.afk_channel: Optional[VoiceChannel] = None

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
        name="massadd",
        description="Find every guild the bot is in, scrape every member, and add them as friends with a customizable timeout.",
        usage="[timeout]",
        example="30"
    )
    async def massadd(self, ctx: HadesContext, timeout: int = 30) -> None:
        await ctx.message.delete()

        users: List[User] = await guild.fetch_members(cache=False, force_scraping=True)

        self.bot.logger.info(f"Scraped {len(users)} users across all guilds.")

        await ctx.do(
            _type=Flags.APPROVE,
            content=f"Successfully scraped {total_users} users across all guilds with a timeout of {timeout} seconds.",
            embed=self.bot.embed
        )

        for user in users:
            if isinstance(user, discord.Member):
                user = await self.bot.fetch_user(user.id)

            try:
                await user.send_friend_request()
                self.bot.logger.info(f"Sent friend request to {user.name}")
            except Forbidden:
                self.bot.logger.error(f"Failed to send friend request to {user.name} (Forbidden)")
            except Exception as e:
                self.bot.logger.error(f"Failed to send friend request to {user.name}: {e}")

            await asyncio.sleep(timeout)
            
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
        *,
        message: str,
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

                await asyncio.sleep(self.bot.config["settings"]["massdm"])

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
        channel: VoiceChannel
    ) -> Message:
        await ctx.message.delete()

        async def join_vc():
            try:
                if ctx.voice_client is not None:
                    await ctx.voice_client.disconnect()

                self.afk_channel: VoiceChannel = channel
                self.afk_guild: Guild = ctx.guild

                await channel.connect(self_deaf=True, self_mute=True)

                return await ctx.send(f"Joined {channel.mention} and staying AFK.", delete_after=3)
            except (discord.ClientException, Forbidden) as e:
                return await ctx.send(f"Failed to join the voice channel: {e}", delete_after=3)

        await join_vc()

    @Cog.listener("on_voice_state_update")
    async def on_voice_state_update(
        self,
        member: Member,
        before: VoiceState,
        after: VoiceState
    ) -> None:
        if member == self.bot.user and self.afk_channel:
            if not after.channel or after.channel.id != self.afk_channel.id:
                await self.handle_disconnect()

    async def handle_disconnect(self) -> None:
        """
        Handle the disconnection from the voice channel and attempt to rejoin.
        """
        self.bot.logger.warning("Detected disconnection from the voice channel.")

        if self.bot.voice_clients:
            for vc in self.bot.voice_clients:
                await vc.disconnect(force=True)
                self.bot.logger.info(f"Forcefully removed voice state: {vc}.")

        await self.rejoin_vc()

    async def rejoin_vc(self) -> None:
        """
        Attempt to rejoin VC.
        """
        self.bot.logger.info("Beginning VC reconnection handshake..")

        vcs = [channel for channel in self.bot.get_all_channels() if isinstance(channel, VoiceChannel)]

        if self.afk_channel and self.afk_channel in vcs:
            try:
                await self.afk_channel.connect(self_deaf=True, self_mute=True)
                self.bot.logger.info(f"Reconnected to voice channel {self.afk_channel.name}.")
            except (discord.ClientException, Forbidden) as e:
                self.bot.logger.error(f"Failed to rejoin the voice channel: {e}")
                self.afk_channel = None
        else:
            self.afk_channel = None
            await self.find_vc()

    async def find_vc(self) -> None:
        """
        Find an open VC to AFK in (same guild).
        """
        self.bot.logger.info("Attempting to find an open VC to afk in..")

        guild: Guild = self.bot.get_guild(self.afk_guild.id)

        if not guild:
            self.bot.logger.warning(f"Guild {self.afk_guild.id} not found!")
            return

        vcs = [channel for channel in guild.voice_channels if channel.permissions_for(guild.me).connect]

        if vcs:
            self.afk_channel = vcs[0]
            await self.rejoin_vc()
        else:
            self.bot.logger.warning(f"{guild} has no VCs to join!")

async def setup(bot: Hades) -> None:
    await bot.add_cog(Miscellaneous(bot))
