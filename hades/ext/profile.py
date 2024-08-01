from __future__ import annotations
from typing import Dict, List, Any

from discord import (
    User,
    Member,
    DMChannel,
    Message,
    HypeSquadHouse,
    Gift
)
from discord.ext.commands import group, command, Cog

from ..constants import HYPESQUAD, NITRO_REGEX, PRIVNOTE_REGEX
from ..managers.context import HadesContext, Flags
from ..managers.embed import Embed
from ..util import read_note
from ..hades import Hades

import requests
import asyncio
import re

class Profile(Cog):
    def __init__(self, bot: Hades) -> None:
        self.bot: Hades = bot
        self.used_notes: List[str] = []
        self.used_codes: List[str] = []

    def redeem(self: Profile, code: str) -> bool:
        response = requests.post(
            f"https://discord.com/api/entitlements/gift-codes/{code}/redeem",
            headers={
                "authorization": self.bot._token
            }
        )
        return True if response.ok else False

    def can_nitro(self: Profile, message: Message) -> bool:
        sniper = self.bot.config["snipers"].get("nitro", False)
        return (
            sniper
            and (match := NITRO_REGEX.search(message.content))
            and match.group(2) not in self.used_codes
        )

    def can_privnote(self: Profile, message: Message) -> bool:
        sniper = self.bot.config["snipers"].get("privnote", False)
        return (
            sniper
            and (match := PRIVNOTE_REGEX.search(message.content))
            and match.group(0) not in self.used_notes
        )

    @Cog.listener()
    async def snipe_privnote(self: Profile, message: Message) -> None:
        if self.can_privnote(message):
            if match := PRIVNOTE_REGEX.search(message.content):
                url = match.group(0)
                try:
                    note = read_note(url)
                    self.bot.logger.info(f"Privnote successfully sniped! » {note}")
                    self.used_notes.append(url)
                except Exception as e:
                    self.bot.logger.error(f"Failed to snipe Privnote! » {url}")

    @Cog.listener()
    async def snipe_nitro(self: Profile, message: Message) -> None:
        if self.can_nitro(message):
            if match := NITRO_REGEX.search(message.content):
                code = match.group(2)
                try:
                    self.redeem(code)
                    self.bot.logger.info(f"Successfully sniped nitro code! » {code}")
                    self.used_codes.append(code)
                except Exception as e:
                    self.bot.logger.error(f"Failed to snipe nitro code! » {code}")

    @command(
        name="privnotesniper",
        description="Toggle the Privnote sniper on or off.",
        usage="(on/off)",
        example="on"
    )
    async def privnotesniper(
        self: Profile,
        ctx: HadesContext,
        option: str
    ) -> Message:
        await ctx.message.delete()
        option = option.lower()

        if option not in ["on", "off"]:
            return await ctx.do(
                _type=Flags.ERROR,
                emoji="❌",
                content="Invalid option! Please use `on` or `off`.",
                embed=self.bot.embed
            )

        sniper = option == "on"
        self.bot.config["settings"]["privnote"] = sniper
        
        return await ctx.do(
            _type=Flags.APPROVE,
            emoji="✅",
            content=f"Privnote sniper has been turned {'on' if sniper else 'off'}.",
            embed=self.bot.embed
        )
        
    @command(
        name="nitrosniper",
        description="Toggle the Nitro sniper on or off.",
        usage="(on/off)",
        example="on"
    )
    async def nitrosniper(
        self: Profile,
        ctx: HadesContext,
        option: str
    ) -> Message:
        await ctx.message.delete()
        option = option.lower()
        
        if option not in ["on", "off"]:
            return await ctx.do(
                _type=Flags.ERROR,
                emoji="❌",
                content="Invalid option! Please use `on` or `off`.",
                embed=self.bot.embed
            )

        sniper = option == "on"
        self.bot.config["settings"]["nitro"] = sniper
        
        return await ctx.do(
            _type=Flags.APPROVE,
            emoji="✅",
            content=f"Nitro sniper has been turned {'on' if sniper else 'off'}.",
            embed=self.bot.embed
        )

    @command(
        name="hypesquad",
        description="Change your profile's hypesquad team!",
        example="brilliance",
        usage="(team)"
    )
    async def hypesquad(
        self: Profile, 
        ctx: HadesContext, 
        *, 
        team: str
    ) -> Message:
        await ctx.message.delete()
        await self.bot.user.edit(house=HYPESQUAD[team])

        return await ctx.do(
            _type=Flags.NEUTRAL,
            emoji="🏆",
            content=f"Hypesquad team successfully changed to » {team}",
            embed=self.bot.embed
        )
        
    @command(
        name="bio",
        description="Change your profile's bio!",
        example="My new bio.",
        usage="(bio)"
    )
    async def bio(
        self: Profile, 
        ctx: HadesContext, 
        *, 
        bio: str
    ) -> Message:
        await ctx.message.delete()
        await self.bot.user.edit(bio=bio)

        return await ctx.do(
            _type=Flags.NEUTRAL,
            emoji="📖",
            content=f"Bio successfully changed to » {bio}",
            embed=self.bot.embed
        )


async def setup(bot: Hades) -> None:
    await bot.add_cog(Profile(bot))
