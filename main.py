import nextcord, datetime, json, re, httpx, certifi
from nextcord.ext import commands

config = json.load(open('./config.json', 'r', encoding='utf-8'))

bot = commands.Bot(
    command_prefix='nyx!',
    help_command=None,
    intents=nextcord.Intents.all(),
    strip_after_prefix=True,
    case_insensitive=True
)

class topupModal(nextcord.ui.Modal):

    def __init__(self):
        super().__init__(title='เติมเงิน', timeout=None, custom_id='topup-modal')
        self.link = nextcord.ui.TextInput(
            label = 'ลิ้งค์ซองอังเปา',
            placeholder = 'https://gift.truemoney.com/campaign/?v=xxxxxxxxxxxxxxx',
            style = nextcord.TextInputStyle.short,
            required = True
        )
        self.add_item(self.link)

    async def callback(self, interaction: nextcord.Interaction):
        link = str(self.link.value).replace(' ', '')
        message = await interaction.response.send_message(content='checking.', ephemeral=True)
        if re.match(r'https:\/\/gift\.truemoney\.com\/campaign\/\?v=+[a-zA-Z0-9]{18}', link):
            voucher_hash = link.split('?v=')[1]
            response = httpx.post(
                url = f'https://gift.truemoney.com/campaign/vouchers/{voucher_hash}/redeem',
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/8a0.0.3987.149 Safari/537.36'
                },
                json = {
                    'mobile': config['phoneNumber'],
                    'voucher_hash': f'{voucher_hash}'
                },
                verify=certifi.where(),
            )
            if (response.status_code == 200 and response.json()['status']['code'] == 'SUCCESS'):
                data = response.json()
                amount = int(float(data['data']['my_ticket']['amount_baht']))
                userJSON = json.load(open('./database/users.json', 'r', encoding='utf-8'))
                if (str(interaction.user.id) not in userJSON):
                    userJSON[str(interaction.user.id)] = {
                        "userId": interaction.user.id,
                        "point": amount,
                        "all-point": amount,
                        "transaction": [
                            {
                                "topup": {
                                    "url": link,
                                    "amount": amount,
                                    "time": str(datetime.datetime.now())
                                }
                            }
                        ]
                    }
                else:
                    userJSON[str(interaction.user.id)]['point'] += amount
                    userJSON[str(interaction.user.id)]['all-point'] += amount
                    userJSON[str(interaction.user.id)]['transaction'].append({
                        "topup": {
                            "url": link,
                            "amount": amount,
                            "time": str(datetime.datetime.now())
                        }
                    })
                json.dump(userJSON, open('./database/users.json', 'w', encoding='utf-8'), indent=4, ensure_ascii=False)
                embed = nextcord.Embed(description='✅﹒**เติมเงินสำเร็จ**', color=nextcord.Color.green())
            else:
                embed = nextcord.Embed(description='❌﹒**เติมเงินไม่สำเร็จ**', color=nextcord.Color.red())
        else:
            embed = nextcord.Embed(description='⚠﹒**รูปแบบลิ้งค์ไม่ถูกต้อง**', color=nextcord.Color.red())
        await message.edit(content=None,embed=embed)

