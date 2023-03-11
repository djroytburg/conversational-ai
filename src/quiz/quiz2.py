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
__author__ = 'Jinho Choi, Dani Roytburg'
from emora_stdm import DialogueFlow

transitions = {
    'state': 'start',
    '`Hi there! How can I help you?`': {
        '[{haircut, [hair, cut], [cut, hair]}]': {
            '`Let\'s get you a haircut! What times are you looking for?`': {
                '{[monday, 10 am], [monday, 1 pm], [monday, 2 pm], [tuesday, 2 pm]}': {
                    '`Unfortunately, we cannot accommodate that time. Please re-book with a different date. We appreciate your understanding.`': 'end'
                },
                'error': {
                    '`Great! We\'ve got that appointment set up for you. We look forward to seeing you soon!`': 'end'
                }
            }
        },
        '[{[color, hair], [hair, coloring]}]' : {
            '`We can do that for you! What times were you looking at for that?`': {
                '{[wednesday, 10 am], [wednesday, 11 am], [wednesday, 1 pm], [thursday, 10 am], [thursday, 11 am]}': {
                    '`Unfortunately, we cannot accommodate that time. Please re-book with a different date. We appreciate your understanding.`': 'end'
                },
                'error': {
                    '`Great! We\'ve got that appointment set up for you. We look forward to seeing you soon!`': 'end'
                }
            }
        },
        '[{perm, perms}]' : {
            '`We can do that for you! What times were you looking at for that?`': {
                '{[friday, 10 am], [friday, 11 am], [friday, 1 pm], [friday, 2 pm], [Saturday, 10 am], [Saturday, 2 pm]}': {
                    '`Unfortunately, we cannot accommodate that time. Please re-book with a different date. We appreciate your understanding.`': 'end'
                },
                'error': {
                    '`Great! We\'ve got that appointment set up for you. We look forward to seeing you soon!`': 'end'
                }
            }
        },
        'error': {
            '`I\'m sorry -- either you\'ve requested a service that we do not offer, or we cannot understand your request.\n'
            'We provide haircuts, hair colorings, and perms. Can we start over?\n`': 'start'
        }
    }
}

df = DialogueFlow('start', end_state='end')
df.load_transitions(transitions)

if __name__ == '__main__':
    df.run()