import discord
from discord.ext import commands
import asyncio
import random
import os

# ---- إعدادات البوت الأساسية والصلاحيات الكاملة ----
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

is_paused = False

# ---- الديكوريتور الخاص بحماية الرتب العليا للأوامر العادية ----
def has_allowed_role():
    async def predicate(ctx):
        member_role_names = [role.name for role in ctx.author.roles]
        return any(role in ["*༺ Queen ༻*", "👑 ୨୧ 𝑶𝒘𝒏𝒆𝒓"] for role in member_role_names)
    return commands.check(predicate)

# ==================== الأحداث (Events) ====================

@bot.event
async def on_ready():
    print(f'=== Elysia Bot Is Online ===')
    print(f'Logged in as: {bot.user.name}')
    print(f'============================')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Elysia Community"))

# نظام الترحيب التلقائي بالأعضاء الجدد
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="welcome")
    if channel:
        embed = discord.Embed(
            title="🌸 عضو جديد في ديارنا! 🌸",
            description=f"أهلاً بك يا {member.mention} في سيرفرنا المميز!\nنورتنا بوجودك، أتمنى لك وقتاً ممتعاً معنا.",
            color=discord.Color.from_rgb(255, 182, 193)
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"أنت العضو رقم {len(member.guild.members)}")
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            print("خطأ: البوت لا يملك صلاحية الإرسال في روم الترحيب.")

@bot.event
async def on_message(message):
    global is_paused
    if message.author == bot.user: return
    clean_content = message.content.strip()

    # تحويل الاختصارات ومعالجتها قبل أي قيود
    if clean_content.startswith('!حذف نك'):
        message.content = clean_content.replace('!حذف نك', '!حذف_نك', 1)
    if clean_content.startswith('!ستريك') and len(message.mentions) > 0:
        message.content = clean_content.replace('!ستريك', '!ستريك_منشن', 1)

    member_role_names = [role.name for role in message.author.roles]
    has_admin_privilege = any(r in ["*༺ Queen ༻*", "👑 ୨୧ 𝑶𝒘𝒏𝒆𝒓"] for r in member_role_names)

    # التحكم في وضع السكون
    if clean_content == '-توقيف':
        if has_admin_privilege:
            is_paused = True
            await message.channel.send('💤 البوت الآن في وضع السكون.')
        return
    if clean_content == '-تشغيل':
        if has_admin_privilege:
            is_paused = False
            await message.channel.send('🤖 عدت للعمل يا امبراطورتي!')
        return

    if is_paused: return

    # --- الردود التلقائية والمنشن ---
    if clean_content == '!يا فانزي':
        await message.channel.send('لبيه يا عيوني؟ 🌸')
        return
        
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        await message.channel.send('نعم عزيزتي')
        return
    if clean_content == 'لا تعيديها':
        await message.channel.send('آسفه يا مولاتي')
        return
    if len(clean_content) >= 5 and all(char == 'ه' for char in clean_content):
        await message.channel.send('ترا ما يضحك لا تسلكِ')
        return

    # معالجة الأوامر البريفكس (مهم جداً أن تكون في نهاية الحدث)
    await bot.process_commands(message)

# ==================== الأوامر (Commands) ====================

# 1. أمر النك المحدث
@bot.command()
async def نك(ctx, member: discord.Member = None, *, new_name: str = None):
    if is_paused: return
    member_role_names = [role.name for role in ctx.author.roles]
    has_admin_privilege = any(r in ["*༺ Queen ༻*", "👑 ୨୧ 𝑶𝒘𝒏𝒆𝒓"] for r in member_role_names)
    if not has_admin_privilege:
        await ctx.send("❌ عذراً، هذا الأمر مخصص للإمبراطورة وصاحبات رتب الإدارة العليا فقط!", delete_after=5)
        return
    if member is None or new_name is None:
        await ctx.send("❌ مثال: `!نك @العضوة الاسم الجديد`", delete_after=5)
        return
    try:
        await member.edit(nick=new_name)
        await ctx.send(f"✅ تم تغيير اسم {member.mention} بنجاح إلى: **{new_name}** 👑")
    except discord.Forbidden:
        await ctx.send("❌ ليس لدي صلاحية لتعديل اسم هذه العضوة (تأكدي من رفع رتبة البوت).")
    except Exception as e:
        await ctx.send(f"⚠️ حدث خطأ: {e}")

# 2. أمر حذف النك
@bot.command(name="حذف_نك")
async def remove_nick(ctx, member: discord.Member = None):
    if is_paused: return
    member_role_names = [role.name for role in ctx.author.roles]
    has_admin_privilege = any(r in ["*༺ Queen ༻*", "👑 ୨୧ 𝑶𝒘𝒏𝒆𝒓"] for r in member_role_names)
    if not has_admin_privilege: return
    if member is None: return
    try:
        await member.edit(nick=None)
        await ctx.send(f"✨ تم إزالة اللقب المستعار لـ {member.mention} بنجاح.")
    except Exception as e:
        await ctx.send(f"⚠️ حدث خطأ: {e}")

