import pandas as pd

from parsers.yargy_parser import Yargyparser
from parsers.natasha_parser import Natasha
from parsers.rule_based_parser import RuleBased

import argparse

par = argparse.ArgumentParser()
par.add_argument("-p", "--parser", type=str, default='yargy', choices=['yargy', 'natasha', 'rule_based'],
                    required=True,
                    help='Select parser')
par.add_argument("-d", "--data", type=str, required=True, help='Select data path')
par.add_argument('-c', '--command', choices=['manager_name', 'company_name', 'manager_stats', 'greetings', 'goodbye',
                                                'introduce'])
par.add_argument('-r', '--rules', help='Add rules to models in dict type', default=None)
args = par.parse_args()
data = pd.read_csv(args.data)
if args.rules is None:
    rules = None
else:
    rules = args.rules
if args.parser == 'yargy':
    model = Yargyparser(data, rules)
elif args.parser == 'natasha':
    model = Natasha(data, rules)
else:
    model = RuleBased(data, rules)

if args.command == 'manager_name':
    print(model.get_manager_name())
elif args.command == 'company_name':
    print(model.get_company_name())
elif args.command == 'manager_stats':
    print(model.get_manager_stats())
elif args.command == 'greetings':
    print(model.get_greetings_goodbye()[0])
elif args.command == 'goodbye':
    print(model.get_greetings_goodbye()[1])
elif args.command == 'introduce':
    print(model.get_manager_inroduce())