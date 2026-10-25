#!/usr/bin/env python
"""
    Módulo para generar una cola de reproducción en el Bot de discord para música.

    Utiliza asyncio para generar la cola FIFO.
    Utiliza logging para loguear las excepciones que se levantan.
    Typing para el typehint del constructor.

    exceptions_queue:
        Son excepciones creadas que heredan el comportamiento de excepciones ya existentes de asyncio.
"""
import asyncio
import logging
from typing import Self

from .exceptions_queue import *
from ..players.youtube import YTDLSource

logger = logging.getLogger(__name__)

class MusicQueue:
    """
        Clase destinada a la cola de reproducción de música para el bot de discord.
    """

    def __init__(self: Self, maxsize: int = 30) -> None:
        """
            Atributos del constructor.

            Args:
                maxsize:
                    Máxima capacidad de la cola de reproducción.
        """
        self.queue: asyncio.Queue[YTDLSource] = asyncio.Queue(maxsize=maxsize)

    @property
    def capacidad(self: Self) -> int:
        """
            Devuelve la cantidad de elementos que acepta la cola,
            esta es una propiedad, es decir, la llamada no requiere parentesis.

            Returns:
                Un número entero con la maxima capacidad que puede tener la cola.
        """
        return self.queue.maxsize

    @property
    def cantidad(self: Self) -> int:
        """
            Devuelve el tamaño de la cola actual,
            esta es una propiedad, es decir, la llamada no requiere parentesis.

            Returns:
                Un número entero con la cantidad de elementos en la cola.
        """
        return self.queue.qsize()

    @property
    def esta_vacio(self: Self) -> bool:
        """
            Comunica si la cola esta vacia o no.

            Returns:
                Un valor booleano indicando si la cola esta vacía o no.
        """
        return self.queue.empty()

    @property
    def esta_llena(self: Self) -> bool:
        """
            Comunica si la cola esta llena o no.

            Returns:
                Un valor booleano indicando si la cola esta llena o no.
            
            Aclaracion
            -----------
                Si maxsize=0, esta funcion nunca retorna True, por el simple hecho
                de que ese valor por default declara una cola con capacidad infinita
                de elementos.
        """
        return self.queue.full()

    def cerrar(self: Self) -> None:
        """
            Cierra forzadamente la cola de reproducción.
        """
        self.queue.shutdown(immediate=True)

    def vaciar(self: Self) -> None:
        """
            Elimina todas las canciones pendientes de reproducción.
        """
        while not self.esta_vacio:
            self.queue.get_nowait()

    @staticmethod
    def _se_suministro_la_cancion(source: YTDLSource) -> bool:
        """
            Función que se ocupa de válidar si la canción
            se suministro o no.
        """
        if not source:
            logger.warning("No se suministro la canción para la cola | Source=%s", source)
            return False

        return True
        
    def encolar(self: Self, source: YTDLSource) -> None:
        """
            Función síncrona que se encarga de encolar en la cola de reproducción
            agregando el elemento a lo último de la cola.

            Args:
                source:
                    Instancia de YTDLSource con la metadata que se proceso.
            
            Exceptions:
                FullMusicQueue:
                    Si la cola esta llena, esta excepción se levanta.
                MusicQueueInactive:
                    Si la cola de reproducción no esta activa.
        """
        if not self._se_suministro_la_cancion(source):
            raise NoSongProvided("No se suministro una canción.")
        
        try:
            self.queue.put_nowait(source)
            
        except asyncio.QueueFull as exc:
            logger.warning(msg="Cola de reproducción llena.")
            raise FullMusicQueue("La cola de reproducción esta llena") from exc
        except asyncio.QueueShutDown as exc:
            logger.warning("La cola de reproducción no se encuentra activa.")
            raise MusicQueueInactive("La cola de reproducción no se encuentra activa.") from exc

    async def desencolar(self: Self) -> YTDLSource:
        """
            Función asincrona que se encarga de desencolar en la cola de reproducción,
            eliminado el primer elemento de la cola, y también retorna este item, esto
            es necesario para poder eliminar y reproducir la canción.
            
            Returns:
                La canción desencolada, esta misma es removida de la cola
                y devuelta para que el motor de reproducción lo procese.
            
            Exceptions:
                MusicQueueInactive:
                    Si la cola de reproducción no esta activa.
        """

        try:
            source = await self.queue.get()

        except asyncio.QueueShutDown as exc:
            logger.warning("La cola de reproducción no se encuentra activa.")
            raise MusicQueueInactive("La cola de reproducción no se encuentra activa.") from exc

        return source