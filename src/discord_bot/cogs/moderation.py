#!/usr/bin/env python

# Copyright (c) 2026 Rodrigo Riera.
# SPDX-License-Identifier: MIT

import discord
import logging
from discord.ext import commands
from datetime import timedelta

logger = logging.getLogger(__name__)


class Moderation(commands.Cog):
    """
        Moderador del bot de la taberna.

        Hereda:
            commands.Cog de discord.ext.
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
            Atributos del constructor.

            Args:
                bot: Bot del servidor de discord.
        """
        self.bot = bot

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        """
            Función predefinida como callback para poder elevar un error.

            Args:
                ctx: Contexto de ejecución de un comando.
                error: error a elevar cuando un comando falla.
        """
        if isinstance(error, commands.MemberNotFound):
            await ctx.send("Jefe, no pude encontrar a ese usuario, vofi.")

    @commands.command(name="clear", description="Elimina mensajes en un canal específico.")
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

    @commands.command(name="kick", description="Kickea a un usuario del servidor.")
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str | None = None) -> None:
        """
            Kickea a un usuario que se encuentra en el servidor.

            Args:
                ctx: Contexto en el que se ejecuta el comando.
                member: Miembro a kickear del servidor.
                reason [Opcional]: Razón del kickeo del servidor.
        """
        try:
            archivo = discord.File("files/meme.jpg", filename="meme.jpg", description="Meme para el kick.")
            embed = discord.Embed(title="🍺 Expulsado de la taberna", description=f"Nos vemos en Disney, {member.name}. Te re cabio el kick.", color=discord.Color.red())
            embed.set_image(url="attachment://meme.jpg")
            
            await member.send(content=f"Fuiste kickeado del servidor por fachero y papirulo {member.name}. Nos vemos en disney.", file=archivo, embed=embed)
            await member.kick(reason=reason)
            await ctx.send(f"{member} fue kickeado del servidor.")
        except discord.Forbidden:
            await ctx.send("No pude enviarle el DM, pero voy a expulsarlo.")
            logger.error("No pude mandarle el DM a %s", member.name)

    @commands.command(name="ban", description="Banea a un usuario del servidor.")
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str | None = None) -> None:
        """
            Banea a un usuario que se encuentra en el servidor.

            Args:
                ctx: Contexto en el que se ejecuta el comando.
                member: Miembro a banear del servidor.
                reason[Optional]: Razón del kickeo del servidor.
        """
        await member.ban(reason=reason)
        await ctx.send(f"{member} fue baneado del servidor.")
    
    @commands.command(name="unban", description="Desbanea a un usuario del servidor.")
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, member: discord.User, *, reason: str | None = None) -> None:
        """
            Desbanea a un usuario que se encuentra en el servidor.

            Args:
                ctx: Contexto en el que se ejecuta el comando.
                member: Miembro a desbanear del servidor.
                reason[Optional]: Razón del kickeo del servidor.
        """
        if ctx.guild is None:
            return
        
        await ctx.guild.unban(member, reason=reason)
        await ctx.send(f"{member} desbaneado.")

    @commands.command(name="timeout", description="Mutea a un usuario por un tiempo específico.")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def timeout(self, ctx: commands.Context,
                      member: discord.Member,
                      minutes: int,
                      *,
                      reason: str | None = None) -> None:
        """
            Mutea a un usuario durante un tiempo especificado.

            Args:
                ctx: Contexto de ejecución de un comando.
                member: Miembro del servidor.
                seconds[Optional]: segundos.
                minutes[Optional]: minutos.
                hours[Optional]: horas.
                days[Optional]: días.
                reason[Optional]: Razón del muteo.
        """
        if minutes <= 0:
            await ctx.send("La duración de los minutos debe ser mayor a 0.")
            return

        duracion = timedelta(minutes=minutes)

        await member.timeout(duracion, reason=reason)
        await ctx.send(f"{member.mention} se le aplico un timeout por {duracion}", ephemeral=True)

    @commands.command(name="untimeout", description="Desmutea a un usuario")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def untimeout(self, ctx: commands.Context, member: discord.Member, guild_id: int) -> None:
        """
            Desmutea a un usuario.

            Args:
                ctx: Contexto de ejecución de un comando.
                member: Miembro del servidor de discord.
                guild_id: id del servidor de discord.
        """
        await member.timeout(None)

        await ctx.send(f"{member.mention} ya no tiene un timeout.")
    

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Moderation(bot=bot))
