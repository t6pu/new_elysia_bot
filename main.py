import discord
from discord.ext import commands
import random
import os
import re
import asyncio  # تمت إضافتها للتحكم بالوقت

# إعداد الصلاحيات الكاملة للبوت
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix='!', intents=intents)

# متغير افتراضي لحالة إيقاف الألعاب مؤقتاً
is_paused = False

# --- بيانات الألعاب الافتراضية ---
replica_letters = ["أ", "ب", "ت", "ج", "ح", "خ", "د", "ر", "ز", "س", "ش", "ع", "ف", "ق", "ك", "م", "ن", "هـ", "و", "ي"]
cut_tweets = ["شخص مستحيل ترفضين له طلب؟", "صفة فيكِ تبغين تغيرينها؟", "أكثر شي يعدل مزاجكِ بكلمتين؟", "لو أتيحت لكِ فرصة السفر الآن، وين تروحين؟", "شيء سويتيه وندمتِ عليه لاحقاً؟"]
fast_words = ["سيرفر", "ديسكورد", "فعاليات", "أليسيا", "ملكة", "كراسي", "مافيا"]
guess_country_data = [
    {"image": "https://images.unsplash.com/photo-1543731068-7e0f5beff43a", "answer": "مصر"},
    {"image": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34", "answer": "فرنسا"}
]
flags_data = [
    {"image": "https://flagcdn.com/w640/sa.png", "answer": "السعودية"},
    {"image": "https://flagcdn.com/w640/ae.png", "answer": "الإمارات"}
]

# --- كلاسات لعبة الـ XO الجديدة ---

class XOBoard:
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
        self.board = ["🟩"] * 9
        self.current_turn = p1
        self.winner = None
        self.is_draw = False

    def check_winner(self):
        win_conditions = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
        for c in win_conditions:
            if self.board[c[0]] == self.board[c[1]] == self.board[c[2]] != "🟩":
                self.winner = self.p1 if self.board[c[0]] == "❌" else self.p2
                return self.winner
        if "🟩" not in self.board:
            self.is_draw = True
        return None

class XOPlayView(discord.ui.View):
    def __init__(self, game_match):
        super().__init__(timeout=60)
        self.match = game_match
        for i in range(9):
            button = discord.ui.Button(label=str(i+1), style=discord.ui.ButtonStyle.secondary, row=i//3)
            button.callback = self.make_callback(i)
            self.add_item(button)

    def make_callback(self, index):
        async def callback(interaction: discord.Interaction):
            if interaction.user != self.match.current_turn:
                await interaction.response.send_message("❌ هذا ليس دورك!", ephemeral=True)
                return
            if self.match.board[index] != "🟩":
                await interaction.response.send_message("❌ محجوز!", ephemeral=True)
                return

            mark = "❌" if interaction.user == self.match.p1 else "⭕"
            self.match.board[index] = mark
            self.children[index].label = mark
            self.children[index].style = discord.ui.ButtonStyle.primary if mark == "❌" else discord.ui.ButtonStyle.success
            self.children[index].disabled = True
            
            if self.match.check_winner() or self.match.is_draw:
                for child in self.children: child.disabled = True
                self.stop()
                if not self.match.winner: self.match.winner = random.choice([self.match.p1, self.match.p2])
                await interaction.response.edit_message(content=f"🏁 انتهت! الفائز المتأهل: {self.match.winner.mention}", view=self)
                return

            self.match.current_turn = self.match.p2 if self.match.current_turn == self.match.p1 else self.match.p1
            await interaction.response.edit_message(content=f"اللاعب الحالي: {self.match.current_turn.mention}", view=self)
        return callback

class XOJoinView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)
        self.players = []
    @discord.ui.button(label="انضمام للبطولة 🎮", style=discord.ui.ButtonStyle.blurple)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.players: return await interaction.response.send_message("أنت مسجل بالفعل!", ephemeral=True)
        if len(self.players) >= 30: return await interaction.response.send_message("اكتمل العدد!", ephemeral=True)
        self.players.append(interaction.user)
        await interaction.response.send_message(f"✅ تم انضمامك. العدد الحالي: {len(self.players)}", ephemeral=True)

# --- كود البوت الأساسي ---

@bot.event
async def on_ready():
    print(f'تم تشغيل البوت: {bot.user.name}')

@bot.event
async def on_message(message):
    if message.author == bot.user: return
    user_roles = [role.name for role in message.author.roles] if hasattr(message.author, 'roles') else []
    is_queen = "*༺ Queen ༻*" in user_roles
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        await message.channel.send("نعم عزيزتي" if not is_queen else f"{message.author.mention} لبيه ينبضي آمريني")
        return
    if re.search(r'^ه{3,}$', message.content.strip()):
        await message.channel.send("لا تسلكِ مافي شي يضحك")
        return
    await bot.process_commands(message)

# --- الأوامر ---

@bot.command()
async def اوامر(ctx):
    if "*༺ Queen ༻*" not in [role.name for role in ctx.author.roles]: return
    await ctx.send("👑 **قائمة الأوامر المتاحة:**\n`!حذف`, `!نك`, `!حذف نك`, `!ستريك`, `!يا فانزي`\n🎮 **الألعاب:** `!مافيا`, `!روليت`, `!ريبلكا`, `!لغم`, `!xo`, `!خمن`, `!اعلام`, `!نرد`, `!تويت`, `!اسرع`")

@bot.command(name="xo")
async def xo_tournament(ctx):
    if is_paused: return
    view = XOJoinView()
    msg = await ctx.send("🏆 **فتح التسجيل للبطولة (30 ثانية):**\nاضغط للإنضمام (من 2 إلى 30 لاعب).", view=view)
    await asyncio.sleep(30)
    view.stop()
    if len(view.players) < 2: return await ctx.send("❌ لا يوجد لاعبون كافون.")
    
    players = view.players
    round_num = 1
    while len(players) > 1:
        random.shuffle(players)
        bye = players.pop() if len(players) % 2 != 0 else None
        matches = [XOBoard(players[i], players[i+1]) for i in range(0, len(players), 2)]
        
        await ctx.send(f"⚔️ **الجولة {round_num}:** " + ", ".join([f"{m.p1.name} vs {m.p2.name}" for m in matches]))
        
        next_round = []
        if bye: next_round.append(bye)
        for m in matches:
            play_view = XOPlayView(m)
            await ctx.send(f"مباراة {m.p1.mention} ضد {m.p2.mention}", view=play_view)
            await play_view.wait()
            next_round.append(m.winner)
        players = next_round
        round_num += 1
    await ctx.send(f"👑 **البطل النهائي هو:** {players[0].mention} مبارك!")

@bot.command(name="حذف")
@commands.has_permissions(manage_messages=True)
async def delete_messages(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"✅ تم حذف {amount} رسالة.", delete_after=3)

@bot.command(name="نك")
async def change_nickname(ctx, member: discord.Member, *, new_name: str):
    try: await member.edit(nick=new_name); await ctx.send("✅")
    except: await ctx.send("❌")

@bot.command(name="حذف_نك")
async def remove_nickname(ctx, member: discord.Member):
    try: await member.edit(nick=None); await ctx.send("✅")
    except: await ctx.send("❌")

@bot.command(name="ستريك")
async def set_streak_name(ctx, member: discord.Member, streak_count: int):
    if "*༺ Queen ༻*" in [r.name for r in ctx.author.roles] or "୨୧ 𝑶𝒘𝒏𝒆𝒓" in [r.name for r in ctx.author.roles]:
        base = (member.nick or member.name).split(" [")[0]
        await member.edit(nick=f"{base} [{streak_count} 🔥]")
        await ctx.send("🔥 تم.")

@bot.command(name='يا')
async def ya(ctx, *, arg=None):
    if arg == 'فانزي': await ctx.send("لبيه يا عيوني؟ 🌸")

@bot.command()
async def العاب(ctx):
    await ctx.send("🎮 **قائمة الألعاب:** `!مافيا`, `!روليت`, `!ريبلكا`, `!لغم`, `!xo`, `!خمن`, `!اعلام`, `!نرد`, `!تويت`, `!اسرع`")

@bot.command()
async def مافيا(ctx): await ctx.send("🎲 جاري توزيع الأدوار...")

@bot.command()
async def روليت(ctx): await ctx.send(f"🔫 {random.choice(['💥 خسرت', '🔒 نجوت'])}")

@bot.command()
async def ريبلكا(ctx): await ctx.send(f"📝 الحرف هو: **{random.choice(replica_letters)}**")

@bot.command()
async def لغم(ctx): await ctx.send(f"💣 النتيجة: {random.choice(['آمن', 'آمن', 'انفجر!'])}")

@bot.command()
async def خمن(ctx):
    place = random.choice(guess_country_data)
    embed = discord.Embed(title="🗺️ خمن الدولة").set_image(url=place["image"])
    await ctx.send(embed=embed)

@bot.command()
async def اعلام(ctx):
    flag = random.choice(flags_data)
    embed = discord.Embed(title="🏴 خمن العلم").set_image(url=flag["image"])
    await ctx.send(embed=embed)

@bot.command()
async def نرد(ctx): await ctx.send(f"🎲 المجموع: {random.randint(1, 6) + random.randint(1, 6)}")

@bot.command(name="تويت")
async def tweet_game(ctx): await ctx.send(f"💬 {random.choice(cut_tweets)}")

@bot.command(name="اسرع")
async def fast_game(ctx):
    word = random.choice(fast_words)
    await ctx.send(f"⚡ اكتب الكلمة مقلوبة: **{word[::-1]}**")

# تشغيل البوت
token = os.getenv("TOKEN")
if token: bot.run(token)
               
