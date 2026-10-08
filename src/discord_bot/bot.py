import discord
from discord.ext import commands

import logging
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DS_TOKEN")

logger = logging.getLogger(__name__)

class BarmanTaberna(commands.Bot):

    """
        Clase que maneja todas las acciones que realiza el bot.
    """

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        """
            Setup para agregar todos los cogs al bot de discord.
        """
        try:
            await self.load_extension("discord_bot.cogs.moderation")
            await self.load_extension("discord_bot.cogs.members")
            await self.load_extension("discord_bot.cogs.music")

            for command in self.tree.get_commands():
                print(f"Comando registrado: /{command.name}")

            synced = await self.tree.sync()
            print(f"Comandos sincronizados: {[cmd.name for cmd in synced]}")

        except (commands.ExtensionNotFound):
            logger.error("Extension no encontrada, fijate que este bien la carpeta cogs.")
        except (commands.NoEntryPointError):
            logger.error("Extension no cargada, debido seguramente a que no lo configuraste antes.")
        except (commands.ExtensionError) as error:
            logger.error("Ocurrio un error.\nError = %s", error)

    async def on_ready(self) -> None:
        """
            on_ready func que se muestra en la doc, es para mostrar que el
            bot ya esta preparado para funcionar.
        """
        print(f"{self.user} esta listo.")

if __name__ == "__main__":

    bot = BarmanTaberna()
    if TOKEN is None: raise ValueError("No se encontro el token de discord. Saliendo...")

    bot.run(TOKEN)