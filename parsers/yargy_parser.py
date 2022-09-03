import pandas as pd
import pymorphy2
from yargy import or_, rule, Parser
from yargy.interpretation import fact
from yargy.pipelines import morph_pipeline
from yargy.predicates import gram
from yargy.relations import gnc_relation
from yargy.tokenizer import MorphTokenizer


def is_manager_good(greetings, goodbye):
    return 1 if (len(greetings) != 0 and len(goodbye) != 0) else 0


class Yargyparser:
    """
    Based on Yargy rules.
    """

    def __init__(self, data, rules=None):
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
        self.data = data.copy()
        Name = fact(
            'Name',
            ['first', 'middle'])
        gnc = gnc_relation()

        FIRST = gram('Name').interpretation(
            Name.first.inflected()
        ).match(gnc)

        MIDDLE = gram('Patr').interpretation(
            Name.middle.inflected()
        ).match(gnc)

        NAME = or_(
            rule(
                FIRST,
                MIDDLE
            ),
            rule(
                FIRST)
        ).interpretation(
            Name
        )
        Cname = fact(
            'Cname',
            ['title', 'second']
        )
        TITLE = gram('NOUN').interpretation(
            Cname.title.inflected()
        ).match(gnc)
        SECOND = gram('NOUN').interpretation(
            Cname.second.inflected()
        ).match(gnc)
        CNAME = or_(
            rule(
                TITLE,
                SECOND,
            ),
            rule(
                TITLE
            )
        ).interpretation(
            Cname
        )
        Manager = fact(
            'Manager',
            ['type', 'name']
        )

        TYPE = morph_pipeline([
            'меня зовут',
            "мое имя",
            "а меня",
            "меня",
            "зовите меня",
            "я",
            "это"
        ]).interpretation(
            Manager.type.normalized()
        )

        MANAGER = or_(
            NAME,
            TITLE
        ).interpretation(
            Manager.name
        )

        MANAGER = rule(
            TYPE,
            MANAGER
        ).interpretation(
            Manager
        )
        Company = fact(
            'Company',
            ['type', 'name']
        )

        CTYPE = morph_pipeline([
            'компания',
            'компании',
            "компанию",
        ]).interpretation(
            Company.type
        )

        COMPANY = or_(
            CNAME,
            TITLE
        ).interpretation(
            Company.name
        )

        COMPANY = rule(
            CTYPE,
            COMPANY
        ).interpretation(
            Company
        )
        Proxy = fact('Proxy', ['value'])

        RULES = or_(
            MANAGER,
            COMPANY
        ).interpretation(Proxy.value).interpretation(Proxy)
        self.TOKENIZER = MorphTokenizer()
        self.parser = Parser(RULES, tokenizer=self.TOKENIZER)
        self.greetings = {}
        self.goodbye = {}
        self.manager_name = {}
        self.company_name = {}
        self.manager_introduce = {}
        self.geeting_goodbye = {}
        self.names = {}
        self.greeting = {}
        self.company = {}
        self.data['greeting_goodbye'] = None
        self._diag()

    def _diag(self):
        self.d_count = len(self.data.groupby(by='dlg_id'))
        self.dialogs = self.data.groupby(by=['dlg_id', 'role'])

    def find_names(self, dig):
        text = ' '.join(dig.text.str.lower())
        name, company = None, None
        for match in self.parser.findall(text):
            if type(match.fact.value.name).__name__ == 'Name':
                if match.fact.value.name.middle == None:
                    name = ''.join(match.fact.value.name.first)
                else:
                    name = ' '.join(match.fact.value.name)
            elif type(match.fact.value.name).__name__ == 'Cname':
                if match.fact.value.name.second == None:
                    company = ''.join(match.fact.value.name.title)
                else:
                    company = ' '.join(match.fact.value.name)
        return name, company

    def get_manager_name(self):
        for i in range(self.d_count):
            self.manager_name[i] = self.find_names(self.dialogs.get_group((i, 'manager')))[0]
        res = pd.DataFrame(self.manager_name.values(),
                           index=self.manager_name.keys(), columns=['manager_name'])
        res.index.name = 'dlg_id'
        return res

    def get_company_name(self):
        for i in range(self.d_count):
            self.company_name[i] = self.find_names(self.dialogs.get_group((i, 'manager')))[1]
        res = pd.DataFrame(self.company_name.values(),
                           index=self.company_name.keys(), columns=['company_name'])
        res.index.name = 'dlg_id'
        return res

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

        g = pd.concat(self.greetings, ignore_index=True)[['dlg_id', 'text']]
        g.columns = ['dlg_id', 'greeting']
        b = pd.concat(self.goodbye, ignore_index=True)[['dlg_id', 'text']]
        b.columns = ['dlg_id', 'goodbye']
        return g.set_index('dlg_id'), b.set_index('dlg_id')

    def get_manager_inroduce(self):
        for i in range(self.d_count):
            self.manager_introduce[i] = self.find_introduce(self.dialogs.get_group((i, 'manager')))
        intro = pd.concat(self.manager_introduce, ignore_index=True)[['dlg_id', 'text']]
        intro.columns = ['dlg_id', 'introduce']
        return intro.set_index('dlg_id')

    def get_manager_stats(self):
        if len(self.greetings) == 0:
            self.get_greetings_goodbye()
        res = pd.DataFrame(self.geeting_goodbye.values(),
                           index=self.geeting_goodbye.keys(), columns=['greeting_goodbye'])
        res.index.name = 'dlg_id'
        return res

    def overall(self):
        g, b = self.get_greetings_goodbye()
        g = g[~g.index.duplicated(keep='first')]
        b = b[~b.index.duplicated(keep='first')]
        i = self.get_manager_inroduce()
        i = i[~i.index.duplicated(keep='first')]
        n = self.get_manager_name()
        c = self.get_company_name()
        s = self.get_manager_stats()
        tmp = pd.concat([n, c, s], axis=1)
        res = pd.merge(tmp, g, left_index=True, right_index=True, how='left')
        res = pd.merge(res, b, left_index=True, right_index=True, how='left')
        res = pd.merge(res, i, left_index=True, right_index=True, how='left')
        return res