# 3. أمر ستريك المنشن المخصص
@bot.command(name="ستريك_منشن")
async def streak_mention_command(ctx, member: discord.Member = None, number: str = None):
    if is_paused: return
    member_role_names = [role.name for role in ctx.author.roles]
    has_admin_privilege = any(r in ["*༺ Queen ༻*", "👑 ୨୧ 𝑶𝒘𝒏𝒆𝒓"] for r in member_role_names)
    if not has_admin_privilege: return
    if member is None or number is None: return
    current_base_name = member.nick if member.nick else member.name
    if "🔥" in current_base_name:
        current_base_name = current_base_name.split("🔥")[0].strip()
    new_nickname = f"{current_base_name} 🔥{number}"
    try:
        await member.edit(nick=new_nickname)
        await ctx.send(f"✅ تم تحديث ستريك {member.mention} بنجاح إلى: **{number}** 🔥")
    except Exception as e:
        await ctx.send(f"⚠️ حدث خطأ: {e}")

# 4. كلاس وأمر لعبة الكراسي التفاعلية
class ChairsGameView(discord.ui.View):
    def __init__(self, ctx, players):
        super().__init__(timeout=30.0)
        self.ctx = ctx
        self.players = players.copy()
        self.claimed_players = []
        self.chairs_count = len(self.players) - 1
        self.game_over = False
        for i in range(self.chairs_count):
            btn = discord.ui.Button(label=f"🪑 كرسي {i+1}", style=discord.ButtonStyle.success, custom_id=f"chair_{i}")
            btn.callback = self.make_callback(i)
            self.add_item(btn)

    def make_callback(self, index):
        async def button_callback(interaction: discord.Interaction):
            if interaction.user not in self.players: return
            if interaction.user in self.claimed_players: return
            self.claimed_players.append(interaction.user)
            for item in self.children:
                if item.custom_id == f"chair_{index}":
                    item.disabled = True
                    item.style = discord.ButtonStyle.secondary
                    item.label = f"🔒 محجوز لـ {interaction.user.display_name}"
                    break
            await interaction.response.edit_message(view=self)
            await self.ctx.send(f"💨 {interaction.user.mention} جلست وحجزت كرسيها!")
            if len(self.claimed_players) == self.chairs_count:
                self.stop()
                await self.end_round()
        return button_callback

    async def end_round(self):
        if self.game_over: return
        self.game_over = True
        loser = None
        for p in self.players:
            if p not in self.claimed_players:
                loser = p
                break
        if loser:
            self.players.remove(loser)
            await self.ctx.send(f"💀 **انتهت الجولة!** {loser.mention} تم إقصاؤها! 🚷")
        if len(self.players) == 1:
            await self.ctx.send(f"👑✨ **الفائزة النهائية هي: {self.players[0].mention}!** ✨👑")
        elif len(self.players) > 1:
            await asyncio.sleep(3)
            next_view = ChairsGameView(self.ctx, self.players)
            await self.ctx.send("🎵 **اضغطوا الكراسي المتاحة فورا!**", view=next_view)

    async def on_timeout(self):
        await self.end_round()

@bot.command()
@has_allowed_role()
async def كراسي(ctx):
    if is_paused: return
    await ctx.send("🎵 **لعبة الكراسي الموسيقية بدأت!** 🎵\nاضغطي على زر **(انضمام 🎮)** للمشاركة!")
    registered_players = []
    class JoinView(discord.ui.View):
        def __init__(self): super().__init__(timeout=20.0)
        @discord.ui.button(label="انضمام 🎮", style=discord.ButtonStyle.primary)
        async def join_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user in registered_players: return
            registered_players.append(interaction.user)
            await interaction.response.send_message("✅ تم تسجيلكِ!", ephemeral=True)
    join_view = JoinView()
    msg = await ctx.send("سجلي هنا:", view=join_view)
    await asyncio.sleep(20.0)
    if len(registered_players) < 2:
        await ctx.send("❌ إلغاء، عدد اللاعبين غير كافٍ.")
        return
    first_round_view = ChairsGameView(ctx, registered_players)
    await ctx.send("🪑 **توقفت الموسيقى!! أسرعوا!**", view=first_round_view)

# تشغيل البوت بسحب التوكن بشكل آمن من Railway Variables
TOKEN = os.environ.get("TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("خطأ: لم يتم العثور على متغير TOKEN!")
        
