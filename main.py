import json
import khl, dice
import os

# load config from config/config.json, replace `path` points to your own config file
# config template: `./config/config.json.example`
with open('./config.json', 'r', encoding = 'utf-8') as f:
    config = json.load(f)

# init Cert for Bot OAuth
cert = khl.Cert(client_id = config['client_id'],
                client_secret = config['client_secret'],
                token = config['token'])

# init Bot
bot = khl.Bot(cmd_prefix = ['.'], cert = cert)


# replicate the message, in KMarkdown
@bot.command(name = 'md')
async def md(msg: khl.message.TextMsg, *dummy):
    content = msg.content[4:]
    await bot.delete(msg.msg_id)
    await msg.ctx.send(f"(met){msg.author_id}(met)说:\n" + content)

# dice parsing and evaluation
@bot.command(name = 'r')
async def r(msg: khl.message.TextMsg, *dummy):
    content = msg.content[len('.r '):].strip(' \n')

    if content == 'help':
        await msg.ctx.send(dice.__doc__)
        return

    msg2send = '\n'.join(dice.parse_and_eval_dice(content))
    await msg.ctx.send(f'(met){msg.author_id}(met)：\n' + msg2send)

# everything done, go ahead now!
bot.run()