class sellroleView(nextcord.ui.View):

    def __init__(self, message: nextcord.Message, value: str):
        super().__init__(timeout=None)
        self.message = message
        self.value = value

    @nextcord.ui.button(
        label='✅﹒ยืนยัน',
        custom_id='already',
        style=nextcord.ButtonStyle.primary,
        row=1
    )
    async def already(self, button: nextcord.Button, interaction: nextcord.Interaction):
        roleJSON = json.load(open('./database/roles.json', 'r', encoding='utf-8'))
        userJSON = json.load(open('./database/users.json', 'r', encoding='utf-8'))
        if (str(interaction.user.id) not in userJSON):
            embed = nextcord.Embed(description='🏦﹒เติมเงินเพื่อเปิดบัญชี', color=nextcord.Color.red())
        else:
            if (userJSON[str(interaction.user.id)]['point'] >= roleJSON[self.value]['price']):
                userJSON[str(interaction.user.id)]['point'] -= roleJSON[self.value]['price']
                userJSON[str(interaction.user.id)]['transaction'].append({
                    "payment": {
                        "roleId": self.value,
                        "time": str(datetime.datetime.now())
                    }
                })
                json.dump(userJSON, open('./database/users.json', 'w', encoding='utf-8'), indent=4, ensure_ascii=False)
                if ('package' in self.value):
                    for roleId in roleJSON[self.value]['roleIds']:
                        try:
                            await interaction.user.add_roles(nextcord.utils.get(interaction.user.guild.roles, id = roleId))
                        except:
                            pass
                    channelLog = bot.get_channel(config['channelLog'])
                    if (channelLog):
                        embed = nextcord.Embed()
                        embed.set_thumbnail(url=interaction.user.avatar.url)
                        embed.title = '»»———　ประวัติการซื้อยศ　——-««<'
                        embed.description = f'''
                       ﹒𝐔𝐬𝐞𝐫 : **<@{interaction.user.id}>**
                       ﹒𝐍𝐚𝐦𝐞 : **{interaction.user.name}**
                       ﹒𝐏𝐫𝐢𝐜𝐞 : **{roleJSON[self.value]['price']}**𝐓𝐇𝐁
                       ﹒𝐆𝐞𝐭𝐑𝐨𝐥𝐞 : <@&{roleJSON[self.value]["roleId"]}>
                       »»———　NUAHEE　——-««<'''
                        embed.color = nextcord.Color.blue()
                        embed.set_footer(text='NUAHEE AUTO BUY ROLE', icon_url='https://cdn.discordapp.com/attachments/1213843172661264434/1213843648907845692/standard_2.gif?ex=65f6f2fe&is=65e47dfe&hm=aea1b2add2f29bfbe61684e393f1cabc187abb47954283f35faeba8393fa097f&')
                        await channelLog.send(embed=embed)
                    embed = nextcord.Embed(description=f'💲﹒ซื้อยศสำเร็จ ได้รับ <@&{roleJSON[self.value]["name"]}>', color=nextcord.Color.green())
                else:
                    channelLog = bot.get_channel(config['channelLog'])
                    if (channelLog):
                        embed = nextcord.Embed()
                        embed.set_thumbnail(url=interaction.user.avatar.url)
                        embed.title = '»»———　ประวัติการซื้อยศ　——-««<'
                        embed.description = f'''
                       ﹒𝐔𝐬𝐞𝐫 : **<@{interaction.user.id}>**
                       ﹒𝐍𝐚𝐦𝐞 : **{interaction.user.name}**
                       ﹒𝐏𝐫𝐢𝐜𝐞 : **{roleJSON[self.value]['price']}**𝐓𝐇𝐁
                       ﹒𝐆𝐞𝐭𝐑𝐨𝐥𝐞 : <@&{roleJSON[self.value]["roleId"]}>
                       »»———　NUAHEE　——-««<'''
                        embed.color = nextcord.Color.blue()
                        embed.set_footer(text='NUAHEE AUTO BUY ROLE', icon_url='https://cdn.discordapp.com/attachments/1210553148607828089/1210582238974967838/standard_1.gif?ex=65eb1591&is=65d8a091&hm=4f72ae768b6eee50a61aa2c42a4b6115ea8100ecb94faf1db55932a08555b9a2&')
                        await channelLog.send(embed=embed)
                    embed = nextcord.Embed(description=f'💲﹒ซื้อยศสำเร็จ ได้รับยศ <@&{roleJSON[self.value]["roleId"]}>', color=nextcord.Color.green())
                    role = nextcord.utils.get(interaction.user.guild.roles, id = roleJSON[self.value]['roleId'])
                    await interaction.user.add_roles(role)
            else:
                embed = nextcord.Embed(description=f'⚠﹒เงินของท่านไม่เพียงพอ ขาดอีก ({roleJSON[self.value]["price"] - userJSON[str(interaction.user.id)]["point"]})', color=nextcord.Color.red())
        return await self.message.edit(embed=embed, view=None, content=None)

    @nextcord.ui.button(
        label='❌﹒ยกเลิก',
        custom_id='cancel',
        style=nextcord.ButtonStyle.red,
        row=1
    )
    async def cancel(self, button: nextcord.Button, interaction: nextcord.Interaction):
        return await self.message.edit(content='💚﹒ยกเลิกสำเร็จ',embed=None, view=None)

