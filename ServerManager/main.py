import nextcord
from nextcord.ext import commands
import json
import os
from colorama import Fore
from discord.ext import tasks
import asyncio

import webserver
import sys

with open('config.json','r') as f:
  config = json.load(f)

intents = nextcord.Intents.all()  
intents.members = True
intents.reactions = True
bot = commands.Bot(
	command_prefix=config['prefix'],
  help_command=None,
	intents=intents
)

color = 0xff0000

#presence_change.start()
@bot.event
async def on_ready():
  print(Fore.GREEN + f"正常に起動しました\nBot:{bot.user}" + Fore.RESET)
  try:
    os.mkdir(f"db-{config['guild']}")
  except FileExistsError:
    pass
  presence_change.start()

@tasks.loop(seconds=15)
async def presence_change():
  await bot.change_presence(activity=nextcord.Game(name=f"{len(bot.get_guild(int(config['guild'])).members)}人を監視中"))
  await asyncio.sleep(5)
  await bot.change_presence(activity=nextcord.Game(name=f"Ping {round(bot.latency * 1000)}ms"))
  await asyncio.sleep(5)
  await bot.change_presence(activity=nextcord.Game(name=f"スパムを検出中..."))
 

@bot.slash_command(description="botのバージョンを表示する")
async def ver(ctx):
  embed=nextcord.Embed(title="バージョン",description=f"サーバー運営bot ver1.14")
  await ctx.send(embed=embed)

@bot.slash_command(description="botのpingを実行する")
async def ping(ctx):
 await ctx.send(f"{round(bot.latency * 1000)}ms")

@bot.slash_command(description="helpコマンドを実行する")
async def help(ctx):
  embed=nextcord.Embed(title="help",description=f"""
!s.help   このhelpを表示します。
!s.ping   BOTのpingを表示します。   
!s.add [付与したいロール]  リアクションを作成します。[管理者専用コマンド]
!s.clear [削除したい数]  メッセージを消します。 [管理者専用コマンド]
!s.restart  BOTの再起動をします。 [管理者専用のコマンドです。]
BOT:サーバー運営BOT#6960 開発者：RENKUN0105#6484   
""")
  await ctx.send(embed=embed)
  os.execl(sys.executable,sys.executable,*sys.argv)

#ReactionRoleBotの親コマンド

@bot.command()
async def add(ctx,*roles:nextcord.Role):
  if ctx.author.guild_permissions.manage_messages:
    if not config['guild'] == str(ctx.guild.id):
      return
    if len(roles) > 20:
      await ctx.send("ロール数は20以下で指定してください")
      return
    if len(roles) <= 0:
      await ctx.send("ロールを指定してください")
      return
    reactions = ["🇦","🇧","🇨","🇩","🇪","🇫","🇬","🇭","🇮","🇯","🇰","🇱","🇲","🇳","🇴","🇵","🇶","🇷","🇸","🇹"]
    embed=nextcord.Embed(title=bot.user.name)
    for num in range(len(roles)):
      embed.add_field(name=reactions[num],value=roles[num].mention,inline=False)
    board = await ctx.send(embed=embed)
    for num in range(len(roles)):
      await board.add_reaction(reactions[num])
    try:
      os.mkdir(f'db-{config["guild"]}/{ctx.channel.id}')
    except FileExistsError:
      pass
    with open(f'db-{config["guild"]}/{ctx.channel.id}/{board.id}.json','w',encoding='utf-8') as f:
      f.write("{}")
    for num in range(len(roles)):
      with open(f'db-{config["guild"]}/{ctx.channel.id}/{board.id}.json','r',encoding='utf-8') as f:
        data = json.load(f)
        data[reactions[num]] = str(roles[num].id)
      with open(f'db-{config["guild"]}/{ctx.channel.id}/{board.id}.json','w',encoding='utf-8') as f:
        json.dump(data,f,indent=2,ensure_ascii=False)
  else:
    await ctx.send("このコマンドを実行するにはメッセージ管理の権限が必要です")

@bot.event
async def on_raw_reaction_add(payload:nextcord.RawReactionActionEvent):
  if payload.member == bot.user:
    return
  try:
    with open(f'db-{config["guild"]}/{payload.channel_id}/{payload.message_id}.json','r',encoding='utf-8') as f:
      data = json.load(f)
      guild = bot.get_guild(payload.guild_id)
      member = guild.get_member(payload.user_id)
      role = guild.get_role(int(data[payload.emoji.name]))
      try:
        await member.add_roles(role)
      except:
        channel = bot.get_channel(payload.channel_id)
        await channel.send(f"{member.mention}\nロールの付与に失敗しました",delete_after=5)
  except FileNotFoundError:
    return

@bot.event
async def on_raw_reaction_remove(payload:nextcord.RawReactionActionEvent):
  if payload.member == bot.user:
    return
  try:
    with open(f'db-{config["guild"]}/{payload.channel_id}/{payload.message_id}.json','r',encoding='utf-8') as f:
      data = json.load(f)
      guild = bot.get_guild(payload.guild_id)
      member = guild.get_member(payload.user_id)
      role = guild.get_role(int(data[payload.emoji.name]))
      try:
        await member.remove_roles(role)
      except:
        channel = bot.get_channel(payload.channel_id)
        await channel.send(f"{member.mention}\nロールの削除に失敗しました",delete_after=5)
  except FileNotFoundError:
    return


messages = {}
warning = {}
spam_timeout = 20
spam_levels = {
  "level-1":7,
  "level-2":12,
  "level-3":17
}

async def softban(message,member:nextcord.Member):
  try:
    await message.author.ban(reason="ソフトバン",delete_message_days=1)
    await message.author.unban(reason="ソフトバン")
    await message.channel.send(f"{message.author.mention}をスパムでキックしました")
  except:
    await message.channel.send(f"{message.author.mention}のキックに失敗しました")

async def spam_check(message,message_count):
  print(warning)
  if message_count >= spam_levels['level-3']:
    if warning[message.author.id] == "level-2":
      await softban(message,message.author)
  elif message_count >= spam_levels['level-2']:
    if warning[message.author.id] == "level-2":
      return
    if warning[message.author.id] == "level-1":
      warning[message.author.id] = "level-2"
      await message.channel.send(f"{message.author.mention}最終警告\nスパムをやめてください\n意図がないのであれば{spam_timeout+5}秒間の間メッセージを送信しないでください")
      await message_delete(message)
  elif message_count >= spam_levels['level-1']:
    if not message.author.id in warning:
      warning[message.author.id] = "level-1"
      await message.channel.send(f"{message.author.mention}警告\nスパムをやめてください")
  return

async def message_delete(message):
  try:
    for delete_message in messages[message.author.id]:
      await delete_message.delete()
      await message_remove(message)
  except:
    pass

async def message_remove(message):
  try:
    await asyncio.sleep(spam_timeout)
    messages[message.author.id].remove(message)
  except KeyError:
    pass

@bot.listen()
async def on_message(message):
  if message.author.bot:
    return
  if message.guild.id != int(config['guild']) or message.guild.id is None:
    return
  if message.author.guild_permissions.administrator or message.author.guild_permissions.manage_messages:
    return
  if not message.author.id in messages:
    messages[message.author.id] = []
  messages[message.author.id].append(message)
  message_count = len(messages[message.author.id])
  await spam_check(message,message_count)
  await message_remove(message)

webserver.open()
try:
  bot.run(os.getenv("token"))
except:
  os.system("kill 1")
