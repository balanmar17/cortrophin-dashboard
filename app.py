"""Cortrophin public-data portfolio project. Run: python -m streamlit run app.py"""
import pandas as pd
import plotly.express as px
import streamlit as st
from data_model import load_data

st.set_page_config(page_title='Cortrophin | Commercial Analytics', page_icon='📊', layout='wide')
st.markdown('''<style>
.stApp {background-color:#f5f7fb;}
h1,h2,h3 {color:#102b46;}
[data-testid="stMetric"] {background:white;border:1px solid #e0e7ef;border-radius:12px;padding:16px;}
.block-container {padding-top:2rem;max-width:1400px;}
</style>''', unsafe_allow_html=True)

CMS_SPEND = 'https://data.cms.gov/summary-statistics-on-use-and-payments/medicare-medicaid-spending-by-drug/medicare-part-d-spending-by-drug/'
CMS_RX = 'https://data.cms.gov/provider-summary-by-type-of-service/medicare-part-d-prescribers/medicare-part-d-prescribers-by-provider-and-drug'
ANI = 'https://investor.anipharmaceuticals.com/news-releases/news-release-details/ani-pharmaceuticals-reports-third-quarter-2026-financial-results'

try:
    annual, prescribers, revenue = load_data()
except (ValueError, KeyError, FileNotFoundError) as e:
    st.error(f'Unable to load project data: {e}')
    st.info('Keep app.py, data_model.py and all three CSV files in the same folder.')
    st.stop()

st.sidebar.title('Cortrophin')
st.sidebar.caption('COMMERCIAL ANALYTICS')
page = st.sidebar.radio('Explore', ['Overview', 'Prescriber profile', 'ANI business context'])
st.sidebar.divider()
st.sidebar.caption('Independent portfolio project based on public data. Not an official ANI report. No forecast or clinical recommendations.')
st.sidebar.caption('CMS: 2022–2024 • ANI: Q3 2026 report')

def chart(fig):
    fig.update_layout(template='plotly_white', paper_bgcolor='rgba(0,0,0,0)',
                      font=dict(family='Arial',color='#18354d'), margin=dict(l=15,r=15,t=40,b=20),
                      colorway=['#117c83','#305ca8','#d69b3a'], legend_title_text='')
    st.plotly_chart(fig, width='stretch', config={'displaylogo':False})

def download(df, name):
    st.download_button('Download displayed data (CSV)', df.to_csv(index=False).encode('utf-8-sig'), name, 'text/csv')

if page == 'Overview':
    st.title('Cortrophin | Medicare overview')
    st.caption('Medicare Part D • Annual utilization and spending • 2022–2024')
    year = st.selectbox('KPI year', annual['Year'].tolist(), index=len(annual)-1)
    r = annual.loc[annual.Year.eq(year)].iloc[0]
    def delta(col):
        val = r[col + ' growth (%)']
        return None if pd.isna(val) else f'{val:+.1f}% vs prior year'
    a,b,c = st.columns(3)
    a.metric('Total Part D spending', f"${r.Spending/1e6:,.2f}M", delta('Spending'),delta_color='off')
    b.metric('Claims, including refills', f'{r.Claims:,.0f}', delta('Claims'),delta_color='off')
    c.metric('Unique beneficiaries in year', f'{r.Beneficiaries:,.0f}', delta('Beneficiaries'),delta_color='off')
    st.caption('Spending is not ANI net revenue. Beneficiaries are distinct within each year; do not sum across years. KPI selection does not hide the historical charts.')
    left,right = st.columns(2)
    with left:
        plot = annual.assign(**{'Spending ($M)':annual.Spending/1e6})
        fig=px.bar(plot,x='Year',y='Spending ($M)',title='Annual Part D spending',text_auto='.2f')
        fig.update_xaxes(type='category'); chart(fig)
    with right:
        metric=st.selectbox('Utilization trend', ['Claims','Beneficiaries'])
        fig=px.line(annual,x='Year',y=metric,markers=True,title=f'Annual {metric.lower()}')
        fig.update_xaxes(type='category'); chart(fig)
    a,b=st.columns(2)
    a.metric('Average spending per claim', f"${r['Spending per claim']:,.0f}")
    b.metric('Average spending per beneficiary', f"${r['Spending per beneficiary']:,.0f}")
    st.info('Interpretation: spending can change with utilization and the mix of dispensed quantities. Spending per claim is not a list price, and claims do not identify treatment starts or clinical outcomes.')
    with st.expander('Annual data and calculation notes'):
        st.dataframe(annual.round(2),width='stretch',hide_index=True)
        download(annual,'cortrophin_annual_summary.csv')
        st.write('Year-over-year change = current year / previous year − 1. Average spending per claim and per beneficiary are recalculated from totals. Supplied growth/CAGR fields are excluded because their displayed percentage formatting is inconsistent with the underlying values. Weighted spending per dosage unit is retained as supplied; it is not replaced with an unweighted calculation.')
        st.write('All three supplied annual outlier flags are 0; this does not guarantee the absence of data errors.')
    st.markdown(f'Source: [CMS Part D Spending by Drug]({CMS_SPEND}). Definitions: supplied CMS data dictionary dated June 3, 2026.')

