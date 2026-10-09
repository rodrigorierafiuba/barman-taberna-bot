from discord.ext.commands.errors import CheckFailure

class NotConnectedToVoice(CheckFailure):
    """
        El usuario no esta conectado a ningun canal
        de voz.
    """
    pass

class PlayerNotConnected(CheckFailure):
    """
        El bot no esta conectado al canal de voz.
    """
    pass

class MustBeSameChannel(CheckFailure):
    """
        Bot y usuario no estan en el mismo canal.
    """
    pass

class NothingIsPlaying(CheckFailure):
    """
        No hay ninguna canción en reproducción, si
        pasa eso, se levanta la excepción.
    """
    pass

# TODO: Agregar NotEnoughSong, si no hay canciones en la lista de repro.
# TODO: Agregar InvalidLoopMode, si el bucle de canciones es inválido.
