import discord
from discord.ext import commands

import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DS_TOKEN")

class BarmanTaberna(commands.Bot):

    """
        Clase que maneja todas las acciones que realiza el bot.
    """

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        """
            Setup para agregar todos los cogs al bot de discord.
        """
        await self.load_extension("discord_bot.cogs.moderation")

    async def on_ready(self) -> None:
        """
            on_ready func que se muestra en la doc, es para mostrar que el
            bot ya esta preparado para funcionar.
        """
        print(f"{self.user} esta listo.")

if __name__ == "__main__":

    bot = BarmanTaberna()
    bot.run(TOKEN)