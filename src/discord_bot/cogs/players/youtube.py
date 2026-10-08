import discord
import yt_dlp as youtube_dl
import asyncio
import logging

from typing import cast, Mapping, Any, Self

logger = logging.getLogger(__name__)

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
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes.
}

ffmpeg_options = {
    "before_options": (
        "-reconnect 1 "
        "-reconnect_streamed 1 "
        "-reconnect_delay_max 5"
    ),
    "options": "-vn"
}

ytdlp = youtube_dl.YoutubeDL(cast("youtube_dl._Params", ytdl_format_options))

class YTDLSource(discord.PCMVolumeTransformer):
    """
        Crear documentación.
    """

    def __init__(self, source: discord.AudioSource, *, data: Mapping[str, Any], volume: float = 0.5) -> None:
        """
            Crear documentación.
        """
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url: str, *, loop: asyncio.AbstractEventLoop | None = None, stream: bool = False) -> Self:
        """
            Completar type hints y documentacion.
        """

        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdlp.extract_info(url, download=not stream))

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
        
        return cls(discord.FFmpegPCMAudio(filename, before_options=ffmpeg_options["before_options"], options=ffmpeg_options['options']), data=data)