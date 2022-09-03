# dialogo_parser
parse pd.DataFame with columns [dlg_id,role,text]

## Requirements

```bash
pip install -r requirements
```

## Usage

```bash
# return pd.DataFrame[dlg_id,manager_name] with yargy parser
python main.py  -d 'path/to/data/' -p 'yargy' -c 'manager_name' 

# return pd.DataFrame[dlg_id,manager_stats(has greeting & goodbye)] with rule based parser
python main.py  -d 'path/to/data/' -p 'rule_based' -c 'manager_stats' 

# return pd.DataFrame[dlg_id,text] of manager'sgreeting with natasha parser
python main.py  -d 'path/to/data/' -p 'natasha' -c 'greetings' 
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



