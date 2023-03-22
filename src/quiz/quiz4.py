# ========================================================================
# Copyright 2022 Emory University
#
# Licensed under the Apache License, Version 2.0 (the `License`);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an `AS IS` BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ========================================================================
__author__ = 'Dani Roytburg'
print("Installing libraries...")
import logging
logging.getLogger().setLevel(logging.ERROR)
from emora_stdm import DialogueFlow, Macro, Ngrams
from typing import Dict, Any, List
from datetime import datetime
from transformers import pipeline
sentiment = pipeline('sentiment-analysis', model = 'distilbert-base-uncased-finetuned-sst-2-english')
import geocoder
from urllib.request import urlopen
import pandas as pd
import json
import os
import spacy
import re
import ast
from zipfile import ZipFile
import requests,io
from pathlib import Path
import random
from gingerit.gingerit import GingerIt
nlp = spacy.load("en_core_web_trf")

if "user_data.json" not in os.listdir("resources/quiz4"):
    print("No user data found. Creating fresh user data.")
    deef = pd.DataFrame(columns = ['name', 'recommendations'])
    deef.loc[len(deef)] = ['dani', [{'type': 'movie', 'title': 'the shining', 'accepted': 'no'}, {'type': 'song', 'title': 'birdland', 'accepted': 'idk'}, {'type': 'movie', 'title': 'the sound of music (1989)', 'accepted': 'yes'}]]
    deef.to_json("resources/quiz4/user_data.json")
if "ml-25m" not in os.listdir(os.path.join(Path.cwd(), "resources/quiz4/")):
    print("Movies data not found. Downloading movies dataset.")
    r = requests.get('https://files.grouplens.org/datasets/movielens/ml-25m.zip')
    z = ZipFile(io.BytesIO(r.content))
    z.extractall("resources/quiz4")
data_w_genres = pd.read_csv('resources/quiz4/music-data/data_w_genres.csv')
artist_data = pd.read_csv("resources/quiz4/music-data/data.csv")
def extract_quoted_text(s):
    pattern = r'\"(.*?)\"'
    result = re.findall(pattern, s)
    return result[0].lower()
def getpoints(x, y):
    rawtext = urlopen('https://api.weather.gov/points/' + str(x) + "," + str(y)).read()
    jason = json.loads(rawtext)
    return jason

def getgrid(grx, gry):
    for _ in range(100):
        try:
            next_json = json.loads(urlopen(f'https://api.weather.gov/gridpoints/TOP/{str(grx)},{str(gry)}/forecast').read())
            return next_json
        except:
            continue
    print("ERROR")
    return

def first_json():
    coor = geocoder.ip('me').latlng
    x, y = coor[0], coor[1]
    jason = getpoints(x, y)
    return jason
def second_json():
    jason = first_json()
    grx, gry = str(jason['properties']['gridX']), str(jason['properties']['gridY'])
    return getgrid(grx, gry)

def get_weather():
    coor = geocoder.ip('me').latlng
    x, y = coor[0], coor[1]
    jason = getpoints(x, y)
    grx, gry = str(jason['properties']['gridX']), str(jason['properties']['gridY'])
    new_json = getgrid(grx, gry)
    short_forecast = new_json['properties']['periods'][0]['shortForecast'].lower()
    if "snow" in short_forecast:
        return "snowy"
    elif "sun" in short_forecast:
        return "sunny"
    elif "cloud" in short_forecast:
        return "cloudy"
    elif "rain" in short_forecast:
        return "rainy"
    elif "fog" in short_forecast:
        return "foggy"
    else: return short_forecast

