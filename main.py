import discord
import os
import re
import requests

import dotenv # comentar no monstrao
dotenv.load_dotenv() # comentar no monstrao
intents = discord.Intents.all()

client = discord.Client(intents=intents)
api_ip = os.getenv('API_IP')
@client.event
async def on_message(message: discord.Message):
    # if the channel is Geral, do not answer
    
    if message.content.lower() == '!oi':
        # get user name
        user = message.author
        user = user.name.split('#')[0]
        await message.channel.send(f'Olá {user}! ')
    
    elif message.content.lower() == '!source':
        await message.channel.send('O meu código fonte pode ser encontrado nesse repositório: https://github.com/MarceloCMiguel/discord-nlp/')
    
    elif message.content.lower() == "!author":
        await message.channel.send('Meu criador é o Marcelo Miguel ( marcelocm8@al.insper.edu.br )')

    # check if the first 4 words is !run
    elif message.content.lower()[:4] == '!run':
        # Regular expression pattern for matching IP address
        ip_pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"

        ip_adress = message.content.lower()[5:].strip()
        # check if the ip adress is valid
        if re.match(ip_pattern, ip_adress):
            # send the message to the channel
            response = requests.get('https://api.ipgeolocation.io/ipgeo', 
                        params=
                        {'apiKey': api_ip,
                         'ip': ip_adress})
            if response.status_code != 200:
                await message.channel.send('Erro ao obter informações do IP, tente novamente mais tarde')
                return
            data = response.json()
            isp = data['isp']
            country = data['country_name']
            city = data['city']
            await message.channel.send(f'O seu provedor de internet é o {isp}\n situado no país {country} e na cidade {city}')
            
        else:
            # send the message to the channel
            await message.channel.send('Endereço de IP inválido')
    
    elif message.content.lower() == '!help':
        await message.channel.send('''
        Comandos disponíveis:
        !oi - Retorna uma mensagem de boas vindas
        !source - Retorna o link do repositório do bot
        !author - Retorna o email do autor do bot
        !run <IP> - Retorna informações sobre o IP informado
        !help - Retorna uma lista com os comandos disponíveis''')

@client.event
async def on_ready():
    print('client Online')


client.run(os.getenv('TOKEN'))