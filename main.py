import discord
from discord.ext import commands
import random
import os
import re

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
    "لو أتيحت لكِ فرصة السفر الآن، وين تروحين？",
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

@bot.event
async def on_ready():
    print(f'تم تشغيل البوت بنجاح باسم: {bot.user.name}')

# --- نظام الفلاتر والردود الذكية في on_message ---
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # فحص الرتب الخاصة بالمستخدم
    user_roles = [role.name for role in message.author.roles] if hasattr(message.author, 'roles') else []
    is_queen = "*༺ Queen ༻*" in user_roles

    # تنظيف الرسالة للتحقق بدقة
    cleaned_msg = message.content.strip()

    # 1. رد السلام عليكم بالتعديل المطلوب وحروف الترحيب الزائدة للملكة والسيرفر
    if cleaned_msg in ["السلام عليكم", "السلام عليكم ورحمة الله وبركاته"]:
        await message.channel.send("وعليكم السلام ورحمة الله وبركاته ااارررحححبببييي تتتررراااحححيييببب اااللممططررر و ااالللسسسيييللل و ااالللهههيييللل ااارررحححبببييي تتتررراااحححيييبببب ااالللمممطططررر يااا ااالللكككووويييننن")
        return

    # 2. رد المنشن الخاص برتبة الملكة فقط
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        if is_queen:
            await message.channel.send(f"{message.author.mention} لبيه ينبضي آمريني")
            return
        else:
            await message.channel.send("نعم عزيزتي")
            return

    # 3. رد أمر "لا تعيدها" الخاص برتبة الملكة فقط
    if cleaned_msg == "لا تعيدها":
        if is_queen:
            await message.channel.send("آسف يا روحي")
            return

    # 4. فلتر الضحك والتسليك (ههههه إلى ما لا نهاية)
    if re.search(r'^ه{3,}$', cleaned_msg):
        await message.channel.send("لا تسلكِ مافي شي يضحك")
        return

    await bot.process_commands(message)

# --- أوامر التحكم والمميزات الجديدة ---

# 1. أمر قائمة الأوامر (محمي لرتبة الملكة فقط)
@bot.command()
async def اوامر(ctx):
    user_roles = [role.name for role in ctx.author.roles]
    if "*༺ Queen ༻*" not in user_roles:
        return  # يتجاهل الأمر تماماً ولا يستجيب لغير الملكة
        
    help_text = (
        "👑 **قائمة جميع أوامر البوت المتاحة للـ Queen:**\n\n"
        "✨ **أوامر عامة وخاصة:**\n"
        "`!اوامر` ⇦ عرض هذه القائمة (للملكة فقط).\n"
        "`!حذف (عدد)` ⇦ حذف عدد معين من الرسائل.\n"
        "`!نك @منشن الاسم` ⇦ تغيير نك نيم العضو.\n"
        "`!حذف نك @منشن` ⇦ إزالة النك نيم وإعادته للافتراضي.\n"
        "`ستريك @منشن (عدد)` ⇦ وضع رقم الستريك بجانب الاسم مع 🔥.\n"
        "`!يا فانزي` ⇦ رد ترحيبي.\n\n"
        "🎮 **أوامر الألعاب المتاحة (`!العاب`):**\n"
        "`!كراسي` | `!مافيا` | `!روليت` | `!ريبلكا` | `!لغم` | `!xo` | `!خمن` | `!اعلام` | `!نرد` | `!تويت` | `!اسرع`"
    )
    await ctx.send(help_text)

# 2. أمر حذف الرسائل بالعدد
@bot.command(name="حذف")
@commands.has_permissions(manage_messages=True)
async def delete_messages(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"✅ تم حذف {amount} رسالة بنجاح.", delete_after=3)

# 3. أمر تغيير النك نيم ( !نك @منشن الاسم الجديد )
@bot.command(name="نك")
async def change_nickname(ctx, member: discord.Member, *, new_name: str):
    try:
        await member.edit(nick=new_name)
        await ctx.send(f"✅ تم تعديل نك نيم {member.mention} إلى: **{new_name}**")
    except discord.Forbidden:
        await ctx.send("❌ لا أملك صلاحية تعديل اللقب لهذا الشخص.")

# 4. أمر حذف النك نيم ( !حذف نك @منشن )
@bot.command(name="حذف_نك", aliases=["حذف نك"])
async def remove_nickname(ctx, member: discord.Member):
    try:
        await member.edit(nick=None)
        await ctx.send(f"✅ تم إزالة النك نيم لـ {member.mention} وإعادته للاسم الأصلي.")
    except discord.Forbidden:
        await ctx.send("❌ لا أملك صلاحية إزالة اللقب لهذا الشخص.")

# 5. أمر إعطاء الستريك بجانب الاسم ( محمي للرتبتين المذكورتين )
@bot.command(name="ستريك")
async def set_streak_name(ctx, member: discord.Member, streak_count: int):
    user_roles = [role.name for role in ctx.author.roles]
    # التحقق من وجود إحدى الرتبتين المسموح لهما بالأمر
    if "*༺ Queen ༻*" in user_roles or "୨୧ 𝑶𝒘𝒏𝒆𝒓" in user_roles:
        try:
            # تنظيف الاسم القديم من أي ستريك سابق إن وجد عبر قراءة الجزء الأول قبل الفاصل
            current_nick = member.nick if member.nick else member.name
            base_name = current_nick.split(" [")[0].strip()
            
            # تركيب الاسم الجديد مع الستريك والإيموجي
            new_nick = f"{base_name} [{streak_count} 🔥]"
            await member.edit(nick=new_nick)
            await ctx.send(f"🔥 تم وضع الستريك لـ {member.mention} بنجاح ومزامنته بجانب الاسم: **{new_nick}**")
        except discord.Forbidden:
            await ctx.send("❌ فشل تعديل الاسم، يرجى رفع رتبة البوت أعلى من العضو وتفعيل صلاحية (تغيير الأسماء المستعارة).")
    else:
        await ctx.send("🔒 عذراً عزيزتي، هذا الأمر مخصص فقط لـ إدارة السيرفر العليا والملكة.")

# 6. أمر يا فانزي
@bot.command(name='يا')
async def ya(ctx, *, arg=None):
    if arg == 'فانزي':
        await ctx.send("لبيه يا عيوني؟ 🌸")

# تشغيل البوت عبر التوكن المخزن في Railway
token = os.getenv("TOKEN")
if token:
    bot.run(token)
else:
    print("خطأ: لم يتم العثور على متغير TOKEN في إعدادات Railway!")
    
