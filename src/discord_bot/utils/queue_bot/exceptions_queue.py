import asyncio
# Copyright (c) 2026 Rodrigo Riera.
# SPDX-License-Identifier: MIT

"""
    Módulo de excepciones de la cola de reproducción.
"""
class EmptyMusicQueue(asyncio.QueueEmpty):
    """
        RAISES
        -------
            Una excepción lanzada cuando la cola esta vacía y no se puede utilizar
            queue.get() para conseguir una canción a mostrar en el bot de
            discord.
    """
    pass

class FullMusicQueue(asyncio.QueueFull):
    """
        RAISES
        -------
            Una excepción lanzada cuando la cola esta llena y no se puede encolar
            más objetos en la lista de reproducción para el bot de discord.
    """
    pass

class MusicQueueInactive(asyncio.QueueShutDown):
    """
        RAISES
        -------
            Una excepción lanzada cuando la cola no existe mas y se trata de
            encolar o desencolar esta misma.
    """
    pass

class NoSongProvided(Exception):
    """
        RAISES
        -------
            Una excepción lanzada cuando no se suministra una canción para agregar a la cola.
    """
    pass