import discord
import os
import dotenv
dotenv.load_dotenv()
intents = discord.Intents.all()

client = discord.Client(intents=intents)

@client.event
async def on_message(message: discord.Message):
    if message.content.lower() == '!oi':
        # get user name
        user = message.author
        user = user.name.split('#')[0]
        await message.channel.send(f'Olá {user}! ')
    
    elif message.content.lower() == '!source':
        await message.channel.send('O meu código fonte pode ser encontrado nesse repositório: https://github.com/MarceloCMiguel/discord-nlp/')
    
    elif message.content.lower() == "!author":
        await message.channel.send('Meu criador é o Marcelo Miguel ( marcelocm8@al.insper.edu.br )')

@client.event
async def on_ready():
    print('client Online')



client.run(os.getenv('TOKEN'))