"""Data preparation. CMS costs and ANI net revenue remain separate measures."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent

def number(value):
    if pd.isna(value) or not str(value).strip():
        return float('nan')
    return float(str(value).replace('$', '').replace(',', '').strip())

def load_data():
    raw = pd.read_csv(ROOT / 'spending.csv', dtype=str)
    if len(raw) != 1 or raw.iloc[0]['Brnd_Name'].lower() != 'cortrophin':
        raise ValueError('spending.csv must contain exactly one Cortrophin manufacturer row; check aggregation before adding rows.')
    row = raw.iloc[0]
    years = sorted(int(c.rsplit('_', 1)[1]) for c in raw if c.startswith('Tot_Spndng_'))
    annual = pd.DataFrame([{
        'Year': y,
        'Spending': number(row[f'Tot_Spndng_{y}']),
        'Claims': number(row[f'Tot_Clms_{y}']),
        'Beneficiaries': number(row[f'Tot_Benes_{y}']),
        'Weighted spending per dosage unit': number(row[f'Avg_Spnd_Per_Dsg_Unt_Wghtd_{y}']),
        'Outlier flag': number(row[f'Outlier_Flag_{y}']),
    } for y in years])
    annual['Spending per claim'] = annual['Spending'] / annual['Claims']
    annual['Spending per beneficiary'] = annual['Spending'] / annual['Beneficiaries']
    for col in ['Spending', 'Claims', 'Beneficiaries']:
        annual[col + ' growth (%)'] = annual[col].pct_change(fill_method=None) * 100
    prescribers = pd.read_csv(ROOT / 'prescribers_2024.csv', dtype=str)
    required = ['Prscrbr_NPI','Prscrbr_State_Abrvtn','Prscrbr_Type','Brnd_Name','Tot_Clms','Tot_Drug_Cst','Tot_Benes']
    if not set(required).issubset(prescribers):
        raise ValueError('Missing prescriber columns.')
    if prescribers['Prscrbr_NPI'].duplicated().any():
        raise ValueError('Duplicate prescriber IDs: review data before aggregating.')
    if not prescribers['Brnd_Name'].str.lower().eq('cortrophin').all():
        raise ValueError('Only Cortrophin rows are supported in this project.')
    for col in ['Tot_Clms', 'Tot_Drug_Cst', 'Tot_Benes']:
        prescribers[col] = prescribers[col].map(number)
    if prescribers[['Tot_Clms','Tot_Drug_Cst']].isna().any().any():
        raise ValueError('Missing core prescriber measures.')
    if (prescribers['Tot_Clms'] < 11).any():
        raise ValueError('Unexpected claim counts below the published inclusion threshold.')
    revenue = pd.read_csv(ROOT / 'ani_revenue.csv')
    return annual, prescribers, revenue
