#!/usr/bin/env python

# Copyright (c) 2026 Rodrigo Riera.
# SPDX-License-Identifier: MIT

"""
    Módulo para obtener la metadata que proviene de la URL o URI de Spotify.

    Este módulo se encarga de recolectar toda la metadata proveniente de una URL o URI de Spotify,
    para luego ser enviado ordenadamente en un SpotifyTrack al mótor de YTDLSource que se encarga
    de reproducir la canción en Discord mediante YouTube.
"""
import spotipy as spotify
import os
import asyncio
import logging
import re

from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.exceptions import SpotifyException
from dotenv import load_dotenv
from pathlib import Path
from dataclasses import dataclass
from typing import Self, Any

ROOT = Path(__file__).resolve().parents[4]
load_dotenv(ROOT / ".env")

auth_manager = SpotifyClientCredentials(client_id=os.getenv("CLIENT_ID_SP"),
                                        client_secret=os.getenv("CLIENT_SECRET_SP"))

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class SpotifyTrack:
    """
        Se encarga de guardar en una instancia inmutable los siguientes datos:
            > Titulo de la canción.
            > Nombre del artista.
            > Nombre del album.
            > Año en que se publico el album.[Opcional]
            > Duración de la canción.[Se podría usar un conversor.]
    """
    song_title: str
    song_url: str
    artist_name: str
    artist_profile: str
    album_image: str | None
    album_name: str
    release_date: str
    duracion_ms: int

    @property
    def formatear_duracion(self: Self) -> str:
        """
            Formatea la duración que pasa Spotipy de milisegundos
            a un formato: {minutos}:{segundos}.

            Returns:
                Un string formateado con los minutos y segundos preparado
                para ser mostrado en un mensaje o en un embed.
        """
        dividendo = 60_000
        minutos = self.duracion_ms // dividendo
        segundos = int(((self.duracion_ms / dividendo) - minutos) * 60)

        return f"{minutos}:{segundos:02d}"

    @property
    def formatear_release_date(self: Self) -> str:
        """
            Formatea el release year que viene de la manera:
            e.g.: '2017-07-07'.
            
            Returns:
                Un string formateado con la fecha mucho más verbosa,
                con el formato: 
                    Año: {anio}
                    Mes: {mes}
                    Dia: {dia}
                Y el resultado que se obtiene en el return es:
                    Fecha de publicación del album:
                        07-07-2017
        """
        partes = self.release_date.split("-")

        if len(partes) == 3:
            anio, mes, dia = partes
            return f"{dia}/{mes}/{anio}"

        elif len(partes) == 2:
            anio, mes = partes
            return f"{mes}/{anio}"

        return partes[0]
    
class SpotifySource():
    """
        Gestiona los metadatos de canciones mediantes enlaces
        de Spotify.

        Se encarga de consultar canciones y almacenar
        su información en instancias de SpotifyTrack.

        Los metadatos obtenidos se pueden utilizar
        despues para buscar la fuente de audio
        con YTDLSource. [ver youtube.py]

        Aclaración:
            Esta clase no descarga ni reproduce audio.
    """
    @staticmethod
    def _extraer_id_spotify(url: str) -> str | None:
        """
            Se encarga de extraer el id que esta en la URL de Spotify,
            esto facilita el hecho de poder pasar directamente el ID para
            buscar la canción en Spotify y no depender de URL o URI's
            que por una parte, las URL, por ejemplo, pueden no estar normalizadas.

            Args:
                url: Url de la canción de Spotify.
            
            Returns:
                El ID de la canción de Spotify.

                Si no se encuentra un track_id, se devuelve None.
        """
        url_patron = r"^(?:https?://)?open\.spotify\.com/(?:intl-[a-z]{2}/)?track/(?P<track_id>[A-Za-z0-9]{22})/?(?:\?.*)?$"
        uri_patron = r"^spotify:track:(?P<track_id>[A-Za-z0-9]{22})$"
        track_id = ""

        # Checkear patron URL y URI.
        match = re.fullmatch(url_patron, url)
        match_2 = re.fullmatch(uri_patron, url)

        if match:
            track_id = match.group("track_id")
            return track_id
        elif match_2:
            track_id = match_2.group("track_id")
            return track_id
            
        return None

    @staticmethod
    def _completar_spotify_track(result: Any) -> SpotifyTrack:
        """
            Al momento de llamar esta función, ya se manejo la excepción
            de SpotifyException, es por eso que esta función no devuelve un
            Optional[SpotifyTrack], equivalente a SpotifyTrack | None.

            Args:
                result: 
                    Metadata de Spotify relacionada a una canción buscada
                    desde una URL.
            
            Returns:
                Una instancia de SpotifyTrack con los datos ya guardados
                en esta misma.
        """
        song_title = result['name']
        song_url = result['external_urls']['spotify']
        artist_name = result['artists'][0]['name']
        artist_profile = result['artists'][0]['external_urls']['spotify']
        images = result["album"].get("images", [])
        album_image = images[0]['url'] if images else None
        album_name = result['album']['name']
        release_date = result['album']['release_date']
        duracion_ms = result['duration_ms']

        return SpotifyTrack(
            song_title=song_title,
            song_url=song_url,
            artist_name=artist_name,
            artist_profile=artist_profile,
            album_image=album_image,
            album_name=album_name,
            release_date=release_date,
            duracion_ms=duracion_ms
        )

    async def track_from_url(self: Self, url: str) -> SpotifyTrack | None:
        """
            Hace una busqueda con Spotipy de la canción a querer
            reproducir en el bot de Discord.

            Args:
                cancion: 
                    Nombre de la canción a buscar.
            
            Returns:
                Una instancia de SpotifyTrack, teniendo los metadatos de la canción.
                Retorna None si la busqueda no produce resultados.
            
            Exceptions:
                SpotifyException:
                    Si ocurre un error al intentar traer la metadata de la canción
                    de la API de Spotify.
        """
        track_id = self._extraer_id_spotify(url)
        if track_id is None:
            return None
        
        try:
            sp = spotify.Spotify(auth_manager=auth_manager)
            result = await asyncio.to_thread(sp.track, track_id)
        except SpotifyException as err:
            logger.exception("Ocurrió un error al intentar llamar a la API de Spotify | Error = %s", err)
            raise

        return self._completar_spotify_track(result)
        



        

    