class MacroGetTime(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        current_time = datetime.now()
        if current_time.hour < 12:
            return ("good morning")
        elif current_time.hour > 18:
            return ("good evening")
        return ("hey")
class MacroGetWeather(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        jason = first_json()
        vars['first_json'] = jason
        vars['city'] = jason['properties']['relativeLocation']['properties']['city']
        return f"it's {get_weather()} in {vars['city'].lower()} today!"
class MacroGetSentiment(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        text = [vars['__raw_user_utterance__']]
        output = sentiment(text)[0]['label']
        if output == "NEGATIVE":
            return "sorry to hear that!"
        elif output == "POSITIVE":
            return "that's great!"
        else: return "good to know."

class MacroAskName(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        bank = ['what is your name?', 'what do they call you?', 'what\'s your name bruh?', 'what should i call you?', 'preferred name?', 'can i have your name?', 'how shall i address you?']
        return random.choice(bank)

class MacroGetName(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if 'name' in vars:
            return vars['name']
        else:
            output = vars['__user_utterance__']
            doc = nlp(output)
            name = [thing.text for thing in doc.ents if thing.label_ == 'PERSON']
            if len(name) == 0:
                return False
            else:
                if name[0] != 'i am':
                    vars['name'] = name[0]
                else:
                    vars['name'] = name[-1]
                return True

class MacroForceName(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        text = vars['__raw_user_utterance__']
        try:
            if vars['__system_state__'] == 'song':
                vars['request'] = extract_quoted_text(text)
            else:
                vars['name'] = extract_quoted_text(text)
            return True
        except:
            return False
deef = pd.read_json("resources/quiz4/user_data.json")
def ask_question(vars):
    user_data = vars['user_data']
    for rec in user_data['recommendations']:
        if rec['accepted'] == 'yes':
            title = rec['title']
            vars['moretosay'] = True
            bank = ['. did you get to watch #MOVIE?', '. did #MOVIE end up on your list?', '. any thoughts on #MOVIE?']
            return random.choice(bank).replace('#MOVIE', title)
    return ""
class MacroExistingUser(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if not deef['name'].isin([vars['name']]).any():
            return "nice to meet you, " + vars['name']
        else:
            jesus = deef.loc[deef['name'] == vars['name']].iloc[0]
            vars['user_data'] = deef.loc[deef['name'] == vars['name']].iloc[0]
            return "welcome back, " + vars['name'] + ask_question(vars)

movie = pd.read_csv("resources/quiz4/ml-25m/movies.csv")
oratings = pd.read_csv("resources/quiz4/ml-25m/ratings.csv")
oratings = oratings.loc[oratings['rating'] == 5.0]
otags = pd.read_csv("resources/quiz4/ml-25m/tags.csv")

def pick_movie(all_variables):
    if 'user_data' in all_variables and type(all_variables['user_data']) == pd.core.frame.DataFrame:
        user_data = all_variables['user_data']
        cant_reuse = list()
        for element in user_data['recommendations']:
            if element['type'] == 'movie':
                cant_reuse.append(element['title'])
        random_id = random.choice(list(oratings['movieId']))
        random_movie = movie.loc[movie['movieId'] == random_id].iloc[0]
        while random_movie['title'] in cant_reuse:
            random_id = random.choice(list(oratings['movieId']))
            random_movie = movie.loc[movie['movieId'] == random_id].iloc[0]
        return random_movie
    else:
        random_id = random.choice(list(oratings['movieId']))
        random_movie = movie.loc[movie['movieId'] == random_id].iloc[0]
        return random_movie
class MacroGetMovie(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if 'another_try' in vars:
            print(f"sorry you didn't like it :(\nok {vars['name']}... let\'s try again ")
        bank = ['my next hottest pick is #MOVIE.', 'i think you should totally watch #MOVIE.', 'in my opinion, you should check out #MOVIE.', '#MOVIE is really good; at least so i\'ve heard!', 'maybe check out #MOVIE!', 'as an AI language model, i cannot express value judgements. however, a little birdie told me #MOVIE was good.']
        vars['current_pick'] = pick_movie(vars)
        return random.choice(bank).replace('#MOVIE', vars['current_pick']['title'])

class MacroGaugeResponse(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if sentiment(vars['__user_utterance__'])[0]['label'] == 'POSITIVE':
            return True
        else:
            return False
class MacroSo(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        bank = ['cool. ', 'good to hear. ', 'neat. ', 'nice. ', 'sick. ', 'ok! ', 'nice to see it. ']
        if deef['name'].isin([vars['name']]).any():
            if 'moretosay' in vars:
                return random.choice(bank) + "as you know,"
            else:
                return "as you know,"
        else:
            return "so,"
def get_genres(text):
    regex = r'[a-zA-Z\-]+'
    matches = re.findall(regex, text)
    return matches
def detailed_sentence(vars):
    metadata = movie.loc[movie['movieId'] == vars['current_pick']['movieId']]
    tags = list(otags.loc[otags['movieId'] == vars['current_pick']['movieId']]['tag'].value_counts().index)
    nouns = list()
    adjectives = list()
    for tag in tags:
        if len(tag.split()) == 1:
            doc = nlp(tag)
            if doc[0].pos_ == 'NOUN' and any(symbol not in tag for symbol in ["(","/","\\","$"]):
                nouns.append(doc[0].lemma_.lower())
            elif doc[0].pos_ == 'ADJ' and sentiment(doc.text)[0]['label'] == 'POSITIVE':
                adjectives.append(doc[0].lemma_.lower())
    random.shuffle(nouns)
    random.shuffle(adjectives)
    cantnoun = False
    cantadjective = False
    try:
        noun1, noun2, noun3 = nouns.pop(), nouns.pop(), nouns.pop()
    except:
        cantnoun = True
    try:
        adjective1, adjective2 = adjectives.pop(), adjectives.pop()
    except:
        cantadjective = True
    genre = get_genres(metadata['genres'].iloc[0])[0].lower()
    assent = ['sure! ', 'totally! ', 'for sure. ', 'yeah -- ', 'umm... i think ', "ok, so "]
    if cantnoun:
        genreandnoun = ['it\'s a #GENRE movie. ', 'it\'s a #GENRE. i really liked it! ']
    else:
        genreandnoun = ['it\'s a #GENRE movie about #NOUN1 and #NOUN2. ', 'this is a #GENRE film that touches on #NOUN3 and #NOUN2. ', '#NOUN1, #NOUN3 and #NOUN2 are important for this #GENRE movie. ']
    if cantadjective:
        adjective = ['interested?', 'curious?', 'will you watch it?']
    else:
        adjective = ['raters called it a #ADJECTIVE1 and #ADJECTIVE2 watch. interested?', 'some would say it was #ADJECTIVE1 or #ADJECTIVE2. wanna see it?', 'i found it #ADJECTIVE2 and #ADJECTIVE1. curious?']
    if cantnoun and cantadjective:
        out = "it's a #GENRE movie".replace("#GENRE",genre)
    elif cantnoun:
        out = random.choice(assent) + random.choice(genreandnoun).replace("#GENRE",genre) + random.choice(adjective).replace("#ADJECTIVE1",adjective1).replace("#ADJECTIVE2",adjective2)
    elif cantadjective:
        out = random.choice(assent) + random.choice(genreandnoun).replace("#GENRE",genre).replace("#NOUN1",noun1).replace('#NOUN2',noun2).replace("#NOUN3",noun3) + random.choice(adjective)
    else:
        out = random.choice(assent) + random.choice(genreandnoun).replace("#GENRE",genre).replace("#NOUN1",noun1).replace('#NOUN2',noun2).replace("#NOUN3",noun3) + random.choice(adjective).replace("#ADJECTIVE1",adjective1).replace("#ADJECTIVE2",adjective2)
    return GingerIt().parse(out)['result'].lower()
class MacroDetails(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        return detailed_sentence(vars)

def isInterrogative(text):
    if any(trigger in text for trigger in
           ['tell me more', 'why', 'about', 'is it', 'is that', 'is the movie', 'what is the song', 'detail', 'what is',
            'specific', '?']):
        return True
    else:
        return False
class MacroIsInterrogative(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if any(trigger in vars['__user_utterance__'] for trigger in ['tell me more', 'why', 'about', 'is it', 'is that', 'is the movie', 'what is the song', 'detail', 'what is', 'specific', '?']):
            return True
        else:
            return False
class MacroIsNegative(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if isInterrogative(vars['__user_utterance__']):
            return False
        if sentiment(vars['__user_utterance__'])[0]['label'] == "NEGATIVE" or any(seenit in vars['__user_utterance__'] for seenit in ['already','again','seen','watched', 'another']):
            recommendation = {'type': vars['__system_state__'], 'title': vars['current_pick']['title'], 'accepted': 'no'}
            if 'user_data' in vars:
                vars['user_data']['recommendations'].insert(0, recommendation)
                row = deef.loc[deef['name'] == vars['name']].iloc[0]
                row = vars
            else:
                deef.loc[len(deef)] = [vars['name'], [recommendation]]
                vars['user_data'] = deef.loc[len(deef) - 1]
            deef.to_json("resources/quiz4/user_data.json")
            vars['another_try'] = True
            return True
        else:
            return False
class MacroPositive(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        recommendation = {'type': 'movie', 'title': vars['current_pick']['title'], 'accepted': 'yes'}
        if 'user_data' in vars:
            vars['user_data']['recommendations'].insert(0, recommendation)
            row = deef.loc[deef['name'] == vars['name']].iloc[0]
            row = vars
        else:
            deef.loc[len(deef)] = [vars['name'], [recommendation]]
            vars['user_data'] = deef.loc[len(deef) - 1]
        deef.to_json("resources/quiz4/user_data.json")
        if 'another_try' in vars:
            del vars['another_try']
        return f"hope u like it, {vars['name']}! want something else?"


class MacroGetSong(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        request = vars['request']
        mask = [request in thing for thing in data_w_genres['genres']]
        vars['artist_picks'] = data_w_genres.loc[mask]
        if 'user_data' in vars:
            ban_list = [rec['title'] for rec in vars['user_data']['recommendations'] if
                        rec['accepted'] == 'no' and rec['type'] == ['song']]
        else:
            ban_list = []
        artist_choices = list(vars['artist_picks']['artists'])
        random.shuffle(artist_choices)
        try:
            artist = artist_choices.pop()
        except:
            return "we couldn\'t find any. sorry! wanna try again?"
        artist_mask = [artist in ast.literal_eval(roster) for roster in artist_data['artists']]
        songs = artist_data.loc[artist_mask]['name']
        if len(songs) == 0:
            return "we couldn\'t find any. sorry! wanna try again?"
        else:
            return f"ok {vars['name']}, i recommend {list(songs)[0]}. it\'s a good {request} choice by {artist}."



print("Everything's installed!")


macros = {
    "TIME": MacroGetTime(),
    "WEATHER": MacroGetWeather(),
    "SENTIMENT": MacroGetSentiment(),
    "NAME": MacroGetName(),
    "ASKNAME": MacroAskName(),
    "FORCENAME": MacroForceName(),
    "FMOVIE": MacroGetMovie(),
    "SO": MacroSo(),
    "RESPONSE": MacroGaugeResponse(),
    "DETAILS": MacroDetails(),
    "EXISTINGUSER": MacroExistingUser(),
    "WANTSDETAILS": MacroIsInterrogative(),
    "NEGATIVE": MacroIsNegative(),
    "POSITIVE": MacroPositive(),
    "SONG": MacroGetSong()
}

transitions = {
    'state': 'start',
    '#TIME`, what\'s up?`#WEATHER`i\'m yaser, a movie and music recommendation bot.`': {
        'error': {
            '#SENTIMENT`i\'m doing fine myself.`#ASKNAME': {
                '#NAME': 'gotname',
                'error': {
                    '`sorry, i didn\'t quite catch that. enclose your name in quotes and i\'ll just copy that. my bad!`': {
                        '#FORCENAME': 'gotname',
                        'error': {
                            '`maybe we\'re not getting eachother. start over?`': 'start'
                        }
                    }
                }
            }
        }
    }
}
transitions_gotname = {
    'state': 'gotname',
    '#EXISTINGUSER': {
        'error': {
            '#SO`i can recommend a movie or a song. which would you like?`': {
                '[{movie, movies, watch}]': 'movie',
                '[{music, song, songs, listen}]': 'song'
            }
        }
    }
}
transitions_movies = {
    'state': 'movie',
    '#FMOVIE': {
        '#WANTSDETAILS': {
            '#DETAILS': {
                '[song]': 'song',
                '#NEGATIVE': 'movie',
                'error': {
                    '#POSITIVE': {
                        '[{yes, yeah, sure, fine, ok, alright, please, another, again, -song}]': 'movie',
                        '[{music, song, album, artist, listen to}]': 'song',
                        'error': {
                            'score': 0.1,
                            '`goodbye!`': 'end'
                        }
                    }
                }
            }
        },
        '#NEGATIVE': 'movie',
        'error': {
            '#POSITIVE': {
                '[{yes, yeah, sure, fine, ok, alright, please, another, again, -song}]': 'movie',
                '[{music, song, album, artist, listen to}]': 'song',
                'error': {
                    'score': 0.1,
                    '`goodbye!`': 'end'
                }
            }
        }
    }
}
transitions_song = {
    'state': 'song',
    '`put a genre in quotation marks and i\'ll find something!`': {
        '#FORCENAME': {
            '#SONG': 'end'
        },
        'error': 'end'
    }
}
df = DialogueFlow('start', end_state='end')
df.add_macros(macros)
df.load_transitions(transitions)
df.load_transitions(transitions_gotname)
df.load_transitions(transitions_movies)
df.load_transitions(transitions_song)


# To be updated: create and add transitions, macros, and ontologies as needed

if __name__ == '__main__':
    df.run()
