import discord
import os
import re
import requests
from bs4 import BeautifulSoup
import json
from nltk.corpus import wordnet
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib
import numpy as np
from unidecode import unidecode
nltk.download('wordnet')
nltk.download('omw')
nltk.download('omw-1.4')
nltk.download('punkt')


import dotenv # comentar no monstrao
dotenv.load_dotenv() # comentar no monstrao
intents = discord.Intents.all()
vectorizer = TfidfVectorizer()
client = discord.Client(intents=intents)
api_ip = os.getenv('API_IP')
@client.event
async def on_message(message: discord.Message):
    
    if message.author == client.user:
        return
    
    
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
            
    
    # if start with !crawl
    elif message.content.lower()[:6] == '!crawl':


        pipeline = joblib.load('model_sentiment.joblib')

        # create folder website_data if not exists
        if not os.path.exists('website_data'):
            os.mkdir('website_data')


        # check if file inverted_index.json exists
        if not os.path.exists('inverted_index.json'):
            inverted_index = {}
        else:
            with open('inverted_index.json', 'r') as f:
                inverted_index = json.load(f)


        # Regular expression pattern for matching url address
        url_pattern = r"\b(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+)\.([a-zA-Z0-9-]+)\b"
        url_adress = message.content.lower()[7:].strip()
        # check if the url adress is valid
        if re.match(url_pattern, url_adress):
            # get the url
            response = requests.get(url_adress)
            if response.status_code != 200:
                print(response.status_code)
                await message.channel.send('Erro ao obter informações da URL, tente novamente mais tarde')
                return
            # get the html
            html = response.text
            # parse the html
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text( separator=' ')
            words = re.findall(r'\b\w+\b', text)
            data = {}
            data["url"] = url_adress
            title = soup.title.string
            # remove all tokens and accents from title
            title = unidecode(title)
            
            data['title'] = title
            data['links'] = [link.get('href') for link in soup.find_all('a')]
            data["html"] = html
            # transform text to a list of words (the text is words separated by spaces)
            text_list = text.split(' ')
            print('test',pipeline.predict_log_proba([text])[0])
            # converter as probabilidades logarítmicas em probabilidades não logarítmicas
            # pred_log_proba = pipeline.predict_log_proba([text])[0]
            sentiment = pipeline.predict_log_proba(["happy"]).max()
            data['sentiment'] = sentiment    

            try:

                await message.channel.send(f'''
                Sentimento: {data['sentiment']}
                Título: {data['title']}
                Links: {data['links']}
                ''')
            except:
                await message.channel.send('Response too long, but the crawler works!')
            # save the data in a new json file with the name of the title
            with open(f'website_data/{title}.json', 'w+', encoding='utf-8') as f:
                json.dump(data, f)
            
            # now, create a inverted index with term frequencies (TF)

            
            # lower case all words
            words = [word.lower() for word in words]
            
            # count the number of times each word appears in the text
            count_words = {}
            for word in words:
                if word not in count_words:
                    count_words[word] = 0
                count_words[word] += 1
            total_words = len(words)

            # calculate the TF for each word in inverted_index
            for word in count_words:
                if total_words == 0:
                    tf_word = 0
                elif count_words[word] == 0:
                    tf_word = 0
                else:
                    tf_word = count_words[word] / total_words
                if word not in inverted_index:
                    inverted_index[word] = {}
                if title not in inverted_index[word]:
                    inverted_index[word][title] = tf_word
            
            # save the inverted index in a json file
            with open('inverted_index.json', 'w+', encoding= 'utf-8') as f:
                json.dump(inverted_index, f, ensure_ascii=False, indent=4)
            
            # send the message to the channel telling that the crawl was successful and the sentiment
            try:
                await message.channel.send(f'Crawled {url_adress} with sentiment {sentiment}')
            except:
                pass
    
    # check if the message start with !search
    elif message.content.lower()[:8] == '!search ':
        threshold = None
        input = message.content.lower()[8:].strip()
        pattern = r'^[^\s]+ th=(-?\d+\.\d+)$'
        match1 = re.match(pattern, input)
        if match1:
            threshold = float(match1.group(1))
            print(threshold)
            if (threshold < -1) or (threshold > 1):
                await message.channel.send('Threshold inválido, deve estar entre -1 e 1')
                return
            # remove the th=... from the input
            input = input.replace("th="+match1.group(1), '').strip()
            print(input)
        


        # get the rest of the message
        search_term = input

        # count the number of files in website_data
        count_files = 0
        sentiments_title = {}
        for file in os.listdir('website_data'):
            count_files += 1
            # enter in the folder website_data
            with open(f'website_data/{file}', 'r') as f:
                print("abrindo arquivo")
                # check if has the key sentiment
                data = json.load(f)
                if 'sentiment' in data.keys():
                    sentiments_title[data['title']] = data['sentiment']
        if count_files == 0:
            await message.channel.send('Não há nenhum website salvo, rode um !crawl <URL> primeiro')
            return


        print("procurando por: ", search_term, "")
        # check if file inverted_index.json exists
        if not os.path.exists('inverted_index.json'):
            await message.channel.send('Não há nenhum índice invertido salvo, rode um !crawl <URL> primeiro')
            return
        else:
            with open('inverted_index.json', 'r') as f:
                inverted_index = json.load(f)
        # check if the search term is in the inverted index
        if search_term not in inverted_index:
            await message.channel.send('Termo não encontrado')
            return
        else:
            # check which website has the highest TF
            max_tf = 0
            max_tf_website = ''
            tf_maior_0 = 0
            for website in inverted_index[search_term]:
                # check if threshold is not None
                if threshold is not None:
                    # check if the sentiment is higher than the threshold
                    if sentiments_title[website] < threshold:
                        print(sentiments_title[website])
                        continue

                if inverted_index[search_term][website] > max_tf:
                    max_tf = inverted_index[search_term][website]
                    max_tf_website = website
                if inverted_index[search_term][website] > 0:
                    tf_maior_0 += 1
            if tf_maior_0 == 0:
                await message.channel.send('Termo não encontrado')
                return
            # df = numbers of website with tf_0 divided by the total number of websites
            df = tf_maior_0 / count_files
            tf_df = max_tf/df
            
            await message.channel.send(f'''
            O termo {search_term} com o maior TF/DF esta no documento {max_tf_website} com o valor de {tf_df}, o TF é {max_tf} e o DF é {df}
            ''')
    
    # check if the message start with !wn_search
    elif message.content.lower()[:10] == '!wn_search':

        threshold = None
        input = message.content.lower()[10:].strip()
        pattern = r'^[^\s]+ th=(-?\d+\.\d+)$'
        match1 = re.match(pattern, input)
        if match1:
            threshold = float(match1.group(1))
            print(threshold)
            if (threshold < -1) or (threshold > 1):
                await message.channel.send('Threshold inválido, deve estar entre -1 e 1')
                return
            # remove the th=... from the input
            input = input.replace("th="+match1.group(1), '').strip()
            print(input)
        


        terms =re.findall('\w+', input)

        relevancy = {}

        sentiments_title = {}
        for file in os.listdir('website_data'):
            # enter in the folder website_data
            with open(f'website_data/{file}', 'r') as f:
                # check if has the key sentiment
                data = json.load(f)
                if 'sentiment' in data.keys():
                    sentiments_title[data['title']] = data['sentiment']

        await message.channel.send(f'''
        Procurando por: {terms} ou palavras similares
        ''')
        # check if file inverted_index.json exists
        if not os.path.exists('inverted_index.json'):
            await message.channel.send('Não há nenhum índice invertido salvo, rode um !crawl <URL> primeiro')
            return
        
        
        # get the file inverted_index.json
        with open('inverted_index.json', 'r') as f:
            inverted_index = json.load(f)
        
        keys = list(inverted_index.keys())

        # check if threshold is not None
        if threshold is not None:
            keys = []
            for key in inverted_index.keys():
                websites = inverted_index[key]
                websites_keys = list(websites.keys())
                for website in websites_keys:
                    if sentiments_title[website] >= threshold:
                        keys.append(key)

        
        for voc in keys:
            valor_soma = 0
            for word in terms:
                voc_lower = re.sub(r'[^\w\s]', '', voc.lower())

                syns1 = wordnet.synsets(word)
                syns2 = wordnet.synsets(voc_lower)
                print("procurando por ", word, " e ", voc_lower, "")
                if len(syns1) > 0 and len(syns2) > 0:
                    similarity = syns1[0].wup_similarity(syns2[0])
                    print("a similaridade entre ", word, " e ", voc_lower, " é ", similarity, "")
                    if similarity is not None:
                        valor_soma += similarity
            relevancy[voc] = valor_soma

        # remove all terms from relevancy that is 0
        relevancy = {k: v for k, v in relevancy.items() if v != 0}
        if len(relevancy) == 0:
            await message.channel.send('Não há palavras similares')
            return
        

        # sort the relevancy dict and get the first 5 items
        similar_terms = sorted(relevancy.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # search for the similar words in the inverted index
        similarity_words = []
        for term in similar_terms:
            if term[0] in inverted_index:
                similarity_words.append(term[0])
        
        # if there is no similar words, send a message
        if len(similarity_words) == 0:
            await message.channel.send('Não há palavras similares')
            return

        # send the message
        await message.channel.send(f'''
        Palavras similares a {terms}:
        {similarity_words}
        ''')


        
        

            




        
    
    elif message.content.lower() == '!help':
        await message.channel.send('''
        Comandos disponíveis:
        !oi - Retorna uma mensagem de boas vindas
        !source - Retorna o link do repositório do bot
        !author - Retorna o email do autor do bot
        !run <IP> - Retorna informações sobre o IP informado
        !crawl <URL> - Retorna informações sobre a URL informada
        !help - Retorna uma lista com os comandos disponíveis''')

@client.event
async def on_ready():
    print('client Online')


def find_similar_words(word, word_list):

    # Create an empty list to store the similar words
    similar_words = []
    
    # Get the synsets (sets of synonyms) for the word
    synsets = wordnet.synsets(word)
    print(synsets)
    
    # Iterate through each synset and add its lemmas (synonyms) to the list of similar words
    for synset in synsets:
        for lemma in synset.lemmas():
            similar_words.append(lemma.name())
    


    # Add the original word to the list of similar words
    similar_words.append(word)

    print(similar_words)
    
    # Create an empty list to store the words that appear in both similar_words and word_list
    matching_words = []
    
    # Iterate through each word in similar_words and check if it appears in word_list
    for similar_word in similar_words:
        if similar_word in word_list:
            matching_words.append(similar_word)
    
    return matching_words


client.run(os.getenv('TOKEN'))