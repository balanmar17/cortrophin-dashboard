"""Cortrophin Gel public-data portfolio project. Run: python -m streamlit run app.py"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
import plotly.io as pio
from data_model import load_data

st.set_page_config(page_title='ANI | Products & Financial Results', page_icon='📊', layout='wide')
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

st.sidebar.title('ANI Pharmaceuticals')
st.sidebar.caption('PRODUCTS & FINANCIAL RESULTS')
page = st.sidebar.radio('Explore', ['Overview', 'Prescriber profile', 'ANI Financial Results'])
st.sidebar.divider()
st.sidebar.caption('Independent portfolio project based on public data. Not an official ANI report.')
st.sidebar.caption('Prepared by Marina Balan  \nLast updated: November 14, 2026')

def chart(fig):
    fig.update_layout(template='plotly_white', paper_bgcolor='rgba(0,0,0,0)',
                      font=dict(family='Arial',color='#18354d'), margin=dict(l=15,r=15,t=40,b=20),
                      colorway=['#117c83','#305ca8','#d69b3a'], legend_title_text='')
    annotations=list(fig.layout.annotations or [])
    growth_pairs=[]
    for i,arrow in enumerate(annotations[:-1]):
        label=annotations[i+1]
        if arrow.showarrow and not label.showarrow and any(t in (label.text or '') for t in ['%</b>','Projected growth:']):
            # Preserve data-coordinate endpoints directly above the two bar centers.
            label.update(x=(arrow.x+arrow.ax)/2,y=(arrow.y+arrow.ay)/2,
                         xref='x',yref='y',xanchor='center',yanchor='middle',
                         bgcolor='rgba(0,0,0,0)',yshift=18)
            growth_pairs.append([i,i+1])
    if growth_pairs:
        # Measure the rendered axes to match the label angle on every screen size.
        # This changes labels only: the arrows remain attached to data coordinates.
        import json
        script="""
        const gd = document.getElementById('{plot_id}');
        const pairs = PAIRS;
        let busy = false;
        function alignLabels() {
            if (busy || !gd._fullLayout) return;
            const xa=gd._fullLayout.xaxis, ya=gd._fullLayout.yaxis;
            const changes={};
            pairs.forEach(([ai,li]) => {
                const a=gd.layout.annotations[ai], l=gd.layout.annotations[li];
                const dx=xa.l2p(a.x)-xa.l2p(a.ax);
                const dy=ya.l2p(a.y)-ya.l2p(a.ay);
                const angle=Math.atan2(dy,dx)*180/Math.PI;
                const rad=angle*Math.PI/180;
                const xs=18*Math.sin(rad), ys=18*Math.cos(rad);
                if (Math.abs((l.textangle||0)-angle)>.05 || Math.abs((l.xshift||0)-xs)>.05 || Math.abs((l.yshift||0)-ys)>.05) {
                    changes[`annotations[${li}].textangle`]=angle;
                    changes[`annotations[${li}].xshift`]=xs;
                    changes[`annotations[${li}].yshift`]=ys;
                }
            });
            if(Object.keys(changes).length) {
                busy=true;
                Plotly.relayout(gd,changes).then(()=>{busy=false;});
            }
        }
        gd.on('plotly_afterplot',alignLabels);
        alignLabels();
        new ResizeObserver(()=>{Plotly.Plots.resize(gd);}).observe(gd.parentElement);
        """.replace('PAIRS',json.dumps(growth_pairs))
        html=pio.to_html(fig,include_plotlyjs=True,full_html=False,
                         config={'displaylogo':False,'responsive':True},post_script=script)
        components.html('<style>body{margin:0;background:transparent;}</style>'+html,
                        height=int(fig.layout.height or 410)+10,scrolling=False)
    else:
        st.plotly_chart(fig,width='stretch',config={'displaylogo':False})

def download(df, name):
    st.download_button('Download displayed data (CSV)', df.to_csv(index=False).encode('utf-8-sig'), name, 'text/csv')

st.markdown("""<style>
.stApp {background:linear-gradient(135deg,#f0f8fa 0%,#f6f5fc 55%,#f5f7fb 100%);}
[data-testid="stMetric"] {border:1px solid #dce8ee;border-top:4px solid #13989b;
  box-shadow:0 5px 18px rgba(28,57,87,.05);border-radius:14px;}
[data-testid="stMetricValue"] {color:#123c58;}
.overview-label {color:#127e87;font-weight:700;letter-spacing:2px;font-size:12px;margin-bottom:6px;}
.overview-intro {background:linear-gradient(110deg,#e2f4f3,#eaf0fc);border-left:4px solid #13989b;
  border-radius:14px;padding:20px 24px;color:#27455b;line-height:1.65;margin:12px 0 22px;}
.overview-intro p {margin:0 0 10px;}
.overview-intro p:last-child {margin-bottom:0;}
</style>""", unsafe_allow_html=True)

if page == 'Overview':
    st.markdown('<div class="overview-label">CORTROPHIN GEL / MEDICARE PART D</div>', unsafe_allow_html=True)
    st.title('Cortrophin Gel | Medicare overview')
    st.markdown(f"""<div class="overview-intro">
    <p>This page summarizes annual use of Cortrophin Gel (corticotropin) and associated
    prescription-drug spending among Medicare Part D beneficiaries in 2022–2024.
    The data come from the Centers for Medicare &amp; Medicaid Services (CMS)
    <a href="{CMS_SPEND}">Medicare Part D Spending by Drug</a> dataset, using the
    supplied Cortrophin Gel manufacturer record. </p>
    </div>""", unsafe_allow_html=True)
    year = st.selectbox('Year', annual['Year'].tolist(), index=len(annual)-1)
    r = annual.loc[annual.Year.eq(year)].iloc[0]
    def delta(col):
        val = r[col + ' growth (%)']
        return None if pd.isna(val) else f'{val:+.1f}% vs prior year'
    a,b,c = st.columns(3)
    a.metric('Total Part D spending', f"${r.Spending/1e6:,.2f}M", delta('Spending'),delta_color='off')
    a.caption('Total recorded Part D spending on Cortrophin Gel during the selected year, shown in millions of US dollars.')
    b.metric('Claims, including refills', f'{r.Claims:,.0f}', delta('Claims'),delta_color='off')
    b.caption('Number of Cortrophin Gel prescription fills recorded under Part D during the selected year, including initial fills and refills. One person may have multiple claims.')
    c.metric('Unique beneficiaries in year', f'{r.Beneficiaries:,.0f}', delta('Beneficiaries'),delta_color='off')
    c.caption('Number of distinct Part D beneficiaries with a Cortrophin Gel claim in the selected year. A person can appear in multiple years, so annual counts must not be added together.')
    st.caption('Year-over-year change (%) = (selected-year value ÷ preceding-year value − 1) × 100.')
    left,right = st.columns(2)
    with left:
        plot = annual.assign(**{'Spending ($M)':annual.Spending/1e6})
        fig=px.bar(plot,x='Year',y='Spending ($M)',title='Annual Part D spending',text_auto='.2f')
        fig.update_traces(marker_color=['#92d9d4','#38b5b2','#147e91'],textposition='outside',cliponaxis=False,
                          hovertemplate='Year: %{x}<br>Spending: $%{y:,.2f}M<extra></extra>')
        fig.update_yaxes(range=[0,plot['Spending ($M)'].max()*1.18],gridcolor='#e4ebf0')
        fig.update_layout(height=390,bargap=.45)
        fig.update_xaxes(type='category'); chart(fig)
    with right:
        metric=st.selectbox('Utilization trend', ['Claims','Beneficiaries'])
        fig=px.line(annual,x='Year',y=metric,markers=True,title=f'Annual {metric.lower()}')
        fig.update_traces(line=dict(color='#7463c7',width=3),marker=dict(size=10,color='#7463c7'),
                          fill='tozeroy',fillcolor='rgba(116,99,199,.09)',
                          hovertemplate='Year: %{x}<br>Count: %{y:,.0f}<extra></extra>')
        fig.update_layout(height=305)
        fig.update_yaxes(rangemode='tozero',gridcolor='#e4ebf0')
        fig.update_xaxes(type='category'); chart(fig)
    a,b=st.columns(2)
    a.metric('Average spending per claim', f"${r['Spending per claim']:,.0f}")
    a.caption('Calculated as total Part D spending on Cortrophin Gel ÷ total Cortrophin Gel claims in the selected year. The result is the average recorded cost per fill, including refills.')
    b.metric('Average spending per beneficiary', f"${r['Spending per beneficiary']:,.0f}")
    b.caption('Calculated as total Part D spending on Cortrophin Gel ÷ unique Part D beneficiaries receiving Cortrophin Gel in the selected year. The result is the average annual recorded spending per recipient.')
    st.markdown(f'Source: [CMS Medicare Part D Spending by Drug]({CMS_SPEND}), 2022–2024. Definitions: CMS data dictionary dated June 3, 2026.')

elif page == 'Prescriber profile':
    st.markdown('<div class="overview-label">CORTROPHIN GEL / PRESCRIBER LANDSCAPE</div>', unsafe_allow_html=True)
    st.title('Cortrophin Gel | Prescriber profile')
    st.markdown(f"""<div class="overview-intro">
    <p>This page explores Cortrophin Gel prescribing patterns in 2024 using the CMS
    <a href="{CMS_RX}">Medicare Part D Prescribers by Provider &amp; Drug</a> dataset.
    The supplied extract contains 54 unique prescribing specialists across 22 states.
    Prescribers include physicians, nurse practitioners, and physician assistants;
    geography reflects the prescriber’s location, not the patient’s residence.</p>
    </div>""", unsafe_allow_html=True)
    f1,f2=st.columns(2)
    states=f1.multiselect('States',sorted(prescribers.Prscrbr_State_Abrvtn.unique()))
    specialties=f2.multiselect('Specialties',sorted(prescribers.Prscrbr_Type.unique()))
    df=prescribers.copy()
    if states: df=df[df.Prscrbr_State_Abrvtn.isin(states)]
    if specialties: df=df[df.Prscrbr_Type.isin(specialties)]
    if df.empty:
        st.write('No records match this combination. Clear one or both filters to view results.')
    else:
        a,b,c=st.columns(3)
        a.metric('Prescribers',f'{df.Prscrbr_NPI.nunique():,}')
        a.caption('Distinct prescribing specialists, identified by NPI, in the selected published records.')
        b.metric('Claims',f'{df.Tot_Clms.sum():,.0f}')
        b.caption('Total Cortrophin Gel prescription fills, including refills, in the selected records.')
        c.metric('Total claim cost',f'${df.Tot_Drug_Cst.sum()/1e6:,.2f}M')
        c.caption('Sum of recorded Cortrophin Gel claim costs in the selected records, in millions of US dollars.')
        metric=st.selectbox('Rank by', ['Claims','Prescribers','Claim costs'])
        titles={'Claims':'Top states by claims','Prescribers':'Top states by prescribers','Claim costs':'Top states by claim costs'}
        colors={'Claims':'#159b9e','Prescribers':'#7463c7','Claim costs':'#3683bb'}
        def grouped(key):
            g=df.groupby(key).agg(Claims=('Tot_Clms','sum'),Prescribers=('Prscrbr_NPI','nunique'),Cost=('Tot_Drug_Cst','sum')).reset_index()
            g['Claim costs']=g.Cost/1e6
            return g.sort_values([metric,key],ascending=[True,False])
        axis_label='Claim costs ($M)' if metric=='Claim costs' else metric
        left,right=st.columns(2)
        with left:
            g=grouped('Prscrbr_Type')
            fig=px.bar(g,x=metric,y='Prscrbr_Type',orientation='h',title=f'Specialties by {metric.lower()}',labels={'Prscrbr_Type':'',metric:axis_label})
            fig.update_traces(marker_color=colors[metric])
            fig.update_layout(height=460,bargap=.3)
            fig.update_xaxes(gridcolor='#e4ebf0');chart(fig)
        with right:
            g=grouped('Prscrbr_State_Abrvtn').tail(15)
            fig=px.bar(g,x=metric,y='Prscrbr_State_Abrvtn',orientation='h',title=titles[metric],labels={'Prscrbr_State_Abrvtn':'',metric:axis_label})
            fig.update_traces(marker_color=colors[metric])
            fig.update_layout(height=460,bargap=.3)
            fig.update_xaxes(gridcolor='#e4ebf0');chart(fig)
    st.markdown(f'Source: [CMS Medicare Part D Prescribers by Provider & Drug]({CMS_RX}), 2024 Cortrophin Gel extract.')

else:
    st.markdown('<div class="overview-label">ANI / FINANCIAL RESULTS</div>', unsafe_allow_html=True)
    st.title('ANI Financial Results')
    st.markdown(f"""<div class="overview-intro"><p>This page compares Cortrophin Gel,
    ILUVIEN, and total ANI net revenue for the three months ended September 30, 2025 and 2026,
    followed by full-year 2025 actual net revenue versus revised full-year 2026 guidance.
    All figures come from <a href="{ANI}">ANI’s Third Quarter 2026 Financial Results</a>,
    published November 5, 2026. Values are shown in millions of US dollars;
    net revenue is distinct from profit.</p></div>""", unsafe_allow_html=True)
    for col,product in zip(st.columns(3),['Cortrophin Gel','ILUVIEN','ANI total']):
        values=revenue[revenue.Product.eq(product)].set_index('Year').Net_Revenue_USD
        col.metric(product,f'${values[2026]/1e6:,.2f}M',f'{(values[2026]/values[2025]-1)*100:+.1f}% YoY',delta_color='off')
        col.caption(f'{product} net revenue for the three months ended September 30, 2026.')
    chart_data=revenue[revenue.Product.ne('ANI total')].copy()
    chart_data['Net revenue ($M)']=chart_data.Net_Revenue_USD/1e6
    chart_data['Year']=chart_data.Year.astype(str)
    fig=px.bar(chart_data,x='Product',y='Net revenue ($M)',color='Year',barmode='group',text_auto='.2f',
               color_discrete_map={'2025':'#a99adf','2026':'#159b9e'},title='Product net revenue: Q3 2025 vs Q3 2026')
    fig.update_traces(textposition='outside',cliponaxis=False)
    fig.update_layout(height=410,bargap=.35)
    fig.update_yaxes(range=[0,chart_data['Net revenue ($M)'].max()*1.45],gridcolor='#e4ebf0')
    clearance=chart_data['Net revenue ($M)'].max()*.14
    for i,product in enumerate(['Cortrophin Gel','ILUVIEN']):
        values=revenue[revenue.Product.eq(product)].set_index('Year').Net_Revenue_USD
        growth=(values[2026]/values[2025]-1)*100
        low=values[2025]/1e6+clearance
        high=values[2026]/1e6+clearance
        if product == 'Cortrophin Gel':
            # Lift the complete arrow without changing its slope.
            low += 8
            high += 8
        else:
            # Raise the right tip for a clearer upward ILUVIEN slope.
            high += 8
        fig.add_annotation(x=i+.1625,y=high,ax=i-.1625,ay=low,
                           xref='x',yref='y',axref='x',ayref='y',text='',showarrow=True,
                           arrowhead=2,arrowwidth=2.5,arrowsize=1.2,arrowcolor='#127e87')
        fig.add_annotation(x=i,y=(low+high)/2,text=f'<b>+{growth:.1f}%</b>',
                           showarrow=False,yshift=18,font=dict(size=14,color='#127e87'),
                           bgcolor='rgba(255,255,255,.9)',borderpad=3)
    chart(fig)
    st.subheader('Full year | 2025 actual vs 2026 guidance')
    st.caption('Full-year 2025 actual results and revised full-year 2026 management guidance, as reported on November 5, 2026. The 2025 values are rounded to whole millions in the source table.')
    selection=st.selectbox('Guidance measure',['Cortrophin Gel','ANI total','ILUVIEN'])
    # Source: same release, Full Year 2026 Financial Guidance, Revised / 2025 Actual columns.
    values={'Cortrophin Gel':(348,480,500),'ANI total':(883,1085,1125),'ILUVIEN':(75,80,85)}
    actual,low,high=values[selection]
    midpoint=(low+high)/2
    guide=go.Figure(go.Bar(x=['2025 actual','2026 guidance'],y=[actual,midpoint],
                          marker_color=['#a99adf','#159b9e'],
                          error_y=dict(type='data',array=[0,(high-low)/2],visible=True,color='#243e54',thickness=2,width=10),
                          customdata=[[actual,actual],[low,high]],
                          hovertemplate='%{x}<br>$%{customdata[0]:,.0f}–%{customdata[1]:,.0f}M<extra></extra>'))
    for i,(y,label) in enumerate([(actual,f'${actual:,}M'),(high,f'${low:,}–{high:,}M')]):
        guide.add_annotation(x=i,y=y,text=f'<b>{label}</b>',showarrow=False,yshift=18,font=dict(color='#18354d',size=14))
    clearance=high*.18
    guide.add_annotation(x=1,y=high+clearance,ax=0,ay=actual+clearance,
                         xref='x',yref='y',axref='x',ayref='y',text='',showarrow=True,
                         arrowhead=2,arrowwidth=2.5,arrowsize=1.2,arrowcolor='#127e87')
    guide.add_annotation(x=.5,y=(actual+high)/2+clearance,
                         text=f'<b>Projected growth: +{(midpoint/actual-1)*100:.1f}%</b>',
                         showarrow=False,yshift=20,font=dict(size=14,color='#127e87'),
                         bgcolor='rgba(255,255,255,.9)',borderpad=3)
    guide.update_layout(title=f'{selection}: full-year net revenue',height=410,bargap=.5,
                        yaxis_title='Net revenue ($M)',showlegend=False)
    guide.update_yaxes(range=[0,high*1.5],gridcolor='#e4ebf0');chart(guide)
    st.caption('Projected growth = (2026 guidance midpoint ÷ full-year 2025 actual − 1) × 100. The 2026 bar shows the midpoint and whiskers show the published guidance range; 2025 is an actual result, not a forecast. Guidance ranges are not statistical confidence intervals.')
    st.markdown(f'Source: [ANI Third Quarter 2026 Financial Results]({ANI}), November 5, 2026. Quarterly results: three months ended September 30. Full Year 2026 Financial Guidance table: 2025 actual and revised 2026 guidance.')
