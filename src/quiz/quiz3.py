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

from emora_stdm import Macro, Ngrams, DialogueFlow
from typing import Dict, Any, List
import pandas as pd
import json
import ast
import re
import random
import spacy

nlp = spacy.load("en_core_web_trf")


class MacroName(Macro):
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


metadata = pd.read_csv("https://media.githubusercontent.com/media/djroytburg/quiz3/main/quiz3/movies_metadata.csv")
keywords = pd.read_csv("https://media.githubusercontent.com/media/djroytburg/quiz3/main/quiz3/keywords.csv")
class MacroMovie(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        output = vars['__raw_user_utterance__'].lower().replace(",", "").replace(".", "").replace(":", "")
        search = re.search(r'"([^"]+)"', output)
        if search is None:
            print("hey, you didn't say anything!")
            vars['__state__'] = 'nomovie'
            return False
        vars['user_description'] = search.group(1)
        filter = search.group(1).split()
        one_word = False
        if len(filter) == 1:
            one_word = True
        mask = [all(word in title for word in filter) for title in metadata['title1']]
        if one_word:
            mask = [title == filter[0] for title in metadata['title1']]
        moviename = metadata.loc[mask]
        if len(moviename) == 0:
            vars['__state__'] = 'dontknow'
            return False
        if len(moviename) > 50:
            print("i have too many results for you!")
            vars['__state__'] = 'nomovie'
            return False
        vars['results'] = moviename
        vars['pickid'] = list(moviename['title1'])[0]
        genras = dict()
        keys = dict()
        for index, row in moviename.iterrows():
            loss = list()
            thing = row['genres']
            name = row['title1']
            genras[name] = json.loads(thing.replace("'", '"'))
            try:
                keys[name] = json.loads(keywords.loc[index]['keywords'].replace("'", '"'))
                keys[name] = [tok['name'] for tok in keys[name]]
            except:
                loss.append(keywords.loc[index]['keywords'].replace("'", '"'))
        for key in genras.keys():
            genres = [tok['name'] for tok in genras[key]]
            genras[key] = genres
        vars['genres'] = genras
        vars['keywords'] = keys
        cast = pd.read_csv("https://media.githubusercontent.com/media/djroytburg/quiz3/main/quiz3/credits.csv")
        id = int(moviename.iloc[0].name)
        vars['characters'] = [(x['name'], x['character']) for x in ast.literal_eval(cast.loc[id]['cast'])]
        return True


class MacroRespondName(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if 'name' not in vars:
            return "I missed your name!"


class MacroAboutGenre(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        responses = ['i love #GENRE movies like that! what\'s your favorite genre?',
                     'no way! those #GENRE movies are my favorite!  what\'s your favorite genre?',
                     'seems like you are a big fan of #GENRE movies, no?  what\'s your favorite genre?',
                     'that\'s a #GENRE movie, right?  what\'s your favorite genre?']
        genres = vars['genres']
        # print(genres[vars['pickid']])
        selection = random.choice(genres[vars['pickid']]).lower()
        while selection == 'drama' and len(genres[vars['pickid']]) > 1:
            selection = random.choice(genres[vars['pickid']]).lower()
        return random.choice(responses).replace("#GENRE", selection)


class MacroGetDemonym(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        doc = nlp(vars["__user_utterance__"])
        if len(doc.ents) == 0:
            return False
        else:
            culture = [thing.text for thing in doc.ents if thing.label_ == "NORP"]
            if len(culture) == 0:
                return False
            else:
                vars['culture'] = culture[0]
                return True


class MacroGetCulture(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if 'culture' not in vars:
            raise Exception("went to culture without demonym present!")
        else:
            return vars['culture']


class MacroGetName(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        return vars['user_description']


class MacroGetA(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if 'once' in vars:
            return "another"
        else:
            vars['once'] = True
            return "a"


class MacroGiveCharacters(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        picks = random.sample(vars['characters'][0:5], 2)
        a = random.randint(0, 1)
        better, worse = picks[a], picks[1 - a]
        betact, betchar = better
        woract, worchar = worse
        return f"did you like {betact.lower()}'s performance?"


transitions = {
    'state': 'start',
    '`hey! :)\nnice to meet you! what\'s your name?`': {
        '#NAME': {
            '#NAME`-- what a beautiful name!\ni\'m teevee, a bot that likes to talk about movies.`': 'getmovie'
        },
        'error': {
            '`sorry, i didn\'t catch that, i\'m sorry :(. let\'s start over.`': {
                'error': 'start'
            }
        }
    }
}
transitions_get_movie = {
    'state': 'getmovie',
    '`\ntell me about`#A`movie you\'ve seen! use proper citation and enclose its name in quotes.`': {
        '#MOVIE': {
            '#GETGENRE': {
                '[#ONT(scifi)]': {
                    '`i love sci-fi films too!`': 'actor'
                },
                '[#ONT(superhero)]': {
                    '`those are cool, i like marvel movies best!`': 'actor'
                },
                '[#ONT(romcom)]': {
                    '`rom coms melt my heart!`': 'actor'
                },
                '[#ONT(fantasy)]': {
                    '`honestly, i was just being nice. those movies are kinda weird to me...`': 'actor'
                },
                '[#ONT(horror)]': {
                    '`you like being scared, i get it!`': 'actor'
                },
                '[#ONT(comedy)]': {
                    '`i like comedies too!`': 'actor'
                },
                '#IF(#DEMONYM)': {
                    '`That\'s awesome, what ties you to`#CULTURE`culture?`': {
                        'error': {
                            '`did`#WATCHED`make you think about`#CULTURE`film?`': {
                                'error': {
                                    '`i see. anyways,`': 'actor'
                                }
                            }
                        }
                    }
                },
                '#UNX': 'actor'
            }
        },
        'error': {
            'state': 'nomovie',
            '`i got my wires crossed! could you repeat that?`': 'getmovie',
            'state': 'dontknow',
            '`i don\'t know that one! could you tell me about it?`': {
                '#UNX': 'getmovie'
            }
        }
    }
}
transitions_actor = {
    'state': 'actor',
    '#ACTOR': {
        'error': {
            '`just maybe i\'ll watch now. have a good one`#NAME`!`': 'end'
        }
    }
}
macros = {
    'NAME': MacroName(),
    'MOVIE': MacroMovie(),
    "GETGENRE": MacroAboutGenre(),
    "DEMONYM": MacroGetDemonym(),
    "CULTURE": MacroGetCulture(),
    "WATCHED": MacroGetName(),
    "ACTOR": MacroGiveCharacters(),
    "A": MacroGetA()
}

df = DialogueFlow('start', end_state='end')
df.load_transitions(transitions)
df.load_transitions(transitions_get_movie)
df.load_transitions(transitions_actor)
df.knowledge_base().load_json_file('resources/quiz3/ontology_quiz3.json')
df.add_macros(macros)

if __name__ == '__main__':
    df.run()
