#!/usr/bin/env python
import discord
import logging
import asyncio

from yt_dlp.utils import DownloadError
from discord.ext import commands
from discord import app_commands

from typing import cast, Self
from textwrap import dedent
from spotipy.exceptions import SpotifyException

from ..utils.players.youtube import YTDLSource
from ..utils.players.spotify import SpotifySource, SpotifyTrack
from ..utils.queue_bot.music_queue import MusicQueue
from ..utils.queue_bot.exceptions_queue import *


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
        self.cola = MusicQueue()
        self.worker: asyncio.Task[None] | None = None

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
            
            Returns:
                Un embed preparado para mostrar en un chat de texto con la información
                de la canción.
                
        """
        embed: discord.Embed
        if track is not None:
            embed = discord.Embed(title=f"Reproduciendo {track.song_title}",
                                color=discord.Color.green(),
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
                                color=discord.Color.red(),
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
        loop = asyncio.get_running_loop()
        finalizo = asyncio.Event()

        def _al_terminar(error: Exception | None) -> None:
            """
                Al terminar una canción, el callback necesita acceder a loop y finalizo.
                Esta función callback es clave para la comunicación entre Discord y Asyncio.
            """
            if error:
                logger.error("Error del reproductor: %s", error)

            loop.call_soon_threadsafe(finalizo.set)

        try:
            voice_client.play(source=source, after=_al_terminar)
            await finalizo.wait()
            return True

        except (discord.ClientException, OSError) as err:
            source.cleanup()
            logger.exception("No se pudo iniciar la reproducción. | Error = %s", err)
            return False

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

    @staticmethod
    async def _worker(cola: MusicQueue,
                      interaction: discord.Interaction,
                      voice_client: discord.VoiceClient) -> None:
        """
            Función asíncrona que se encarga de iniciar el worker
            que trabaja en la cola de reproducción, la mantiene activa
            y hace todo el trabajo pesado con la instancia MusicQueue.
        
            Args:
                cola:
                    Instancia de MusicQueue que guarda todos los datos
                    y ejecuta las operaciones correspondientes.
                interaction:
                    Contexto para el comando en ejecución.
                voice_client:
                    Cliente a conectarse al canal de voz.
        """

        while True:
            try:
                source = await cola.desencolar()

            except MusicQueueInactive:
                logger.exception("La cola se cerro. Finalizando worker.")
                break

            logger.info("Se desencolo la canción: %s", source.title)
            if not voice_client.is_connected():
                source.cleanup()
                break

            reproducida = await Music._reproducir_cancion(interaction, voice_client, source)
            if not reproducida:
                await interaction.followup.send("Amigo, quise meter el casette y estaba tan borracho que se rompio, perdona bro.")
            


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
        spotify_source = SpotifySource()
        guild = interaction.guild

        if guild is None:
            await interaction.followup.send("Este comando solo funciona en servidores.")
            return

        await interaction.response.defer(thinking=True)
        # casteo el voice_client de VoiceProtocol a VoiceClient, si no es una tortura intentar usar play.
        voice_client = cast(discord.VoiceClient | None, guild.voice_client)

        if voice_client is None or not voice_client.is_connected():
            await interaction.followup.send("Mágico no soy amigo, soy barman. Conectame con /join.")
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

        # encolar a la lista de reproducción.
        try:
            self.cola.encolar(source)
        except FullMusicQueue:
            source.cleanup()
            await interaction.followup.send(f"Amigo que re carajeanos pedis, ya meti {self.cola.capacidad} casettes."
                                            "\nAguanta a que termine 1 canción bro")
            return
        except MusicQueueInactive:
            source.cleanup()
            await interaction.followup.send("Amigo ya me desconecte y me tome 8 vodkas, si queres una canción conectame (toy re borracho igual.).")
            return

        if self.worker is None or self.worker.done():
            self.worker = asyncio.create_task(self._worker(self.cola, interaction, voice_client))

        embed = self._crear_embed(track, source)
        await interaction.followup.send("AH ESTAS PONIENDO LINDOS TEMAS, te veo re manija wacho, mas vale que bailes\n", embed=embed)

    @app_commands.command(name="skip", description="Para saltear una canción en reproducción.")
    @app_commands.guild_only()
    @app_commands.allowed_installs(guilds=True, users=False)
    async def skip(self: Self, interaction: discord.Interaction) -> None:
        """
            Función que se ocupa de skipear la canción actual y continuar con
            la cola de reproducción, si es que esta última está activa.

            Args:
                interaction:
                    Contexto para el comando de ejecución.
        """
        await interaction.response.defer(thinking=True)
        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message("Este comando solo funciona en servidores.")
            return

        voice_client = cast(discord.VoiceClient | None, guild.voice_client)
        if voice_client is None or not voice_client.is_connected():
            await interaction.followup.send("Amigo, primero conectame con el /join.")
            return

        if not voice_client.is_playing() and not voice_client.is_paused():
            await interaction.followup.send("Amigo no hay ninguna canción para saltear, que te pensas, que soy boludo?\nManda un tema wacho.")
            return

        voice_client.stop()
        await interaction.followup.send("Ah pero no me dejas disfrutar un tema porque te encanta skippear gil.")

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

        if self.worker is not None:
            self.worker.cancel()
            try:
                await self.worker
            except asyncio.CancelledError:
                pass
            self.worker = None

        self.cola.vaciar()

        await voice_client.disconnect()
        await interaction.followup.send("Ok amigo, desconecte el casette, pero la proxima tenes que pagar 2 birras si queres que desconecte la musica.")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Music(bot=bot))