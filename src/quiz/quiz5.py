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
__author__ = 'Jinho D. Choi'
import random
from enum import Enum
from typing import Dict, List, Any
from datetime import datetime
from emora_stdm import DialogueFlow, Macro, Ngrams
import sys
import os

sys.path.insert(0, os.path.dirname(sys.path[0]))
sys.path.insert(0, os.path.dirname(sys.path[0]))
from src.utils import MacroGPTJSON, MacroNLG

class U(Enum):
    service = 0 # str
    time = 1


transitions = {
    'state': 'start',
    '`Hello, how can I help you?`': {
        # TODO: to be filled.
    }
}

def set_service(vars:Dict[str, Any], user: Dict[str,Any]):
    if user['service'] == 'N/A':
        raise Exception("invalid service")
    vars["service"] = user["service"]
def set_time(vars:Dict[str, Any], user: Dict[str,Any]):
    vars['time'] = user['time']
def get_time(vars: Dict[str, Any]):
    return vars['time']
def get_service(vars:Dict[str,Any], user: Dict[str,Any]):
    return vars["service"]
def get_compatible_times(times, service, whitelist):
    availables = whitelist[service]
    outs = list()
    for time in times:
        formatted = (time['day'], time['time'])
        for opening in availables:
            if formatted == opening:
                outs.append(formatted)
    return outs

keytoword = {
    "haircut": "haircuts are our bread and butter!",
    "haircolor": "let\'s dye your hair!",
    "perms": "we can do a perm."
}

whitelist = {
    'haircut': [
    ("Monday","10:00"),
    ("Monday", "13:00"),
    ("Monday", "14:00"),
    ("Tuesday", "14:00")
    ],
    'haircolor': [
        ("Wednesday", "10:00"),
        ("Wednesday", "11:00"),
        ("Wednesday", "13:00"),
        ("Thursday", "10:00"),
        ("Thursday", "11:00")
    ],
    'perms': [
        ("Friday", "10:00"),
        ("Friday", "11:00"),
        ("Friday", "13:00"),
        ("Friday", "14:00"),
        ("Saturday", "10:00"),
        ("Saturday", "14:00")
    ]
}
class MacroRespondService(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if 'serviceresponse' in vars:
            return ""
        else:
            vars['serviceresponse'] = True
            return keytoword[vars['service']] + " so,"
class MacroTimeWorks(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        matches = get_compatible_times(vars["time"], vars["service"], whitelist)
        if len(matches) > 0:
            vars['time'] = matches[0]
            return True
        else:
            return False

class MacroSayTimeWorks(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        day, time = vars['time']
        return f"we can see you on {day.lower()} at {datetime.strptime(time,'%H:%M').strftime('%I:%M %p').lower()}. see you soon!"
macros = {
        'GET_SERVICE': MacroNLG(get_service),
        'SERVICE': MacroRespondService(),
        'TIMEWORKS': MacroTimeWorks(),
        'SAYTIMEWORKS': MacroSayTimeWorks(),
        'SET_SERVICE': MacroGPTJSON(
            'Out of the following three options, which service does the speaker want? [\'haircut\', \'perms\',\'haircolor\']',
            {'service': "haircut"}, {'service': 'N/A'}, set_service),
        'SET_TIME': MacroGPTJSON(
            'What times, in day of the week and time, did the speaker say they were available for an appointment? Do not return an outcome if the time is not reflected in the given statement.',
            {'time': [{"day": "Monday", "time": "14:00"}, {"day": "Friday", "time": "10:00"}]}, {'time': []}, set_time),
    }
transitions = {
    'state':'start',
    '`welcome to the salon! what are you coming in to do? we can get you an appointment set up...`': {
        '#SET_SERVICE': {
            'state': 'times',
            '#SERVICE` when works for you?`': {
                '#SET_TIME #TIMEWORKS': {
                    '#SAYTIMEWORKS': 'end'
                },
                'error': {
                    '`don\'t think that works for us. can we try another time?`': 'times'
                }
            },
            'error': {
                '`sorry, we don\'t do that here. have a good one...`': 'end'
            }
        },
        'error': {
            '`sorry, we don\'t do that here. have a good one...`': 'end'
        }
    }
}


df = DialogueFlow('start', end_state='end')
df.load_transitions(transitions)
df.add_macros(macros)

if __name__ == '__main__':
    df.run()