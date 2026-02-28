import discord
from discord.ext import commands
import json
import os
import shutil
from datetime import datetime

TOKEN = os.getenv("wMTQ3NzA2NzAzOTg0MjYzNTg1OA.GPHSSv.PF26lbGzEzVwVpcPX8rh0ogjawP82mt9_lqrG0")

ALERT_ROLE_ID =1477373729486147634
ALERT_CHANNEL_ID =1477368909945503846

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= FILE SYSTEM =================

def load_json(filename):
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            json.dump({}, f)
    with open(filename, "r") as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

def backup_files():
    shutil.copy("stock.json", "backup_stock.json")
    shutil.copy("sales.json", "backup_sales.json")

def is_admin(ctx):
    return ctx.author.guild_permissions.administrator

# ================= INITIAL SETUP =================

if not os.path.exists("stock.json"):
    save_json("stock.json", {
        "LOW": [],
        "MEDIUM": [],
        "HIGH": []
    })

if not os.path.exists("sales.json"):
    save_json("sales.json", [])

# ================= RESTOCK ALERT =================

async def send_restock_alert(ctx, tier, total):
    channel = bot.get_channel(ALERT_CHANNEL_ID)
    if not channel:
        return

    role = ctx.guild.get_role(ALERT_ROLE_ID)
    if not role:
        return

    embed = discord.Embed(
        title="🚨 STOCK UPDATED",
        description=f"**{tier}** has been restocked!",
        color=discord.Color.green()
    )

    embed.add_field(name="Available Now", value=total)
    embed.set_footer(text="Automated Stock System")

    await channel.send(role.mention, embed=embed)

# ================= STORE VIEW =================

class StoreView(discord.ui.View):
    def __init__(self, message=None):
        super().__init__(timeout=None)
        self.message = message

    async def update_panel(self):
        stock = load_json("stock.json")

        embed = discord.Embed(
            title="💎 VIPER GEN STORE",
            description="Click a button below to generate instantly.",
            color=discord.Color.from_rgb(25, 25, 25)
        )

        embed.add_field(
            name="🔴 LOW",
            value=f"3 Credits\nStock: {len(stock['LOW'])}",
            inline=False
        )

        embed.add_field(
            name="🔵 MEDIUM",
            value=f"10 Credits\nStock: {len(stock['MEDIUM'])}",
            inline=False
        )

        embed.add_field(
            name="🟢 HIGH",
            value=f"14 Credits\nStock: {len(stock['HIGH'])}",
            inline=False
        )

        embed.set_footer(text="Instant • Automated • Secure")

        await self.message.edit(embed=embed, view=self)

    async def process_purchase(self, interaction, tier):
        stock = load_json("stock.json")
        sales = load_json("sales.json")

        if len(stock[tier]) == 0:
            return await interaction.response.send_message(
                "❌ Out of stock.", ephemeral=True)

        item = stock[tier].pop(0)
        save_json("stock.json", stock)

        sales.append({
            "user": str(interaction.user),
            "id": interaction.user.id,
            "tier": tier,
            "item": item,
            "date": str(datetime.now())
        })

        save_json("sales.json", sales)
        backup_files()

        try:
            await interaction.user.send(
                f"🎉 Your {tier} account:\n```{item}```"
            )
        except:
            return await interaction.response.send_message(
                "❌ Enable your DMs.", ephemeral=True)

        await interaction.response.send_message(
            f"✅ {tier} delivered to your DM.", ephemeral=True)

        await self.update_panel()

    @discord.ui.button(label="LOW • 3", style=discord.ButtonStyle.danger)
    async def low(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_purchase(interaction, "LOW")

    @discord.ui.button(label="MEDIUM • 10", style=discord.ButtonStyle.primary)
    async def medium(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_purchase(interaction, "MEDIUM")

    @discord.ui.button(label="HIGH • 14", style=discord.ButtonStyle.success)
    async def high(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_purchase(interaction, "HIGH")

# ================= DEPLOY PANEL =================

@bot.command()
async def deploypanel(ctx):
    if not is_admin(ctx):
        return await ctx.send("❌ Admin only command.")

    stock = load_json("stock.json")

    embed = discord.Embed(
        title="💎 VIPER GEN STORE",
        description="Click a button below to generate instantly.",
        color=discord.Color.from_rgb(25, 25, 25)
    )

    embed.add_field(name="🔴 LOW", value=f"3 Credits\nStock: {len(stock['LOW'])}", inline=False)
    embed.add_field(name="🔵 MEDIUM", value=f"10 Credits\nStock: {len(stock['MEDIUM'])}", inline=False)
    embed.add_field(name="🟢 HIGH", value=f"14 Credits\nStock: {len(stock['HIGH'])}", inline=False)

    embed.set_footer(text="Instant • Automated • Secure")

    view = StoreView()
    message = await ctx.send(embed=embed, view=view)
    view.message = message

# ================= RESTOCK =================

@bot.command()
async def restock(ctx, tier: str):
    if not is_admin(ctx):
        return await ctx.send("❌ Admin only command.")

    tier = tier.upper()
    stock = load_json("stock.json")

    if tier not in stock:
        return await ctx.send("❌ Invalid tier.")

    items = ctx.message.content.split("\n")[1:]

    if not items:
        return await ctx.send("❌ Add items below the command.")

    for item in items:
        stock[tier].append(item)

    save_json("stock.json", stock)
    backup_files()

    total = len(stock[tier])

    await send_restock_alert(ctx, tier, total)

    await ctx.send(f"✅ Added {len(items)} items to {tier}")

# ================= SALES HISTORY =================

@bot.command()
async def saleshistory(ctx):
    if not is_admin(ctx):
        return await ctx.send("❌ Admin only command.")

    sales = load_json("sales.json")

    if not sales:
        return await ctx.send("No sales recorded.")

    embed = discord.Embed(title="📊 Sales History", color=discord.Color.gold())

    for sale in sales[-10:]:
        embed.add_field(
            name=f"{sale['tier']} - {sale['user']}",
            value=sale["date"],
            inline=False
        )

    await ctx.send(embed=embed)

# ================= PURCHASE HISTORY =================

@bot.command()
async def purchasehistory(ctx, member: discord.Member):
    if not is_admin(ctx):
        return await ctx.send("❌ Admin only command.")

    sales = load_json("sales.json")
    user_sales = [s for s in sales if s["id"] == member.id]

    if not user_sales:
        return await ctx.send("No purchases found.")

    embed = discord.Embed(
        title=f"🛒 Purchase History - {member}",
        color=discord.Color.orange()
    )

    for sale in user_sales:
        embed.add_field(
            name=sale["tier"],
            value=sale["date"],
            inline=False
        )

    await ctx.send(embed=embed)

# ================= READY =================

@bot.event
async def on_ready():
    print(f"Bot running as {bot.user}")

bot.run(TOKEN)




