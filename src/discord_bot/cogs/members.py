import discord
from discord.ext import commands

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
            await member.send(f"Bienvenido {member.name}! Disfruta del servidor :D")
        except discord.Forbidden:
            print(f"No se pudo enviar un DM a {member.name}")

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