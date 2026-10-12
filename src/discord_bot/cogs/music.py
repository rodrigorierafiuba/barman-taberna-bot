import discord
import logging

from yt_dlp.utils import DownloadError
from discord.ext import commands
from discord import app_commands

from typing import cast, Self
from textwrap import dedent
from spotipy.exceptions import SpotifyException

from .players.youtube import YTDLSource
from .players.spotify import SpotifySource, SpotifyTrack


logger = logging.getLogger(__name__)


class Music(commands.Cog):
    """
        Clase que va a reproducir musica que pida el usuario
        mientras este conectado a un voice channel.
    """

    def __init__(self: Self, bot: commands.Bot) -> None:
        """
            Atributos del constructor.

            Args:
                bot: Bot del servidor.
        """
        self.bot = bot 

    @staticmethod
    def _crear_embed(track: SpotifyTrack | None,
                           source: YTDLSource) -> discord.Embed:

        """
            Función que se encarga de crear el Embed para mostrar en el 
            canal donde se llamo por comando al Bot para reproducir
            una canción, ya sea de Spotify o de Youtube.

            Args:
                track: 
                    Simplemente la metadata de la canción de Spotify
                    que fue buscada, puede ser None.
                
                source:
                    Fuente de audio obtenida mediante yt-dlp, contiene también
                    la metadata del video de Youtube buscado.
                
                cancion:
                    Cancion a reproducir en el canal de voz de discord.
            
            Returns:
                
        """
        embed: discord.Embed
        if track is not None:
            embed= discord.Embed(title=f"Reproduciendo {track.song_title}",
                                color=discord.Color.orange(),
                                url=track.song_url
            )
            embed.description = dedent(f"""
                **Nombre de la canción**: {track.song_title}
                **Artista**: {track.artist_name}
                **Album**: {track.album_name}
                **Año de publicación**: {track.formatear_release_date}
                **Duracion**: {track.formatear_duracion}
            """).strip()
            if track.album_image:
                embed.set_image(url=track.album_image)
        else:
            embed = discord.Embed(title=f"Reproduciendo {source.title}",
                                color=discord.Color.orange(),
                                url=source.webpage_url
            )
            
            embed.description = dedent(f"""
                **Titulo de la canción**: {source.title}
                **URL**: {source.webpage_url}
                **Duración**: {source.formatear_duracion}
            """).strip()
            if source.thumbnail:
                embed.set_image(url=source.thumbnail)

        return embed
    
    @staticmethod
    async def _reproducir_cancion(interaction: discord.Interaction, voice_client: discord.VoiceClient, source: YTDLSource) -> bool:
        """
            Se encarga de reproducir la canción en el canal de voz.

            Args:
                interaction: Contexto del comando en ejecución.
                voice_client: Cliente que se ocupa de reproducir la canción en el canal de voz. [Esto refiere al bot, estando en el canal de voz, intentando reproducir la canción].
                source: canción ya buscada y encontrada por la clase YTDLSource.

            Exceptions:
                ClientError: Si no se pudo iniciar la fuente de audio.
                OSError: Si no se pudo obtener la fuente de audio.
            
            Aclaracion:
                Previamente a ejecutar esta función, se sabe de antemano que source y voice_client no son None. [Mirar función async def play().]
        """
        try:
            voice_client.play(source=source, after=lambda error: (logger.error("Error del reproductor: %s", error) if error else None))

        except (discord.ClientException, OSError) as err:
            source.cleanup()
            logger.exception("No se pudo iniciar la reproducción. | Error = %s", err)
            await interaction.followup.send("El Barman tuvo un problema con el audio, se rompio el cassette.")
            return False

        else:
            return True

    @staticmethod
    async def _ejecutar_yt(interaction: discord.Interaction, *, cancion: str) -> YTDLSource | None:
        """
            Función que se ocupa de obtener la fuente de audio con yt-dlp.

            Args:
                interaction: Contexto del comando en ejecución.
                cancion: Nombre de la canción o la URL de esta misma.
            
            Returns:
                Una instancia de YTDLSource que ya contiene la metadata de la canción a reproducir.

            Exceptions:
                DownloadError: Si no se pudo obtener la fuente de audio.
                ValueError: Si no se pudo obtener la fuente de audio.
                OSError: Si no se pudo obtener la fuente de audio.
        """
        # busco y preparo la fuente de audio
        try:
            source: YTDLSource = await YTDLSource.from_url(cancion, stream=True)
        except DownloadError as err:
            logger.exception("No se pudo obtener la fuente de audio. | Error = %s", err)
            await interaction.followup.send("Mira campeon, si me vas a hacer buscar canciones que no existen, mejor ni ejecutes un comando.")
            return None
        
        except (ValueError, OSError) as err:
            logger.exception("No se pudo obtener la fuente de audio. | Error = %s", err)
            await interaction.followup.send("Ni idea que paso, debo estar muy borracho para poner un tema amigo")
            return None

        else:
            return source

    @app_commands.command(name="join", description="Unirse a un canal de voz.")
    @app_commands.guild_only()
    @app_commands.allowed_installs(guilds=True, users=False)
    async def join(self: Self, interaction: discord.Interaction, *, channel: discord.VoiceChannel) -> None:
        """
            Función para que el bot se una al voice channel.

            Args:
                interaction: Contexto para el comando en ejecución.
                channel: Voice channel donde va a unirse el bot.
        """
        guild: discord.Guild | None = interaction.guild
        member= interaction.user
        if guild is None:
            return

        await interaction.response.defer(thinking=True)

        if not isinstance(member, discord.Member):
            await interaction.followup.send("No pude verificar si estas en el canal de voz, fijate de nuevo porfa")
            return

        if member.voice is None or member.voice.channel != channel:
            await interaction.followup.send("Flaco, como carajeanos queres que vaya a tomar birra y escuchar música con vos"
                                            " si no estas conectado.")
            return
        
        voice_client = cast(discord.VoiceClient | None, guild.voice_client)

        if voice_client is not None:
            if voice_client.is_connected():
                await interaction.followup.send("Amigo vos te pensas que soy re boludo, si estoy con vos escuchando musica mientras me tomo 8 birras.")
                return

            await voice_client.disconnect(force=True)

        await channel.connect()
        await interaction.followup.send("Listo! Ya estoy en el voice amigo!")

    @app_commands.command(name="play", description="Pone música en el canal de voz.")
    @app_commands.guild_only()
    @app_commands.allowed_installs(guilds=True, users=False)
    async def play(self: Self, interaction: discord.Interaction, *, cancion: str) -> None:
        """
        Busca y reproduce música utilizando yt-dlp.

        Args:
            interaction: Interacción de Discord.
            cancion: Nombre de la canción o URL.

        """
        await interaction.response.defer(thinking=True)

        spotify_source = SpotifySource()
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

        try:
            track = await spotify_source.track_from_url(cancion)
        except SpotifyException:
            await interaction.followup.send("Amigo, estoy tan borracho q creo q spotify me reboto la entrada")
            return
        
        if track is not None:
            source = await self._ejecutar_yt(interaction, cancion=f"{track.song_title} - {track.artist_name}")
            if source is None:
                return
        else:
            # busco y preparo la fuente de audio
            source = await self._ejecutar_yt(interaction, cancion=cancion)
            if source is None:
                return
            
        # reproducción del cliente, si falla algo, limpio el source y doy un mensaje q fallo la repro.
        cancion_reproducida = await self._reproducir_cancion(interaction, voice_client, source)
        if not cancion_reproducida:
            return

        embed = self._crear_embed(track, source)

        await interaction.followup.send(f"Baila o te saco de la taberna wachoo!", embed=embed)


    @app_commands.command(name="stop", description="Para desconectar al bot del canal de voz.")
    @app_commands.guild_only()
    @app_commands.allowed_installs(guilds=True, users=False)
    async def stop(self: Self, interaction: discord.Interaction) -> None:
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