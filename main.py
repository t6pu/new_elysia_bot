import discord
from discord.ext import commands
import random
import os
import re
import asyncio

# إعداد الصلاحيات الكاملة للبوت
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix='!', intents=intents)

# متغير افتراضي لحالة إيقاف الألعاب مؤقتاً
is_paused = False

# --- بيانات الألعاب الافتراضية لمنع الأخطاء البرمجية ---
replica_letters = ["أ", "ب", "ت", "ج", "ح", "خ", "د", "ر", "ز", "س", "ش", "ع", "ف", "ق", "ك", "م", "ن", "هـ", "و", "ي"]
cut_tweets = [
    "شخص مستحيل ترفضين له طلب؟",
    "صفة فيكِ تبغين تغيرينها؟",
    "أكثر شي يعدل مزاجكِ بكلمتين؟",
    "لو أتيحت لكِ فرصة السفر الآن، وين تروحين؟",
    "شيء سويتيه وندمتِ عليه لاحقاً؟"
]
fast_words = ["سيرفر", "ديسكورد", "فعاليات", "أليسيا", "ملكة", "كراسي", "مافيا"]
guess_country_data = [
    {"image": "https://images.unsplash.com/photo-1543731068-7e0f5beff43a", "answer": "مصر"},
    {"image": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34", "answer": "فرنسا"}
]
flags_data = [
    {"image": "https://flagcdn.com/w640/sa.png", "answer": "السعودية"},
    {"image": "https://flagcdn.com/w640/ae.png", "answer": "الإمارات"}
]

# --- نظام كلاسات لعبة بطولة الـ XO بالأزرار ---

class XOBoard:
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
        self.board = ["🟩"] * 9
        self.current_turn = p1
        self.winner = None
        self.is_draw = False

    def check_winner(self):
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # أفقياً
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # عمودياً
            (0, 4, 8), (2, 4, 6)              # قطرياً
        ]
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
                await interaction.response.send_message("❌ هذا ليس دوركِ الحالي!", ephemeral=True)
                return
            if self.match.board[index] != "🟩":
                await interaction.response.send_message("❌ هذا المربع مأخوذ بالفعل!", ephemeral=True)
                return

            mark = "❌" if interaction.user == self.match.p1 else "⭕"
            self.match.board[index] = mark
            self.children[index].label = mark
            self.children[index].style = discord.ui.ButtonStyle.primary if mark == "❌" else discord.ui.ButtonStyle.success
            self.children[index].disabled = True

            self.match.check_winner()

            if self.match.winner or self.match.is_draw:
                for child in self.children:
                    child.disabled = True
                self.stop()
                if not self.match.winner:
                    self.match.winner = random.choice([self.match.p1, self.match.p2])
                
                embed = discord.Embed(
                    title="🏁 انتهاء المباراة!",
                    description=f"المواجهة بين: {self.match.p1.mention} ضد {self.match.p2.mention}\n\n🏆 الفائز المتأهل: {self.match.winner.mention}!",
                    color=discord.Color.green()
                )
                await interaction.response.edit_message(embed=embed, view=self)
                return

            self.match.current_turn = self.match.p2 if self.match.current_turn == self.match.p1 else self.match.p1
            embed = discord.Embed(
                title="⚔️ مباراة XO نشطة ⚔️",
                description=f"❌ لاعب 1: {self.match.p1.mention}\n⭕ لاعب 2: {self.match.p2.mention}\n\n🚨 الدور الحالي: {self.match.current_turn.mention}",
                color=discord.Color.blue()
            )
            await interaction.response.edit_message(embed=embed, view=self)
        return callback

class XOJoinView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)
        self.players = []

    @discord.ui.button(label="انضمام للبطولة 🎮", style=discord.ui.ButtonStyle.blurple)
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.players:
            await interaction.response.send_message("❌ أنتِ مسجلة بالفعل!", ephemeral=True)
            return
        if len(self.players) >= 30:
            await interaction.response.send_message("❌ اكتمل الحد الأقصى (30 لاعب)!", ephemeral=True)
            return
        self.players.append(interaction.user)
        await interaction.response.send_message(f"✅ تم تسجيلكِ! المشتركين الآن: {len(self.players)}", ephemeral=True)

# --- أحداث البوت الفلاتر والردود التلقائية ---