elif page == 'Prescriber profile':
    st.title('Cortrophin | Prescriber profile')
    st.caption('2024 • Published provider–drug records • Counts include non-physician prescribers')
    f1,f2=st.columns(2)
    states=f1.multiselect('States (empty = all)',sorted(prescribers.Prscrbr_State_Abrvtn.unique()))
    specialties=f2.multiselect('Specialties (empty = all)',sorted(prescribers.Prscrbr_Type.unique()))
    df=prescribers.copy()
    if states: df=df[df.Prscrbr_State_Abrvtn.isin(states)]
    if specialties: df=df[df.Prscrbr_Type.isin(specialties)]
    st.caption('Filters apply to this page only. Geography refers to the prescriber location, not the patient residence.')
    if df.empty:
        st.warning('No published records match this combination. Clear one or both filters.')
    else:
        a,b,c,d=st.columns(4)
        a.metric('Observed prescribers',f'{df.Prscrbr_NPI.nunique():,}')
        b.metric('Published claims',f'{df.Tot_Clms.sum():,.0f}')
        c.metric('Published claim costs',f'${df.Tot_Drug_Cst.sum()/1e6:,.2f}M')
        d.metric('States represented',f'{df.Prscrbr_State_Abrvtn.nunique():,}')
        st.warning('Incomplete national coverage: provider–drug records with fewer than 11 claims are excluded. Rankings describe published records only; no row for a state does not establish zero use.')
        metric=st.selectbox('Rank by', ['Claims','Observed prescribers','Claim costs ($M)'])
        def grouped(key):
            g=df.groupby(key).agg(Claims=('Tot_Clms','sum'),**{'Observed prescribers':('Prscrbr_NPI','nunique'),'Cost':('Tot_Drug_Cst','sum')}).reset_index()
            g['Claim costs ($M)']=g.Cost/1e6
            return g.sort_values(metric,ascending=True)
        left,right=st.columns(2)
        with left:
            g=grouped('Prscrbr_Type')
            fig=px.bar(g,x=metric,y='Prscrbr_Type',orientation='h',title='Specialty distribution',labels={'Prscrbr_Type':''})
            fig.update_layout(height=450);chart(fig)
        with right:
            g=grouped('Prscrbr_State_Abrvtn').tail(15)
            fig=px.bar(g,x=metric,y='Prscrbr_State_Abrvtn',orientation='h',title='Top states in selected records (up to 15)',labels={'Prscrbr_State_Abrvtn':''})
            fig.update_layout(height=450);chart(fig)
        with st.expander('Filtered records and data quality'):
            st.write(f"Beneficiary counts are suppressed in {df.Tot_Benes.isna().sum()} of {len(df)} selected rows. Missing values remain missing. Beneficiaries are not aggregated across prescribers.")
            st.dataframe(df,hide_index=True,width='stretch')
            download(df,'cortrophin_filtered_prescribers_2024.csv')
    with st.expander('Coverage check — full supplied file, unaffected by filters'):
        total=annual.loc[annual.Year.eq(2024)].iloc[0]
        st.write(f"The full prescriber file contains {prescribers.Tot_Clms.sum():,.0f} claims versus {total.Claims:,.0f} in the drug-level total ({100*prescribers.Tot_Clms.sum()/total.Claims:.1f}%). Its ${prescribers.Tot_Drug_Cst.sum()/1e6:.2f}M of costs represents {100*prescribers.Tot_Drug_Cst.sum()/total.Spending:.1f}% of the drug-level spending total.")
        st.write('These are descriptive reconciliation ratios, not market shares. Suppression is an important reason detailed records do not sum to national totals; the exports do not independently prove the full cause of every difference.')
        st.write('54 unique NPIs; no duplicate NPI rows in the supplied file. Original names and cities were omitted from the prepared project data. NPI is kept as a text identifier. The supplied provider dictionary is an older RY22 version; its core definitions match the fields used, but the project has not independently validated every definition against the 2024 methodology.')
    st.markdown(f'Source: [CMS Part D Prescribers by Provider & Drug]({CMS_RX}). The supplied CMS screenshot confirms the 2024 selection and 54 search results.')

