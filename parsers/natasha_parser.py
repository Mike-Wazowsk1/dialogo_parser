import os
import re

import pandas as pd
import pymorphy2
import torch
import yaml
from navec import Navec
from slovnet import NER
from torch import package


def is_manager_good(greetings, goodbye):
    return 1 if (len(greetings) != 0 and len(goodbye) != 0) else 0


def make_first_lowercase(x):
    return ''.join(x.split()[0].lower()) + ' ' + ' '.join(x.split()[1:])


class Natasha:
    def __init__(self, corpus, path_novec='navec_news_v1_1B_250K_300d_100q.tar', path_ner='slovnet_ner_news_v1.tar',
                 rules=None):
        if not rules:
            self.rules = {'greetings': ['здравствуйте', "добрый день",
                                        "привет", "добрый", "приветсвую", "здрасьте"],
                          'introduce': ['меня зовут', "мое имя", "обращайтесь ко мне",
                                        "можете звать меня", "зовите меня", "называйте меня",
                                        'меня зовут', 'меня', "да это"],
                          'company_name': ["компании", "компания", 'компанию'],
                          'goodbye': ['досвидания', "до свидания", "пока",
                                      "всего хоршего", "всего доброго", "прощайте", "всех благ",
                                      "хорошего"]}
        else:
            self.rules = rules

        self.data = corpus
        self.data['greeting_goodbye'] = None
        self.navec = Navec.load(path_novec)
        self.ner = NER.load(path_ner)
        self.ner.navec(self.navec)
        self.data = corpus.copy()
        self.greetings = {}
        self.goodbye = {}
        self.manager_name = {}
        self.company_name = {}
        self.manager_introduce = {}
        self.geeting_goodbye = {}
        self.names = {}
        self.greeting = {}
        self.company = {}
        self._init_silero()
        self.data.text = self.data.text.str.replace('+', 'plus').str.lower().apply(self.make_capitalize).apply(
            make_first_lowercase)
        self._diag()

    def _diag(self):
        self.d_count = len(self.data.groupby(by='dlg_id'))
        self.dialogs = self.data.groupby(by=['dlg_id', 'role'])

    def _init_silero(self, pre_download=True):
        if not pre_download:
            torch.hub.download_url_to_file('https://raw.githubusercontent.com/snakers4/silero-models/master/models.yml',
                                           'latest_silero_models.yml',
                                           progress=False)
        with open('latest_silero_models.yml', 'r') as yaml_file:
            models = yaml.load(yaml_file, Loader=yaml.SafeLoader)
        model_conf = models.get('te_models').get('latest')
        model_url = model_conf.get('package')

        model_dir = "downloaded_model"
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, os.path.basename(model_url))

        pack = package.PackageImporter(model_path)
        self.model = pack.load_pickle("te_model", "model")

    def make_capitalize(self, text, lan='ru'):
        return self.model.enhance_text(text, lan)


        # Проверям поздоровался ли манагер

    def fing_greetings(self, dig):
        manager_greetings = dig[dig.text.str.lower().str.contains('|'. \
                                                                  join(self.rules['greetings']))]
        return manager_greetings

    # Проверяем попращался ли манагер
    def find_goodbye(self, dig):
        manager_goodbye = dig[dig.text.str.lower().str.contains('|'. \
                                                                join(self.rules['goodbye']))]
        return manager_goodbye

    # Ищем имя манагера
    def find_introduce(self, dig):
        manager_name = dig[dig.text.str.lower().str.contains('|'. \
                                                             join(self.rules['introduce']))]

        return manager_name

    # Ищем название компании
    def find_company(self, dig):
        company_name = dig[dig.text.str.lower().str.contains('|'. \
                                                             join(self.rules['company_name']))][:1]

        start = [company_name.text.str.lower().str.find(f'{x}').values for x \
                 in self.rules['company_name'] if company_name.text.str.find(f'{x}').values > -1]

        string = company_name.text.str[start[0][0] + 9:].values[0].split()

        morph = pymorphy2.MorphAnalyzer()
        name = []
        for i in range(len(string)):
            if morph.parse(string[i])[0].normal_form == string[i] and 'ADVB' not in morph.parse(string[i])[0].tag:
                name.append(string[i])
            else:
                break
        return ' '.join(name).capitalize()

    def get_manager_name(self):
        for i in range(self.d_count):
            data = self.dialogs.get_group((i, 'manager'))
            tmp = data.text
            string = ' '.join(tmp)
            markup = self.ner(string)
            name_spans = [string[x.start:x.stop] for x in markup.spans if
                          x.type == 'PER' and re.search(f"{'|'.join(self.rules['introduce'])}",
                                                        string[x.start - 15 if x.start - 15 > 0 else 0:x.stop])]
            if len(name_spans) > 0:
                self.names[i] = name_spans[0]
            else:
                self.names[i] = None
        return pd.DataFrame(self.names.values(),
                            index=self.names.keys(), columns=['manager_name'])

    def get_greetings_goodbye(self):
        """
        make two dataframes: greetings and goodbyes. fill column greeting_goodbye
        return: DataFrame of greetings and DataFrame of goodbyes
        """
        for i in range(self.d_count):
            self.greetings[i] = self.fing_greetings(self.dialogs.get_group((i, 'manager')))
            self.goodbye[i] = self.find_goodbye(self.dialogs.get_group((i, 'manager')))
            self.geeting_goodbye[i] = is_manager_good(self.greetings.get(i, []),
                                                      self.goodbye.get(i, []))
            self.data.loc[self.data.dlg_id == i, 'greeting_goodbye'] = is_manager_good(
                self.greetings.get(i, []), self.goodbye.get(i, []))

        return pd.concat(self.greetings, ignore_index=True)[['dlg_id','text']], pd.concat(self.goodbye, ignore_index=True)[['dlg_id','text']]

    def get_manager_inroduce(self):
        for i in range(self.d_count):
            self.manager_introduce[i] = self.find_introduce(self.dialogs.get_group((i, 'manager')))
        return pd.concat(self.manager_introduce, ignore_index=True)[['dlg_id','text']]

    def get_manager_stats(self):
        if len(self.greetings) == 0:
            self.get_greetings_goodbye()
        return pd.DataFrame(self.geeting_goodbye.values(),
                            index=self.geeting_goodbye.keys(), columns=['greeting_goodbye'])

    def get_company_name(self):
        for i in range(self.d_count):
            try:
                self.company_name[i] = self.find_company(self.dialogs.get_group((i, 'manager')))
            except:
                self.company_name[i] = None
        return pd.DataFrame(self.company_name.values(),
                            index=self.company_name.keys(), columns=['company_name'])
