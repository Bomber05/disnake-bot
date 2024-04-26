import disnake
import random
from disnake.ext import commands
import sqlite3

user_levels = {}

bot = commands.Bot(command_prefix='!', intents=disnake.Intents.all())

forbidden_words = ['лох', 'дурак', 'какашка', 'тупой']#запрещенные слова при которых бот выдает предупреждение и удаляет сообщение с этим словом
#база данных с предупреждениями
connection = sqlite3.connect('warnings.db')
cursor = connection.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS warnings (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    warnings INTEGER
                )''')
connection.commit()

#база данных с монетами
connect = sqlite3.connect('coins.db')
curso = connect.cursor()

curso.execute('''CREATE TABLE IF NOT EXISTS coins (
                    user_id INTEGER PRIMARY KEY,
                    coins INTEGER
                )''')
connect.commit()
# база данных с лвлами
conne = sqlite3.connect('levels.db')
curs = conne.cursor()

curs.execute('''CREATE TABLE IF NOT EXISTS levels (
                    user_id INTEGER PRIMARY KEY,
                    level INTEGER
                )''')
conne.commit()

#функция которая при нажатие на реакцию выдает рол для общения в чате
@bot.event
async def on_raw_reaction_add(payload):
    if payload.channel_id == 1225495581590421565 and payload.message_id == 1225496162811777074:
        guild = bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        role = guild.get_role(1225497401079500800)

        if member and role:
            await member.add_roles(role)
            print(
                f"Выдана роль {role.name} пользователю {member.display_name}"
            )
        else:
            print(
                "Пользователь или роль не найдены."
            )

#оповещение о том что бот работает и ник бота
@bot.event
async def on_ready():
    print('Бот готов к работе')
    print(f'Запущен как: {bot.user}')


@bot.command()
async def hello(ctx):
    await ctx.send(
        'Привет! Единственное правило на сервере это не матерится!'
    )

#функция которая выдает информацию о пользователе
@bot.command()
async def userinfo(ctx, member: disnake.Member = None):
    member = member or ctx.author

    embed = disnake.Embed(
        title="Информация о пользователе:", color=0x800080
    )
    embed.set_thumbnail(url=member.avatar.url)
    embed.add_field(
        name="Никнейм на сервере:", value=member.display_name
    )
    embed.add_field(
        name="Дискорд никнейм:", value=str(member)
    )
    embed.add_field(
        name="Аккаунт создан:", value=member.created_at.strftime("%d-%m-%Y %H:%M:%S")
    )
    embed.add_field(
        name="Присоединился на сервер:", value=member.joined_at.strftime("%d-%m-%Y %H:%M:%S")
    )

    await (ctx.send
           (embed=embed)
           )

#функция удаляющая определенное количество сообщений
@bot.command()
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(
        f'Удалено {amount} сообщений', delete_after=5
    )

#игра кости которая при нажатие на реакцию выдает число от 1 до 6
@bot.command()
async def kub(ctx):
    message = await ctx.send(
        "НАЖМИТЕ ЧТОБЫ ИГРАТЬ"
    )
    await message.add_reaction(
        "🎲"
    )

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) == "🎲"

    try:
        await bot.wait_for(
            'reaction_add', timeout=30.0, check=check
        )
        await ctx.send(
            f"{ctx.author.mention} бросает куб и выпадает {random.randint(1, 6)}"
        )
    except TimeoutError:
        await ctx.send(
            "Время вышло, кубик не был брошен."
        )

#проверка написал ли пользователь запрещенное слово
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if any(word in message.content.lower() for word in forbidden_words):
        await message.delete()
        channel = bot.get_channel(1225509370226413568)
        await channel.send(
            f'{message.author.mention} употребил запрещенное слово в своем сообщении: "{message.content}"'
        )

        await message.channel.send(
            f'{message.author.mention} не ругайся!'
        )

        cursor.execute('''INSERT OR IGNORE INTO warnings (user_id, username, warnings) VALUES (?, ?, ?)''',
                       (message.author.id, str(message.author), 0))
        cursor.execute(
            '''UPDATE warnings SET warnings = warnings + 1 WHERE user_id = ?''', (message.author.id,)
        )
        connection.commit()

    await bot.process_commands(message)

#информация о том сколько предупреждений получил пользователь
@bot.command()
async def mat(ctx, member: disnake.Member = None):
    member = member or ctx.author

    cursor.execute(
        '''SELECT username, warnings FROM warnings WHERE user_id = ?''', (member.id,)
    )
    result = cursor.fetchone()

    if result:
        username, warnings = result
        embed = disnake.Embed(
            title=f"Количество предупреждений у {member.display_name}: {warnings}", color=0x800080
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send("У пользователя нет предупреждений.")
#при вводе команды выдает определенному пользователю роль которая запреает писать сообщения
@bot.command()
async def mute(ctx, member: disnake.Member, *, reason=""):
    role = ctx.guild.get_role(1225504947836158002)
    if role is None:
        await ctx.send(
            "Роль для выдачи мута не найдена."
        )
        return

    if ctx.author.top_role.id != 1229740170975252551:
        await ctx.send(
            "У вас недостаточно прав."
        )
        return

    if role in member.roles:
        await ctx.send(
            f"{member.mention} уже замьючен."
        )
        return

    await member.add_roles(
        role, reason=reason
    )
    await ctx.send(
        f"{member.mention} получил мут по причине: {reason}"
    )

#забирают эту роль
@bot.command()
async def unmute(ctx, member: disnake.Member):
    role = ctx.guild.get_role(1225504947836158002)
    if role is None:
        await ctx.send(
            "Роль для выдачи мута не найдена."
        )
        return

    if ctx.author.top_role.id != 1229740170975252551:
        await ctx.send(
            "У вас недостаточно прав."
        )
        return

    if role not in member.roles:
        await ctx.send(
            "Он и так не замьючен."
        )
        return

    await member.remove_roles(role)
    await ctx.send(
        f"{member.mention} теперь может снова говорить!"
    )

#бот отправляет аватарку определенного пользователя
@bot.command()
async def avatar(ctx, member: disnake.Member = None):
    user = ctx.message.author if member is None else member
    if user.avatar:
        embed = disnake.Embed(
            title=f'Аватар пользователя {user}', color=0x800080
        )
        embed.set_image(
            url=user.avatar.url
        )
        await ctx.send(
            embed=embed
        )
    else:
        await ctx.send(
            "У пользователя нет аватарки."
        )

#выдает предупреждение
@bot.command()
async def vor(ctx, member: disnake.Member):
    cursor.execute('''INSERT OR IGNORE INTO warnings (user_id, username, warnings) VALUES (?, ?, ?)''',
                   (member.id, str(member), 0))
    cursor.execute(
        '''UPDATE warnings SET warnings = warnings + 1 WHERE user_id = ?''', (member.id,)
    )
    connection.commit()

    if ctx.author.top_role.id != 1229740170975252551:
        await ctx.send(
            "У вас недостаточно прав."
        )
        return

    await ctx.send(
        f'Пользователь {member.mention} получил предупреждение.'
    )

#отправляет сообщение в чат модеров
@bot.command()
async def ticket(ctx, *, text: str):
    embed = disnake.Embed(title="Ticket", description=text, color=0x800080)

    role_mention = ctx.guild.get_role(1229740170975252551).mention

    embed.set_footer(
        text=f"сообщение от {ctx.author.display_name}"
    )

    channel = bot.get_channel(1225509370226413568)
    await channel.send(role_mention, embed=embed)

    await ctx.message.delete()

#выгоняет определенного пользователя с сервера
@bot.command()
async def kick(ctx, member: disnake.Member, *, reason: str = "Нарушение правил"):
    if ctx.author.top_role.id != 1229740170975252551:
        await ctx.send(
            "Недостаточно прав."
        )
        return
    moderator = ctx.author.display_name
    await member.kick(reason=reason)
    await ctx.send(
        f"{member.mention} был кикнут."
    )

    kick_channel = bot.get_channel(1225509370226413568)
    await kick_channel.send(
        f"{member.mention} был кикнут с сервера по причине: {reason}. Модератор: {moderator}"
    )

#банит пользователя
@bot.command()
async def ban(ctx, member: disnake.Member, *, reason=""):
    if ctx.author.top_role.id != 1229740170975252551:
        await ctx.send(
            "Недостаточно прав."
        )
        return

    await member.ban(reason=reason)
    await ctx.send(
        f"{member.mention} был забанен."
    )

    moderator = ctx.author.display_name

    channel = bot.get_channel(1225509370226413568)
    await channel.send(
        f"{member.mention} был забанен. Модератор: {moderator}"
    )

#разбанивает пользователя
@bot.command()
async def unban(ctx, member: disnake.User):
    if ctx.author.top_role.id != 1229740170975252551:
        await ctx.send(
            "Недостаточно прав."
        )
        return

    await ctx.guild.unban(member)
    await ctx.send(
        f"{member.mention} был разбанен."
    )

    moderator = ctx.author.display_name

    channel = bot.get_channel(1225509370226413568)
    await channel.send(
        f"{member.mention} был разбанен. Модератор: {moderator}"
    )

#выдает список у кого сколько предупреждений
@bot.command()
async def lidermat(ctx):
    cursor.execute('''SELECT username, warnings FROM warnings ORDER BY warnings DESC LIMIT 10''')
    user_warnings = cursor.fetchall()

    embed = disnake.Embed(title="Топ 10 пользователей по количеству предупреждений:", color=0x800080)

    for username, warnings in user_warnings:
        embed.add_field(name=f"Пользователь: {username}", value=f"Предупреждений: {warnings}", inline=False)

    await ctx.send(embed=embed)

#очищает базу данных с предупреждениями
@bot.command()
async def clearlid(ctx):
    if ctx.author.top_role.id != 1229740170975252551:
        await ctx.send(
            "Недостаточно прав."
        )
        return
    cursor.execute(
        '''DELETE FROM warnings'''
    )
    connection.commit()
    await ctx.send(
        "Список предупреждений очищен."
    )

#игра камень ножница бумага с ботом
@bot.command()
async def igra(ctx, choice: str):
    choices = ['камень', 'ножницы', 'бумага']
    emojis = {'камень': '🪨', 'ножницы': '✂️', 'бумага': '📃'}

    if choice.lower() not in choices:
        await ctx.send(
            "Пожалуйста, выберите только из: камень, ножницы или бумага."
        )
        return

    bot_choice = random.choice(choices)

    if choice.lower() == bot_choice:
        result = "Ничья!"
    elif (choice.lower() == 'камень' and bot_choice == 'ножницы') or \
            (choice.lower() == 'ножницы' and bot_choice == 'бумага') or \
            (choice.lower() == 'бумага' and bot_choice == 'камень'):
        result = "Поздравляю, вы победили!"
    else:
        result = "К сожалению, вы проиграли."

    user_emoji = emojis[choice.lower()]
    bot_emoji = emojis[bot_choice]

    embed = disnake.Embed(
        title="Игра в камень, ножницы, бумагу!", color=0x800080
    )
    embed.add_field(
        name="Ваш выбор:", value=f"{choice.capitalize()} {user_emoji}", inline=False
    )
    embed.add_field(
        name="Выбор бота:", value=f"{bot_choice.capitalize()} {bot_emoji}", inline=False
    )
    embed.add_field(
        name="Результат:", value=result, inline=False
    )

    await ctx.send(embed=embed)

#при вводе команды бот удаляет твое соообщение и выдает его за свое
@bot.command()
async def anonim(ctx, *, text):
    await ctx.message.delete()
    await ctx.send(text)

#перевест деньги с своего баланса определенному пользователю
@bot.command()
async def pay(ctx, amount: int, member: disnake.Member):
    user_id = ctx.author.id

    recipient_id = member.id

    if amount <= 0:
        await ctx.send(
            "Пожалуйста, укажите положительное количество монет."
        )
        return

    curso.execute(
        '''SELECT coins FROM coins WHERE user_id = ?''', (user_id,)
    )
    sender_coins = curso.fetchone()[0]
    if sender_coins < amount:
        await ctx.send(
            "У вас недостаточно монет для этой операции."
        )
        return

    curso.execute(
        '''UPDATE coins SET coins = coins - ? WHERE user_id = ?''', (amount, user_id)
    )

    curso.execute(
        '''INSERT OR IGNORE INTO coins (user_id, coins) VALUES (?, ?)''', (recipient_id, 0)
    )

    curso.execute(
        '''UPDATE coins SET coins = coins + ? WHERE user_id = ?''', (amount, recipient_id)
    )

    connect.commit()

    await ctx.send(
        f'Вы успешно перевели {amount} монет пользователю {member.mention}.'
    )

#забирает у определенного пользователя определенное количество монет с его баланса
@bot.command()
@commands.has_permissions(administrator=True)
async def min(ctx, amount: int, member: disnake.Member):
    if amount <= 0:
        await ctx.send(
            "Пожалуйста, укажите положительное количество монет."
        )
        return

    curso.execute(
        '''SELECT coins FROM coins WHERE user_id = ?''', (member.id,)
    )
    result = curso.fetchone()

    if not result or result[0] < amount:
        await ctx.send(
            "У пользователя недостаточно монет для списания."
        )
        return

    curso.execute(
        '''UPDATE coins SET coins = coins - ? WHERE user_id = ?''', (amount, member.id)
    )
    connect.commit()

    await ctx.send(
        f"У пользователя {member.mention} списано {amount} монет!"
    )

#топ 10 лидеров по количеству монет
@bot.command()
async def leadercoin(ctx):
    curso.execute(
        '''SELECT user_id, coins FROM coins ORDER BY coins DESC LIMIT 10'''
    )
    leaders = curso.fetchall()

    embed = disnake.Embed(
        title="Топ 10 самых богатых пользователей:", color=0x800080
    )

    for user_id, coins in leaders:
        member = ctx.guild.get_member(user_id)
        if member:
            embed.add_field(name=member.display_name, value=f"{coins} монет", inline=False)

    await ctx.send(embed=embed)

#выдает монеты которые нигде не хранятся можно сказать выдает с воздуха
@bot.command()
@commands.has_permissions(administrator=True)
async def payplus(ctx, member: disnake.Member, amount: int):
    if amount <= 0:
        await ctx.send(
            "Пожалуйста, укажите положительное количество монет."
        )
        return

    curso.execute('''INSERT OR IGNORE INTO coins (user_id, coins) VALUES (?, ?)''',
                   (member.id, 0))
    curso.execute(
        '''UPDATE coins SET coins = coins + ? WHERE user_id = ?''', (amount, member.id)
    )
    connect.commit()

    await ctx.send(
        f"Пользователь {member.mention} получил {amount} монет!"
    )

#количество монет пользователя который ввел данную команду
@bot.command()
async def money(ctx):
    user_id = ctx.author.id

    curso.execute(
        '''SELECT coins FROM coins WHERE user_id = ?''', (user_id,)
    )
    result = curso.fetchone()

    if result is None:
        curso.execute(
            '''INSERT INTO coins (user_id, coins) VALUES (?, ?)''', (user_id, 0)
        )
        connect.commit()
        coins = 0
    else:
        coins = result[0]

    await ctx.send(
        f'У вас {coins} монет.'
    )

#система лвлов
#каждые 15 сообщений пользователя бот добавляет 1 уровень в базу данных
class UserLevel:
    def __init__(self, user_id):
        self.user_id = user_id
        self.message_count = 0
        self.level = 0

    async def track_messages(self, ctx):
        self.message_count += 1
        if self.message_count % 15 == 0:
            self.level += 1
            curs.execute('''INSERT OR REPLACE INTO levels (user_id, level) VALUES (?, ?)''',
                           (self.user_id, self.level))
            conne.commit()
            await ctx.send(f"Ваш уровень повышен! Текущий уровень: {self.level}")


@bot.event
async def on_messagee(message):
    if message.author.bot:
        return

    user_id = message.author.id
    if user_id not in user_levels:
        user_levels[user_id] = UserLevel(user_id)

    user_level = user_levels[user_id]

    curs.execute('''SELECT level FROM levels WHERE user_id = ?''', (user_id,))
    result = curs.fetchone()
    if result:
        user_level.level = result[0]

    await user_level.track_messages(message.channel)
    await bot.process_commands(message)


#выдает текущий уровень пользователя
@bot.command()
async def userlvl(ctx):
    user_id = ctx.author.id
    if user_id in user_levels:
        user_level = user_levels[user_id]
        await ctx.send(f"Ваш текущий уровень: {user_level.level}")
    else:
        await ctx.send("Вы еще не получили уровень!")

#топ 10 лидеров по уровню
@bot.command()
async def lvlrecord(ctx):
    curs.execute('''SELECT user_id, level FROM levels ORDER BY level DESC LIMIT 3''')
    records = curs.fetchall()

    if not records:
        await ctx.send("В базе данных нет информации о уровнях пользователей.")
        return

    embed = disnake.Embed(title="Топ 3 лидеров по уровню:", color=0x800080)

    for index, (user_id, level) in enumerate(records, start=1):
        member = ctx.guild.get_member(user_id)
        username = member.display_name if member else f"User ID: {user_id}"
        embed.add_field(name=f"{index}. {username}", value=f"Уровень: {level}", inline=False)

    await ctx.send(embed=embed)

bot.run('токен')

connection.close()
connect.close()
conne.close()
