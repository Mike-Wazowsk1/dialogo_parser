# dialogo_parser
Parse DataFrame with columns:
* dlg_id
* role
* text

Parsers description at [jupyter](https://github.com/Mike-Wazowsk1/dialogo_parser/blob/master/Parsers_info.ipynb)

## Requirements

```bash
pip install -r requirements
```

## Usage
### Bash
```bash
# return pd.DataFrame[dlg_id,manager_name] with yargy parser
python main.py  -d 'path/to/data/' -p 'yargy' -c 'manager_name' 

# return pd.DataFrame[dlg_id,manager_stats(has greeting & goodbye)] with rule based parser
python main.py  -d 'path/to/data/' -p 'rule_based' -c 'manager_stats' 

# return pd.DataFrame[dlg_id,text] of manager's greeting with natasha parser
python main.py  -d 'path/to/data/' -p 'natasha' -c 'greetings' 
```
### Python
```python

from parsers.yargy_parser import Yargyparser
from parsers.natasha_parser import Natasha
from parsers.rule_based_parser import RuleBased

data = pd.read_csv(data.csv)
parser = RuleBased(data)

# all returns pd.DataFrame
introduction = parser.get_manager_inroduce()
manager_name = parser.get_manager_name()
cname = parser.get_company_name()
stats = parser.get_manager_stats()

# return pd.DataFrame[dlg_id,text] of greetings and pd.DataFrame[dlg_id,text] od goodbye
hello, bye = parser.get_greetings_goodbye()

```

## Commands 

```python
c = 'manager_name','company_name', 'introduce', 'manager_stats', 'greetings', 'goodbye', 'introduce'
e = 'yargy', 'natasha', 'rule_based'
r [OPTIONAL] =  {'greetings': list[str],
                 'introduce': list[str],
                 'company_name': list[str],
                 'goodbye': list[str],
                 }

```
## Tips
Do not use Natasha parser. It doen't work with lowercase words and for preprocess need to capitalize entity(take a lot of time).
