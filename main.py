import discord
from discord.ext import commands
import os
import json
import shutil
import datetime

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================== ARQUIVOS ==================

def load_json(file):
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def backup_files():
    if not os.path.exists("backup"):
        os.makedirs("backup")

    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    for file in ["credits.json", "stock.json", "history.json"]:
        if os.path.exists(file):
            shutil.copy(file, f"backup/{file.replace('.json','')}_{now}.json")

# ================== COMANDOS ==================

@bot.command()
async def credits(ctx):
    credits = load_json("credits.json")
    user_id = str(ctx.author.id)
    saldo = credits.get(user_id, 0)
    await ctx.send(f"💳 Você tem {saldo} créditos.")

@bot.command()
async def addcredits(ctx, member: discord.Member, amount: int):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send("❌ Sem permissão.")

    credits = load_json("credits.json")
    user_id = str(member.id)

    credits[user_id] = credits.get(user_id, 0) + amount
    save_json("credits.json", credits)

    await ctx.send(f"✅ {amount} créditos adicionados para {member.mention}")

@bot.command()
async def stock(ctx):
    stock = load_json("stock.json")

    embed = discord.Embed(title="📦 Estoque Atual", color=discord.Color.blue())
    embed.add_field(name="LOW", value=len(stock["LOW"]), inline=False)
    embed.add_field(name="MEDIUM", value=len(stock["MEDIUM"]), inline=False)
    embed.add_field(name="HIGH", value=len(stock["HIGH"]), inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def restock(ctx, tier: str):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send("❌ Sem permissão.")

    tier = tier.upper()
    stock = load_json("stock.json")

    if tier not in stock:
        return await ctx.send("❌ Tier inválido.")

    items = ctx.message.content.split("\n")[1:]

    if not items:
        return await ctx.send("❌ Coloque os itens abaixo do comando.")

    for item in items:
        stock[tier].append(item)

    save_json("stock.json", stock)
    backup_files()

    await ctx.send(f"✅ {len(items)} itens adicionados em {tier}")

# ================== ENTREGA ==================

class GenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def process(self, interaction, tier, price):
        credits = load_json("credits.json")
        stock = load_json("stock.json")
        history = load_json("history.json")

        user_id = str(interaction.user.id)

        if credits.get(user_id, 0) < price:
            return await interaction.response.send_message("❌ Créditos insuficientes.", ephemeral=True)

        if len(stock[tier]) == 0:
            return await interaction.response.send_message("❌ Sem estoque.", ephemeral=True)

        item = stock[tier].pop(0)
        credits[user_id] -= price

        history.append({
            "user": str(interaction.user),
            "tier": tier,
            "item": item
        })

        save_json("stock.json", stock)
        save_json("credits.json", credits)
        save_json("history.json", history)

        backup_files()

        try:
            await interaction.user.send(f"🔐 Produto gerado:\n```{item}```")
            await interaction.response.send_message("✅ Enviado no seu privado.", ephemeral=True)
        except:
            await interaction.response.send_message("❌ Ative sua DM.", ephemeral=True)

    @discord.ui.button(label="LOW - 3 créditos", style=discord.ButtonStyle.red)
    async def low(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process(interaction, "LOW", 3)

    @discord.ui.button(label="MEDIUM - 10 créditos", style=discord.ButtonStyle.blurple)
    async def medium(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process(interaction, "MEDIUM", 10)

    @discord.ui.button(label="HIGH - 14 créditos", style=discord.ButtonStyle.green)
    async def high(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process(interaction, "HIGH", 14)

@bot.command()
async def painel(ctx):
    await ctx.send("Escolha o tier:", view=GenView())

# ==================

@bot.event
async def on_ready():
    print(f"Bot online como {bot.user}")

bot.run(TOKEN)