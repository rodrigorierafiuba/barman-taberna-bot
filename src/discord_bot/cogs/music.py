import discord
import logging

from yt_dlp.utils import DownloadError
from discord.ext import commands
from discord import app_commands

from typing import cast
from discord_bot.cogs.players.youtube import YTDLSource

logger = logging.getLogger(__name__)


class Music(commands.Cog):
    """
        Clase que va a reproducir musica que pida el usuario
        mientras este conectado a un voice channel.
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
            Atributos del constructor.

            Args:
                bot: Bot del servidor.
        """
        self.bot = bot 

    @app_commands.command(name="join", description="Unirse a un canal de voz.")
    @app_commands.guild_only()
    @app_commands.allowed_installs(guilds=True, users=False)
    async def join(self, interaction: discord.Interaction, *, channel: discord.VoiceChannel) -> None:
        """
            Función para que el bot se una al voice channel.

            Args:
                interaction: Contexto para el comando en ejecución.
                channel: Voice channel donde va a unirse el bot.
        """
        guild: discord.Guild | None = interaction.guild

        if guild is None: return
        await interaction.response.defer(thinking=True)
        voice_client = cast(discord.VoiceClient | None, guild.voice_client)

        if voice_client is not None:
            if voice_client.is_connected() or voice_client.is_playing():
                await interaction.followup.send("Amigo vos te pensas que soy re boludo, si estoy con vos escuchando musica mientras me tomo 8 birras.")
                return

        await interaction.followup.send("Listo! Ya estoy en el voice amigo!")
        await channel.connect()

    @app_commands.command(name="play", description="Pone música en el canal de voz.")
    @app_commands.guild_only()
    @app_commands.allowed_installs(guilds=True, users=False)
    async def play(self, interaction: discord.Interaction, *, cancion: str) -> None:
        """
        Busca y reproduce música utilizando yt-dlp.

        Args:
            interaction: Interacción de Discord.
            cancion: Nombre de la canción o URL.
        
        Exceptions:
            DownloadError, ValueError, OSError: Si no se pudo obtener la fuente de audio.
            ClientError: Si no se pudo iniciar la fuente de audio.
        """
        await interaction.response.defer(thinking=True)

        guild = interaction.guild

        if guild is None:
            await interaction.followup.send("Este comando solo funciona en servidores.")
            return

        # casteo el voice_client de VoiceProtocol a VoiceClient, si no es una tortura intentar usar play.
        voice_client = cast(discord.VoiceClient | None, guild.voice_client)

        if voice_client is None or not voice_client.is_connected():
            await interaction.followup.send("Mágico no soy amigo, soy barman. Conectame con /join.")
            return

        if voice_client.is_playing() or voice_client.is_paused():
            await interaction.followup.send("Estás manija, no te gusta la música, ta bien, te entiendo. Mejor desconectame, salchicha.")
            return

        # busco y preparo la fuente de audio
        try:
            source: discord.AudioSource = await YTDLSource.from_url(cancion, stream=True)

        except (DownloadError, ValueError, OSError):
            logger.exception("No se pudo obtener la fuente de audio.")
            await interaction.followup.send("Mira campeon, si me vas a hacer buscar canciones que no existen, mejor ni ejecutes un comando.")
            return

        # reproducción del cliente, si falla algo, limpio el source y doy un mensaje q fallo la repro.
        try:
            voice_client.play(source=source, after=lambda error: (logger.error("Error del reproductor: %s", error) if error else None))

        except (discord.ClientException, OSError):
            source.cleanup()
            logger.exception("No se pudo iniciar la reproducción.")
            await interaction.followup.send("El Barman tuvo un problema con el audio, se rompio el cassette.")
            return

        await interaction.followup.send(f"Reproduciendo: {cancion}.\nNombre de la canción: {source.title}.\nBaila o te saco de la taberna wacho.")

    @app_commands.command(name="stop", description="Para desconectar al bot del canal de voz.")
    @app_commands.guild_only()
    @app_commands.allowed_installs(guilds=True, users=False)
    async def stop(self, interaction: discord.Interaction) -> None:
        """
            Detiene el bot de música y lo desconecta del canal.

            Args:
                interaction: Contexto para el comando de ejecución.
        """

        await interaction.response.defer(thinking=True)

        guild: discord.Guild | None = interaction.guild

        if guild is None: 
            await interaction.followup.send("Este comando sirve solo en servidores.")
            return

        voice_client: discord.VoiceClient | None = cast(discord.VoiceClient | None, guild.voice_client)

        if voice_client is None or not voice_client.is_connected():
            await interaction.followup.send("Me queres desconectar cuando no estoy conectado, buen chiste campeon. Conectame con /join.")
            return
        
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()

        await voice_client.disconnect()
        await interaction.followup.send("Ok amigo, desconecte el casette, pero la proxima tenes que pagar 2 birras si queres que desconecte la musica.")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Music(bot=bot))