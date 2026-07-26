from redbot.core import commands
import discord

class Mycog(commands.Cog):
    """My custom cog that does stuff! Edit me, then [p]reload mycog."""

    @commands.command()
    async def mycom(self, ctx):
        """This does stuff!"""
        await ctx.send("I can do stuff!")

    @commands.command()
    async def punch(self, ctx, user: discord.Member):
        """I will punch anyone! >.<  Usage: [p]punch @someone"""
        await ctx.send(f"ONE PUNCH! And {user.mention} is out! ლ(ಠ益ಠლ)")

    @commands.command()
    async def hello(self, ctx, *, name: str = ""):
        """Greets someone. Usage: [p]hello [name]"""
        target = name or ctx.author.display_name
        await ctx.send(f"Hello, {target}! 🐍")

def setup(bot):
    bot.add_cog(Mycog())
