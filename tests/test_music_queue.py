#!/usr/bin/env python
"""
Módulo de testing para la cola de reproducción.

Se testea:
    - Creación de la cola.
    - Encolación de canciones.
    - Desencolación y orden FIFO.
    - Espera asíncrona cuando la cola está vacía.
    - Manejo de excepciones.
    - Reutilización de la cola después de vaciarla.
"""

import asyncio
from unittest.mock import Mock
from typing import Callable, cast

import pytest

from discord_bot.utils.queue_bot.music_queue import MusicQueue
from discord_bot.utils.queue_bot.exceptions_queue import (
    FullMusicQueue, NoSongProvided, MusicQueueInactive
)
from discord_bot.utils.players.youtube import YTDLSource


@pytest.fixture
def crear_source():
    """Crea una fuente de audio simulada sin utilizar YouTube ni FFmpeg."""
    def factory(nombre: str) -> YTDLSource:
        source = Mock(spec=YTDLSource)
        source.title = nombre
        return source

    return factory


def test_crear_cola(crear_source: Callable[..., YTDLSource]) -> None:
    """Comprueba la creación, capacidad y vaciado de la cola."""
    cola = MusicQueue(maxsize=3)

    assert cola.capacidad == 3, "La capacidad inicial de la cola debería ser 3."
    assert cola.cantidad == 0, "La cantidad inicial debería ser 0."

    cola.encolar(crear_source("Te doy una canción - Silvio Rodríguez"))
    cola.encolar(crear_source("Ojalá - Silvio Rodríguez"))

    assert cola.cantidad == 2, "La cantidad debería ser 2."

    cola.encolar(crear_source("Té para tres - Gustavo Cerati"))

    assert cola.cantidad == 3, "La cantidad debería ser 3."
    assert cola.esta_llena, "La cola debería estar llena."

    cola.vaciar()

    assert cola.cantidad == 0, "La cantidad debería ser 0."
    assert cola.esta_vacio, "La cola debería estar vacía."


def test_encolar(crear_source: Callable[..., YTDLSource]) -> None:
    """Comprueba que se puedan encolar 30 canciones y que la siguiente sea rechazada."""
    cola = MusicQueue()

    for i in range(30):
        cola.encolar(crear_source(f"Canción encolada {i}"))
        assert cola.cantidad == i + 1, f"Se esperaban {i + 1} canciones, pero hay {cola.cantidad}."

    assert cola.cantidad == 30, "La cola debería contener 30 canciones."
    assert cola.esta_llena, "La cola debería estar llena."

    with pytest.raises(FullMusicQueue):
        cola.encolar(crear_source("Una canción más"))

    cola.vaciar()

    assert cola.cantidad == 0, "La cantidad debería ser 0."
    assert cola.esta_vacio, "La cola debería estar vacía."


@pytest.mark.asyncio
async def test_desencolar(crear_source: Callable[..., YTDLSource]) -> None:
    """Comprueba la desencolación de 100 canciones respetando el orden FIFO."""
    cola = MusicQueue(maxsize=100)
    canciones = [crear_source(f"Canción encolada {i}") for i in range(100)]

    for source in canciones:
        cola.encolar(source)

    for source_esperado in canciones:
        source_obtenido = await cola.desencolar()
        assert source_obtenido is source_esperado, "La cola debería devolver las canciones en orden FIFO."

    cola.cerrar()

    with pytest.raises(MusicQueueInactive):
        await cola.desencolar()

    assert cola.cantidad == 0, "La cola debería tener cantidad 0."
    assert cola.esta_vacio, "La cola debería estar vacía."


@pytest.mark.asyncio
async def test_esperar_cancion_para_desencolar(crear_source: Callable[..., YTDLSource]) -> None:
    """Comprueba que desencolar espere hasta recibir una fuente de audio."""
    cola = MusicQueue()
    tarea = asyncio.create_task(cola.desencolar())

    await asyncio.sleep(0)

    assert not tarea.done(), "Desencolar no debería finalizar si la cola está vacía."

    source = crear_source("La Noche Sin Ti - Los Huayra")
    cola.encolar(source)

    cancion = await asyncio.wait_for(tarea, timeout=1)

    assert cancion is source, "La canción desencolada debería ser la misma instancia encolada."
    assert cola.esta_vacio, "La cola debería estar vacía."


def test_cancion_vacia() -> None:
    """Comprueba que se rechace una fuente de audio no suministrada."""
    cola = MusicQueue()

    with pytest.raises(NoSongProvided):
        cola.encolar(cast(YTDLSource, None))


def test_encolar_cola_cerrada(crear_source: Callable[..., YTDLSource]) -> None:
    """Comprueba que no se pueda encolar después de cerrar la cola."""
    cola = MusicQueue()
    cola.cerrar()

    with pytest.raises(MusicQueueInactive):
        cola.encolar(crear_source("Owner of a Lonely Heart - Yes"))


@pytest.mark.asyncio
async def test_cerrar_mientras_espera() -> None:
    """Comprueba que cerrar la cola desbloquee una tarea que espera una canción."""
    cola = MusicQueue()
    tarea = asyncio.create_task(cola.desencolar())

    await asyncio.sleep(0)

    assert not tarea.done(), "Desencolar no debería finalizar si la cola está vacía."

    cola.cerrar()

    with pytest.raises(MusicQueueInactive):
        await asyncio.wait_for(tarea, timeout=1)


def test_reutilizar_cola_despues_de_vaciar(crear_source: Callable[..., YTDLSource]) -> None:
    """Comprueba que la cola pueda reutilizarse después de vaciarla, como en /stop."""
    cola = MusicQueue()

    cola.encolar(crear_source("Soda Stereo"))
    cola.vaciar()

    source = crear_source("Gustavo Cerati")
    cola.encolar(source)

    assert cola.cantidad == 1, "La cantidad debería ser 1."
    assert not cola.esta_vacio, "La cola no debería estar vacía."
    assert cola.queue.get_nowait() is source, "La cola debería conservar la nueva fuente."