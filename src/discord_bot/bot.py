import discord
from discord.ext import commands
from discord import app_commands

import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DS_TOKEN")

class BarmanTaberna(commands.Bot):

    """
        Clase que maneja todas las acciones que realiza el bot.
    """

    def __init__(self) -> None:

        super().__init__(command_prefix="!", intents=discord.Intents.default())

    async def setup_hook(self) -> None:
        await self.tree.sync()