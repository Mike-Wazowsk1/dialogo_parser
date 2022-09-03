import pandas as pd
import pymorphy2


def is_manager_good(greetings, goodbye):
    return 1 if (len(greetings) != 0 and len(goodbye) != 0) else 0


class RuleBased:
    """
    Based on rules.
    """

    def __init__(self, corpus, rules=None):
        if not rules:
            self.rules = {'greetings': ['здравствуйте', "добрый день",
                                        "привет", "добрый", "приветсвую", "здрасьте"],
                          'introduce': ['меня зовут', "мое имя", "обращайтесь ко мне",
                                        "можете звать меня", "зовите меня", "называйте меня",
                                        'меня зовут', 'меня', "да это"],
                          'names': ['ангелина', "дмитрий", "александр", "анастасия"],
                          'company_name': ["компании", "компания", 'компанию'],
                          'goodbye': ['досвидания', "до свидания", "пока",
                                      "всего хоршего", "всего доброго", "прощайте", "всех благ",
                                      "хорошего"]}
        else:
            self.rules = rules
        self.greetings = {}
        self.goodbye = {}
        self.manager_name = {}
        self.company_name = {}
        self.manager_introduce = {}
        self.data = corpus
        self.geeting_goodbye = {}
        self.data['greeting_goodbye'] = None
        self._diag()

    def _diag(self):
        self.d_count = len(self.data.groupby(by='dlg_id'))
        self.dialogs = self.data.groupby(by=['dlg_id', 'role'])

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
    def find_introduce(self, dig) -> pd.DataFrame:
        manager_name = dig[dig.text.str.lower().str.contains('|'. \
                                                             join(self.rules['introduce']))]

        return manager_name

    def find_name(self, dig):
        manager_name = dig[dig.text.str.lower().str.contains('|'. \
                                                             join(self.rules['introduce']))][:1]
        start = []
        l = []
        for x in self.rules['introduce']:
            if manager_name.text.str.lower().str.find(f'{x}').values > -1:
                start.append(manager_name.text.str.lower().str.find(f'{x}').values)
                l.append(len(x))

        string = manager_name.text.str[start[0][0] + l[0] + 1:].values[0].split()

        return ''.join(string[0]).capitalize()

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

    def get_manager_name(self):
        for i in range(self.d_count):
            try:
                self.manager_name[i] = self.find_name(self.dialogs.get_group((i, 'manager')))
            except:
                self.manager_name[i] = None
        return pd.DataFrame(self.manager_name.values(),
                            index=self.manager_name.keys(), columns=['manager_name'])

    def get_company_name(self):
        for i in range(self.d_count):
            try:
                self.company_name[i] = self.find_company(self.dialogs.get_group((i, 'manager')))
            except:
                self.company_name[i] = None
        return pd.DataFrame(self.company_name.values(),
                            index=self.company_name.keys(), columns=['company_name'])