class sellroleSelect(nextcord.ui.Select):

    def __init__(self):
        options = []
        roleJSON = json.load(open('./database/roles.json', 'r', encoding='utf-8'))
        for role in roleJSON:
            options.append(nextcord.SelectOption(
                label=roleJSON[role]['name'],
                description=roleJSON[role]['description'],
                value=role,
                emoji=roleJSON[role]['emoji']
            ))
        super().__init__(
            custom_id='select-role',
            placeholder='[ เลือกยศที่คุณต้องการซื้อ ]',
            min_values=1,
            max_values=1,
            options=options,
            row=0
        )
    async def callback(self, interaction: nextcord.Interaction):
        message = await interaction.response.send_message(content='[SELECT] กำลังตรวจสอบ', ephemeral=True)
        selected = self.values[0]
        if ('package' in selected):
            roleJSON = json.load(open('./database/roles.json', 'r', encoding='utf-8'))
            embed = nextcord.Embed()
            embed.description = f'''
E {roleJSON[selected]['name']}**
'''
            await message.edit(content=None,embed=embed,view=sellroleView(message=message, value=selected))
        else:
            roleJSON = json.load(open('./database/roles.json', 'r', encoding='utf-8'))
            embed = nextcord.Embed()
            embed.title = '»»———　ยืนยันการสั่งซื้อ　——-««'
            embed.description = f'''
           \n คุณแน่ใจหรอที่จะซื้อ <@&{roleJSON[selected]['roleId']}> \n
»»———　NUAHEE　——-««
'''
            embed.color = nextcord.Color.blue()
            embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/1210553148607828089/1210582238974967838/standard_1.gif?ex=65eb1591&is=65d8a091&hm=4f72ae768b6eee50a61aa2c42a4b6115ea8100ecb94faf1db55932a08555b9a2&')
            await message.edit(content=None,embed=embed,view=sellroleView(message=message, value=selected))

class setupView(nextcord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(sellroleSelect())

    @nextcord.ui.button(
        label='🧧﹒เติมเงิน',
        custom_id='topup',
        style=nextcord.ButtonStyle.primary,
        row=1
    )
    async def topup(self, button: nextcord.Button, interaction: nextcord.Interaction):
        await interaction.response.send_modal(topupModal())

    @nextcord.ui.button(
        label='💳﹒เช็คเงิน',
        custom_id='balance',
        style=nextcord.ButtonStyle.primary,
        row=1
    )
    async def balance(self, button: nextcord.Button, interaction: nextcord.Interaction):
        userJSON = json.load(open('./database/users.json', 'r', encoding='utf-8'))
        if (str(interaction.user.id) not in userJSON):
            embed = nextcord.Embed(description='🏦﹒เติมเงินเพื่อเปิดบัญชี', color=nextcord.Color.red())
        else:
            embed = nextcord.Embed(description=f'╔═══════▣◎▣═══════╗\n\n💳﹒ยอดเงินคงเหลือ **__{userJSON[str(interaction.user.id)]["point"]}__** บาท\n\n╚═══════▣◎▣═══════╝', color=nextcord.Color.green())
        return await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_ready():
    bot.add_view(setupView())
    print(f'LOGIN AS {bot.user}')

@bot.slash_command(
    name='setup',
    description='setup',
    guild_ids=[config['serverId']]
)
async def setup(interaction: nextcord.Interaction):
    if (interaction.user.id not in config['ownerIds']):
        return await interaction.response.send_message(content='[ERROR] No Permission For Use This Command.', ephemeral=True)
    embed = nextcord.Embed()
    embed.title = '───                    NUAHEE               ───'
    embed.description = f'''
```
─────────────────────────────────────
🧧﹒บอทซื้อยศ 24 ชั่วโมง 💚

・ ซื้อยศต่างๆได้ตลอด 24/7
・ ✨﹒ระบบออโต
・ 💲﹒ซื้อแล้วได้ยศเลย
・ 🔓﹒เติมเงินเพื่อเปิดบัญชี
─────────────────────────────────────```
'''
    embed.color = nextcord.Color.blue()
    embed.set_image(url='https://cdn.discordapp.com/attachments/1213843172661264434/1213843647779311666/standard_3.gif?ex=65f6f2fd&is=65e47dfd&hm=2a3f5a37a7129b918515801a6d1eb254dde4c23db02e5802a8b62d3ad252424b&')
    embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/1213843172661264434/1213843648907845692/standard_2.gif?ex=65f6f2fe&is=65e47dfe&hm=aea1b2add2f29bfbe61684e393f1cabc187abb47954283f35faeba8393fa097f&')
    await interaction.channel.send(embed=embed, view=setupView())
    await interaction.response.send_message(content='[SUCCESS] Done.', ephemeral=True)

bot.run(config['token'])