@bot.event
async def on_ready():
    print(f'تم تشغيل البوت بنجاح باسم: {bot.user.name}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # جلب أسماء رتب العضو المرسل بشكل آمن لمنع الأخطاء في الخاص
    user_roles = [role.name for role in message.author.roles] if hasattr(message.author, 'roles') else []
    is_queen = "*༺ Queen ༻*" in user_roles

    # 1. رد المنشن الخاص برتبة الملكة فقط
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        if is_queen:
            await message.channel.send(f"{message.author.mention} لبيه ينبضي آمريني")
            return
        else:
            await message.channel.send("نعم عزيزتي")
            return

    # 2. رد "لا تعيدها" الخاص برتبة الملكة فقط
    if message.content.strip() == "لا تعيدها":
        if is_queen:
            await message.channel.send("آسف يا روحي")
            return

    # 3. فلتر الضحك والتسليك (ههههه إلى ما لا نهاية)
    if re.search(r'^[هـ]{3,}$', message.content.strip()):
        await message.channel.send("لا تسلكِ مافي شي يضحك")
        return

    # هام جداً: معالجة الأوامر دائماً لضمان عدم تعليق البوت!
    await bot.process_commands(message)

# --- الأوامر الإدارية والتحكم ---

# أمر قائمة الأوامر (محمي بالكامل لـ Queen فقط)
@bot.command(name="اوامر")
async def اوامر_queen(ctx):
    user_roles = [role.name for role in ctx.author.roles]
    if "*༺ Queen ༻*" not in user_roles:
        return  # تجاهل تام لغير رتبة الكوين

    help_text = (
        "👑 **قائمة جميع أوامر البوت المتاحة للـ Queen:**\n\n"
        "✨ **أوامر عامة وخاصة:**\n"
        "`!اوامر` ⇦ عرض هذه القائمة (للملكة فقط).\n"
        "`!حذف (عدد)` ⇦ حذف عدد معين من الرسائل.\n"
        "`!نك @منشن الاسم` ⇦ تغيير نك نيم العضو.\n"
        "`!حذف نك @منشن` ⇦ إزالة النك نيم وإعادته للافتراضي.\n"
        "`!ستريك @منشن (عدد)` ⇦ وضع رقم الستريك بجانب الاسم مع 🔥.\n"
        "`!يا فانزي` ⇦ رد ترحيبي.\n\n"
        "🎮 **أوامر الألعاب المتاحة (`!العاب`):**\n"
        "`!كراسي` | `!مافيا` | `!روليت` | `!ريبلكا` | `!لغم` | `!xo` | `!خمن` | `!اعلام` | `!نرد` | `!تويت` | `!اسرع`"
    )
    await ctx.send(help_text)

# أمر الحذف بالعدد
@bot.command(name="حذف")
@commands.has_permissions(manage_messages=True)
async def delete_messages(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"✅ تم حذف {amount} رسالة بنجاح.", delete_after=3)

# أمر تغيير اللقب (!نك @منشن الاسم)
@bot.command(name="نك")
async def change_nickname(ctx, member: discord.Member, *, new_name: str):
    try:
        await member.edit(nick=new_name)
        await ctx.send(f"✅ تم تعديل نك نيم {member.mention} إلى: **{new_name}**")
    except discord.Forbidden:
        await ctx.send("❌ لا أملك صلاحية تعديل اللقب لهذا الشخص.")

# أمر حذف اللقب (!حذف نك @منشن)
@bot.command(name="حذف_نك", aliases=["حذف نك"])
async def remove_nickname(ctx, member: discord.Member):
    try:
        await member.edit(nick=None)
        await ctx.send(f"✅ تم إزالة النك نيم لـ {member.mention}.")
    except discord.Forbidden:
        await ctx.send("❌ لا أملك صلاحية إزالة اللقب لهذا الشخص.")

# أمر تعديل الستريك بجانب الاسم (محمي للملكة والـ Owner)
@bot.command(name="ستريك")
async def set_streak_name(ctx, member: discord.Member, streak_count: int):
    user_roles = [role.name for role in ctx.author.roles]
    if "*༺ Queen ༻*" in user_roles or "୨୧ 𝑶𝒘𝒏𝒆𝒓" in user_roles:
        try:
            current_nick = member.nick if member.nick else member.name
            base_name = current_nick.split(" [")[0].strip()
            new_nick = f"{base_name} [{streak_count} 🔥]"
            await member.edit(nick=new_nick)
            await ctx.send(f"🔥 تم وضع الستريك لـ {member.mention} بجانب الاسم: **{new_nick}**")
        except discord.Forbidden:
            await ctx.send("❌ فشل تعديل الاسم، يرجى رفع رتبة البوت وتفعيل صلاحية إدارة الأسماء.")
    else:
        await ctx.send("🔒 عذراً عزيزتي، هذا الأمر مخصص فقط لـ إدارة السيرفر العليا والملكة.")

# أمر يا فانزي
@bot.command(name='يا')
async def ya(ctx, *, arg=None):
    if arg == 'فانزي':
        await ctx.send("لبيه يا عيوني؟ 🌸")

# --- أوامر الألعاب بالكامل ---

@bot.command(name="العاب")
async def العاب(ctx):
    if is_paused: return
    embed = discord.Embed(
        title="🎮 قـائـمـة الألـعـاب الـمـتـاحـة فـي الـسـيرفـر 🎮",
        description="استخدم البادئة (!) قبل اسم اللعبة لبدء اللعب فوراً مَع طاقم السيرفر والأعضاء!",
        color=discord.Color.purple()
    )
    embed.add_field(name="🕵️‍♂️ !مافيا", value="بدء سحب قرعة أدوار المافيا عشوائياً بين الأعضاء المتواجدين.", inline=True)
    embed.add_field(name="🔫 !روليت", value="تحدي الحظ الروسي (إقصاء أو نجاة عشوائية).", inline=True)
    embed.add_field(name="📝 !ريبلكا", value="يعطيكِ حرف عشوائي لتبدأوا لعبة (إنسان، حيوان، نبات...).", inline=True)
    embed.add_field(name="💣 !لغم", value="اختبر حظك واختر مربعاً لتتفادى الألغام الكامنة.", inline=True)
    embed.add_field(name="❌ !xo", value="بطولة الـ XO الاستراتيجية الكبرى بالأزرار وتصفيات بين المشتركين.", inline=True)
    embed.add_field(name="🗺️ !خمن", value="يعرض صورة لمعلم شهير في بلد ما، وعليكِ تخمين الدولة.", inline=True)
    embed.add_field(name="🏴 !اعلام", value="يعرض علم دولة عشوائي وعليكِ معرفة اسم الدولة بسرعة.", inline=True)
    embed.add_field(name="🎲 !نرد", value="رمي النرد واستخراج أرقام الحظ العشوائية.", inline=True)
    embed.add_field(name="💬 !تويت", value="لعبة كت تويت الشهيرة (أسئلة واعترافات للسيرفر).", inline=True)
    embed.add_field(name="⚡ !اسرع", value="لعبة السرعة، يظهر البوت كلمة وعليك كتابتها أولاً.", inline=True)
    embed.set_footer(text="Elysia Community Bot ୨୧")
    await ctx.send(embed=embed)

@bot.command(name="xo")
async def xo_tournament(ctx):
    if is_paused: return
    view = XOJoinView()
    embed = discord.Embed(
        title="🏆 فتح التسجيل في بطولة الـ XO الجماعية 🏆",
        description="اضغطي على الزر بالأسفل للانضمام إلى قائمة التحدي المباشر!\n\n⏳ **الوقت المتاح للتسجيل:** 30 ثانية فقط.\n👥 **العدد المسموح:** من 2 إلى 30 لاعب كحد أقصى.",
        color=discord.Color.purple()
    )
    init_msg = await ctx.send(embed=embed, view=view)
    await asyncio.sleep(30)
    view.stop()

    players_list = view.players
    if len(players_list) < 2:
        await ctx.send("❌ لم ينضم عدد كافٍ من اللاعبين لبدء البطولة (أقل حد لاعبين).")
        return

    round_num = 1
    while len(players_list) > 1:
        random.shuffle(players_list)
        bye_player = players_list.pop() if len(players_list) % 2 != 0 else None

        schedule_text = f"📋 **جدول مواجهات الـ XO الحالية - الجولة [{round_num}]:**\n\n"
        matches = []
        for i in range(0, len(players_list), 2):
            p1, p2 = players_list[i], players_list[i+1]
            matches.append(XOBoard(p1, p2))
            schedule_text += f"⚔️ مباراة: {p1.mention} **Vs** {p2.mention}\n"
        if bye_player:
            schedule_text += f"✨ تأهل تلقائي بهذه الجولة: {bye_player.mention}\n"

        await ctx.send(embed=discord.Embed(title=f"⚔️ انطلاق الجولة {round_num} ⚔️", description=schedule_text, color=discord.Color.gold()))
        await asyncio.sleep(4)

        next_round_players = []
        if bye_player:
            next_round_players.append(bye_player)

        for idx, match in enumerate(matches):
            round_embed = discord.Embed(
                title=f"🎯 المباراة [{idx + 1}] بدأت الآن!",
                description=f"❌ لاعب 1: {match.p1.mention}\n⭕ لاعب 2: {match.p2.mention}\n\n🚨 الدور الحالي: {match.p1.mention}",
                color=discord.Color.blue()
            )
            play_view = XOPlayView(match)
            await ctx.send(embed=round_embed, view=play_view)
            await play_view.wait()
            next_round_players.append(match.winner)
            await asyncio.sleep(3)

        players_list = next_round_players
        round_num += 1

    await ctx.send(embed=discord.Embed(
        title="👑 بـطـل الـسـيـرفـر الـنـهـائـي 👑",
        description=f"🎉 ألف مبروك الفوز ببطولة الـ XO الكبرى للاعب:\n\n🏆  {players_list[0].mention}  🏆\n\nلقد تفوقتِ على الجميع بجدارة! ✨🔥",
        color=discord.Color.from_rgb(255, 215, 0)
    ))

@bot.command()
async def مافيا(ctx):
    if is_paused: return
    await ctx.send("🎲 **جاري توزيع أدوار لعبة المافيا عشوائياً على الروم الحالي...**\nتم اختيار الأدوار الأساسية لهذه الجولة بنجاح!")

@bot.command()
async def روليت(ctx):
    if is_paused: return
    outcomes = ["💥 *طخخخ! لقد خسرتِ في الروليت الحتمية وجاءت الرصاصة فيكِ!*", "🔒 *نجاة! مرت الرصاصة بسلام ولم يصيبكِ مكروه هذه المرة.*"]
    await ctx.send(f"🔫 {ctx.author.mention} يقوم بسحب زناد الروليت الروسية...\n\n{random.choice(outcomes)}")

@bot.command()
async def ريبلكا(ctx):
    if is_paused: return
    await ctx.send(f"📝 **لعبة ريبليكا:**\n> الحرف المختار لهذه الجولة هو: **[ {random.choice(replica_letters)} ]**")

@bot.command()
async def لغم(ctx):
    if is_paused: return
    choice = random.choice(["🟩 آمن", "🟩 آمن", "💣 لـغـم انفجر!"])
    await ctx.send(f"💣 **لقد خطوتِ خطوة في ساحة الألغام:**\n> النتيجة: {choice}")

@bot.command()
async def خمن(ctx):
    if is_paused: return
    place = random.choice(guess_country_data)
    embed = discord.Embed(title="🗺️ خمني الدولة التي يوجد بها هذا المعلم الشهير؟", color=discord.Color.blue())
    embed.set_image(url=place["image"])
    await ctx.send(embed=embed)

@bot.command()
async def اعلام(ctx):
    if is_paused: return
    flag = random.choice(flags_data)
    embed = discord.Embed(title="🏴 ما هي الدولة صاحبة هذا العلم؟", color=discord.Color.orange())
    embed.set_image(url=flag["image"])
    await ctx.send(embed=embed)

@bot.command()
async def نرد(ctx):
    if is_paused: return
    d1, d2 = random.randint(1, 6), random.randint(1, 6)
    await ctx.send(f"🎲 لقد رميتِ أحجار النرد:\n> الحجر الأول: **{d1}** | الثاني: **{d2}**\n✨ المجموع: **{d1 + d2}**")

@bot.command(name="تويت")
async def tweet_game(ctx):
    if is_paused: return
    await ctx.send(f"💬 **كت تويت الفعاليات:**\n> {random.choice(cut_tweets)}")

@bot.command(name="اسرع")
async def fast_game(ctx):
    if is_paused: return
    word = random.choice(fast_words)
    await ctx.send(f"⚡ **أسرع واحدة تكتب الكلمة التالية صحيحة تفوز:**\n> الكلمة المقلوبة هي: **{word[::-1]}**")

# تشغيل البوت عبر التوكن المخزن في Railway
token = os.getenv("TOKEN")
if token:
    bot.run(token)
                    
