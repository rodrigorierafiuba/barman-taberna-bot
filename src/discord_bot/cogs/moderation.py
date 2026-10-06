import discord
from discord.ext import commands


class Moderation(commands.Cog):
    """
        Moderador del bot de la taberna.

        Hereda:
            commands.Cog de discord.ext.
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
            Atributos del constructor.
        """
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def clear(self, ctx: commands.Context, count: int) -> None:
        """
            Elimina los ultimos 'count' mensajes (solo para moderadores).

            Args:
                ctx: Contexto en el que se ejecuto el comando.
                count: Cantidad de mensajes a borrar.
        """
        if not 1 <= count <= 100:
            await ctx.send("Elegi un número entre el 1 y el 100.")
            return

        if not isinstance(ctx.channel, discord.TextChannel):
            return
        
        eliminado = await ctx.channel.purge(limit=count + 1)
        confirmacion = await ctx.send(f"Eliminado: {len(eliminado) - 1} mensajes.")
        await confirmacion.delete(delay=3)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Moderation(bot=bot))
        