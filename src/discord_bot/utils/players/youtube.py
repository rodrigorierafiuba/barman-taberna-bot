#!/usr/bin/env python

# Copyright (c) 2026 Rodrigo Riera.
# SPDX-License-Identifier: MIT

"""
    Motor de youtube implementado para reproducir canciones por busqueda de texto y canciones.

    El corazón del motor es YTDLSource, 
    que representa una fuente de audio obtenida mediante yt-dlp,
    preparada para su reproducción en un canal de voz de Discord.

    Se encarga de almacenar los metadatos de la canción,
    configurar la fuente de audio con FFmpeg y 
    permitir el control de volumen durante la reproducción.
"""
import discord
import yt_dlp as youtube_dl
import asyncio
import logging
import sys

from time import perf_counter
from typing import cast, Mapping, Any, Self
from pathlib import Path

logger = logging.getLogger(__name__)

COOKIES_PATH = Path(__file__).resolve().parents[3] / "cookies.txt" # Esto es si cookies.txt esta en la raíz del proyecto.

ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': False,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0', # formato ipv4, ipv6 a veces tiene errores.
    'cookiefile': str(COOKIES_PATH) # VITAL para que no frene al bot, necesitas crear un cookies.txt
}

ffmpeg_options = {
    "before_options": (
        "-reconnect 1 "
        "-reconnect_streamed 1 "
        "-reconnect_delay_max 5"
    ),
    "options": "-vn -loglevel info"
}

ytdlp = youtube_dl.YoutubeDL(cast("youtube_dl._Params", ytdl_format_options))

class YTDLSource(discord.PCMVolumeTransformer):
    """
        Representa una fuente de audio obtenida mediante yt-dlp,
        preparada para su reproducción en un canal de voz de Discord.

        Se encarga de almacenar los metadatos de la canción,
        configurar la fuente de audio con FFmpeg y 
        permitir el control de volumen durante la reproducción.

        Hereda de:
            discord.PCMVolumeTransformer.
    """

    def __init__(self: Self, source: discord.AudioSource, *, data: Mapping[str, Any], volume: float = 0.5) -> None:
        """
            Inicializa el constructor de la clase y una fuente de audio con sus
            metadatos y un volumen de reproducción determinado.

            Args:
                source:
                    Fuente de audio que será utilizada por discord.
                
                data:
                    Diccionario con los metadatos obtenidos mediante
                    yt-dlp, como el título y la URL del contenido.
                
                volume:
                    Volumen inicial de reproducción.
                    Por defecto, esta en 0.5 (50%)
            
            Attributes:
                data:
                    Metadatos originales de la canción.
                
                title:
                    Titulo de la canción, si esta disponible.
                
                cancion:
                    URL del contenido obtenida de los metadatos.
        """
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.cancion = data.get('url')
        self.duracion = data.get('duration')
        self.thumbnail = data.get('thumbnail')
        self.webpage_url = data.get('webpage_url')

    @property
    def formatear_duracion(self) -> str | None:
        """
            Formatea la duración que pasa yt-dlp de milisegundos
            a un formato: {minutos}:{segundos}.

            Returns:
                Un string formateado con los minutos y segundos preparado
                para ser mostrado en un mensaje o en un embed.
            
            Aclaracion:
                Se tomo el tipo de calculo del conversor llamado tinycalcs [Checkear su página para mas info].
        """
        if self.duracion is None:
            return None

        minutos, segundos = divmod(int(self.duracion), 60)

        return f"{minutos}:{segundos:02d}"

    @staticmethod
    async def obtener_playlist(url: str) -> list[str] | None:
        """
            Método estático que a partir de una url de una playlist,
            obtiene todas las canciones para ser encoladas en el reproductor
            de música del bot de discord.

            Args:
                url:
                    Url de la playlist.
            
            Returns:
                Listado de URL's a reproducir.
        """

        opciones = {
            **ytdl_format_options,
            "noplaylist": False,
            "extract_flat": "in_playlist",
            "skip_download": True,
        }

        ydl = youtube_dl.YoutubeDL(cast("youtube_dl._Params", opciones))
        data = await asyncio.to_thread(ydl.extract_info, url, download=False)

        if not data or data.get("_type") != "playlist" or data.get("extractor_key") != "YoutubeTab":
            return None

        return [f"https://www.youtube.com/watch?v={entry["id"]}"
                for entry in data.get("entries", [])
                if entry and entry.get("id")
            ]

    @classmethod
    async def from_url(cls: type[Self], cancion: str, *,
                       loop: asyncio.AbstractEventLoop | None = None,
                       stream: bool = False) -> Self:
        """
            Obtiene información de una canción mediante yt-dlp
            y construye una fuente de audio reproducible en Discord.

            La extracción de información se ejecuta en un executor
            para evitar bloquear el event loop de asyncio.

            Si la busqueda devuelve múltiples resultados, se selecciona
            el primero disponible.

            Args:
                cancion:
                    URL o texto de busqueda de la canción.
                    Las busquedas por texto dependen de la configuración
                    de yt-dlp.
                
                loop:
                    Event loop utilizado para ejecutar la extracción.
                    Si no se proporciona, se obtiene el event loop asociado al contexto actual.
                
                stream:
                    Indica si el audio se reproducirá directamente
                    desde una URL o desde un archivo descargado.

                    True:
                        Utiliza la URL de audio extraída.

                    False:
                        Descarga el contenido y utiliza la ruta
                        del archivo generado.

                    Por defecto, es False.
            Returns:
                Una instancia de YTDLSource con los metadatos
                y la fuente FFmpeg preparada para reproducirse.

            Raises:
                ValueError:
                    Si no se encuentran resultados válidos o
                    no se puede obtener la ubicación del audio.

                yt_dlp.utils.DownloadError:
                    Si yt-dlp no puede descargar o extraer
                    la información solicitada.

            Aclaración:
                Este método prepara la fuente de audio, pero
                no inicia su reproducción automáticamente.
                Para reproducirla debe utilizarse el método
                play() de discord.VoiceClient.
                  
        """
        # Configuro un logger para evaluar el delay que pasa siempre en el primer arranque del bot.
        inicio = perf_counter()
        logger.info("Iniciando extracción con yt-dlp: %s", cancion)
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdlp.extract_info(cancion, download=not stream))

        logger.info("Extracción finalizada en %.2f segundos", perf_counter() - inicio)
        entries = data.get('entries')

        if entries is not None:
            data = next(iter(entries), None)

            if data is None:
                logger.error("No se pudo extraer información del video.")
                raise ValueError("No se pudo extraer información del video.")

        filename = data.get('url') if stream else ytdlp.prepare_filename(data)
        if filename is None:
            logger.error("No se pudo obtener la URL del audio.")
            raise ValueError("No se pudo obtener la URL del audio.")
        
        return cls(discord.FFmpegPCMAudio(filename,
                                          before_options=ffmpeg_options["before_options"],
                                          options=ffmpeg_options['options'],
                                          stderr=sys.stderr.buffer), data=data)