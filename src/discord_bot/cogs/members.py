import discord
import logging
from discord.ext import commands


# TODO: Configurar logger.
# TODO: Cuando se kickea a un usuario, mandar un md.
# TODO: Asignar un rol cuando el usuario se une.


logger = logging.getLogger(__name__)

class Members(commands.Cog):
    """
        Clase para interacción con los miembros de discord.

        Hereda:
            commands.Cog
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
            Atributos del constructor.

            Args:
                bot: Bot del servidor de discord.
        """

        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """
            Si el usuario se une, se le manda un mensaje privado de bienvenida.

            Args:
                member: Miembro del servidor de discord.
        """
        try:
            rol = discord.utils.get(member.guild.roles, name="Miembro")
            bot_member = member.guild.me
            text_channel = discord.utils.get(member.guild.text_channels, name="bienvenida")
            archivo = discord.File("files/beer_batman.jpg", filename="beer_batman.jpg", description="Batman tomandose una birra")
            if bot_member is not None:
                permisos = bot_member.guild_permissions
                if permisos.manage_roles and rol is not None:
                        await member.add_roles(rol)

            if text_channel is not None and bot_member is not None:
                await text_channel.send(f"Bienvenido {member.name}. Te uniste a la taberna, ahi te gire una birra bro. [Mentira me la re eskabie yo.]", file=archivo)

            await member.send(f"Bienvenido {member.name}! Disfruta del servidor :D")
            logger.info("Se mando un MD al usuario. Nombre = %s", member.name)
        except discord.Forbidden:
            logger.error(f"Fallo seguramente la asignación de rol, o el mandado de DM. Miembro = %s", member.name)
        except discord.HTTPException:
            logger.error(f"No se pudo asignar el rol y tiro una excepción HTTP.")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        """
            Si al usuario se fue del servidor, se le envia
            un mensaje privado para informarle que el se pierde
            tremendo servidor.

            Args:
                member: Miembro del servidor de discord.
        """
        try:
            bot_member = member.guild.me
            text_channel = discord.utils.get(member.guild.text_channels, name="despedida")
            archivo = discord.File("files/batman_triste_tomando_birra.jpg", filename="batman_triste_tomando_birra.jpg", description="Batman sad porq se fue un miembro")
            embed = discord.Embed(title="🍺 Te fuiste de la taberna :(", description=f"Nos vemos amigo, fue un gusto conocerte.", color=discord.Color.orange())
            embed.set_image(url="attachment://meme.jpg")
            if bot_member is not None and text_channel is not None:
                await text_channel.send(f"Estoy triste, te fuiste de mi vida, ahora tomo 3 birras en dedicación a vos soldado caído.", embed=embed, file=archivo)

            await member.send("Te fuiste del servidor? vos te lo perdes papirulo.")
        except discord.Forbidden:
            print(f"No se pudo enviar un DM a {member.name}")

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User) -> None:
        """
            Si el usuario es baneado, se le manda un mensaje personalizado al DM.

            Args:
                guild: Servidor de discord donde ocurre el baneo.
                user: Usuario baneado.
        """
        try:
            await user.send("Lamentablemente te tuvimos que banear. Por algo sera papirulo.")
        except discord.Forbidden:
            print(f"No se pudo enviar un DM a {user}")

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User) -> None:
        """
            Si el usuario es desbaneado, se le manda un mensaje personalizado al DM.
            Args:
                guild: Servidor de discord donde ocurre el desbaneo.
                user: Usuario desbaneado.
        """
        try:
            await user.send("Te desbanee porque estaba bueno. La proxima se pica y no cebolla.")

        except discord.Forbidden:
            print(f"No se pudo enviar un DM a {user}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Members(bot=bot))