else:
    st.title('ANI | Business context')
    st.caption('Q3 2026 versus Q3 2025 • Company-reported net revenue • Report published November 5, 2026')
    a,b,c=st.columns(3)
    for col, product in zip([a,b,c], ['Cortrophin Gel','ILUVIEN','ANI total']):
        vals=revenue[revenue.Product.eq(product)].set_index('Year').Net_Revenue_USD
        col.metric(product,f'${vals[2026]/1e6:,.2f}M',f'{100*(vals[2026]/vals[2025]-1):+.1f}% YoY',delta_color='off')
    st.caption('ANI total includes the products shown and other business lines. Do not add the total to individual product revenues.')
    chart_data=revenue[revenue.Product.ne('ANI total')].copy()
    chart_data['Net revenue ($M)']=chart_data.Net_Revenue_USD/1e6
    chart_data['Year']=chart_data.Year.astype(str)
    chart(px.bar(chart_data,x='Product',y='Net revenue ($M)',color='Year',barmode='group',text_auto='.2f',title='Product net revenue: same-quarter comparison'))
    left,right=st.columns(2)
    with left:
        st.subheader('2026 Cortrophin guidance')
        st.metric('Full-year net revenue forecast', '$480–500M')
        st.caption('Management guidance as of November 5, 2026. Not actual full-year revenue and not a forecast generated by this dashboard.')
    with right:
        st.subheader('Commercial context')
        st.write('ANI reported capacity constraints in its specialty pharmacy network that slowed conversion of demand into patients on therapy. It described expanding the network and patient support capabilities.')
        st.write('Follow-up question: which access stages account for the longest delays? Answering it requires internal operational data, unavailable in these CMS files.')
    st.info('Separate evidence: CMS panels cover Medicare Part D in 2022–2024; this page covers company net revenue in Q3 2025 and Q3 2026. Do not calculate a Medicare share of ANI revenue or infer that the older CMS trends caused the later company results.')
    with st.expander('Reported financial data'):
        st.dataframe(revenue,hide_index=True,width='stretch')
        download(revenue,'ani_q3_revenue_comparison.csv')
        st.write('Values were transcribed from the report’s Third Quarter 2026 Financial Results table. Original units were thousands of dollars; values here are multiplied by 1,000. Only Q3 figures are included, not nine-month totals.')
    st.markdown(f'Source: [ANI Q3 2026 financial results]({ANI}).')

st.divider()
st.caption('Scope: descriptive analytics only • Public CMS exports and ANI financial disclosures • No patient-level records • Prepared for an interview portfolio')
