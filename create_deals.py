import re
import pandas as pd
import pycountry_convert as pc

# load the deal stage csvs
firms_df = pd.read_csv("csv/firms.csv")
firms_dict = pd.Series(firms_df['name'].values, index=firms_df['id'].astype(str)).to_dict()

members_df = pd.read_csv("csv/members.csv")
members_dict = pd.Series(members_df['email'].values, index=members_df['id'].astype(str)).to_dict()

media_df = pd.read_csv("csv/media.csv")
media_dict = pd.Series(media_df['filepath'].values, index=media_df['id'].astype(str)).to_dict()

leads_df = pd.read_csv("csv/leads.csv")
mandates_df = pd.read_csv("csv/mandates.csv")
transactions_df = pd.read_csv("csv/transactions.csv")

# drop inactive leads
leads_df['isActive'] = pd.to_numeric(leads_df['isActive'], errors='coerce').fillna(0).astype(int)
leads_df = leads_df[leads_df['isActive'] == 1]

# add deal stage
leads_df['dealStage_lead'] = 1
mandates_df['dealStage_mandate'] = 1
transactions_df['dealStage_transaction'] = 1

# drop orphaned mandates
mandates_df = mandates_df[mandates_df['lead_id'].notna() & (mandates_df['lead_id'] != '')]

# merge leads with their mandates
leads_and_mandates = pd.merge(leads_df, mandates_df, how='left', left_on='id', right_on='lead_id', suffixes=('', '_mandate'))
mandate_columns = [ 'mandate_id', 'transaction_id','isActive','isDraft', 'id_mandate','lead_id','transaction_id_mandate']
leads_and_mandates = leads_and_mandates.drop(columns=[col for col in mandate_columns if col in leads_and_mandates.columns])

# drop orphaned transactions
transactions_with_lead = transactions_df[transactions_df['lead_id'].notna() & (transactions_df['lead_id'] != '')]

# merge leads, mandates with their transactions
final_merged = pd.merge(leads_and_mandates, transactions_with_lead, how='left', left_on='id', right_on='lead_id', suffixes=('', '_transaction'))

# float to int
int_columns = ['assistanceRequired', 'confidential', 'metricsConfidential']
for col in int_columns:
    if col in final_merged.columns:
        final_merged[col] = pd.to_numeric(final_merged[col], errors='coerce').fillna(0).astype(int)

# add deal stage column
def determine_deal_stage(row):
    if pd.notna(row.get('dealStage_transaction')):
        return 'closed transaction'
    elif pd.notna(row.get('dealStage_mandate')):
        return 'active mandate'
    elif pd.notna(row.get('dealStage_lead')):
        return 'lead'
    return ''

final_merged['dealStage'] = final_merged.apply(determine_deal_stage, axis=1)
deal_stage_columns = ['dealStage_lead', 'dealStage_mandate', 'dealStage_transaction']
final_merged = final_merged.drop(columns=[col for col in deal_stage_columns if col in final_merged.columns])

# map ids
def clean_id(x):
    try:
        return str(int(float(x)))
    except:
        return ''

for col, mapping_dict in [('memberFirm_id', firms_dict), 
                          ('otherMembers', firms_dict),
                          ('dealTeamLead_id', members_dict), 
                          ('logoA_id', media_dict), 
                          ('logoB_id', media_dict)]:
    if col in final_merged.columns:
        final_merged[col] = final_merged[col].apply(clean_id).map(mapping_dict).fillna('')

# add base URL for logos
base_url = "https://aicanetwork.com/crm/"
for col in ['logoA_id', 'logoB_id']:
    if col in final_merged.columns:
        final_merged[col] = final_merged[col].apply(lambda x: base_url + x if x else x)

# remove the random trailing spaces in service
final_merged['service'] = final_merged['service'].str.strip()
mask = ~final_merged['service'].isin(['sell', 'buy', 'equity', 'debt', 'other', ''])
final_merged.loc[mask, 'serviceother'] = final_merged.loc[mask, 'service']
final_merged.loc[mask, 'service'] = 'other'

# map sector terms
sector_terms_mapping = {
    'Business_Services': 'Business Services',
    'Financial_Services': 'Financial Services',
    'Industrials': 'Industrials and Manufacturing',
    'Technology': 'Technology, Media & Telecoms',
    'Consumer Products': 'Consumer and Retail',
    'Retail': 'Consumer and Retail',
    'Media_Entertainment': 'Technology, Media & Telecoms',
    'Real_Estate': 'Real Estate',
}
final_merged['primaryIndustry'] = final_merged['primaryIndustry'].map(sector_terms_mapping).fillna(final_merged['primaryIndustry'])

# map deal values
deal_values_mapping = {
    '1-5': '<10',
    '6-10': '<10',
    '11-15': '10-20',
    '16-20': '10-20',
    '21-30': '20-30',
    'More than 30': '30-50',
}
final_merged['estimatedValue'] = final_merged['estimatedValue'].map(deal_values_mapping).fillna(final_merged['estimatedValue'])

# map regon column
def get_region(country):
    try:
        country = country.strip()
        country_code = pc.country_name_to_country_alpha2(country)
        continent_code = pc.country_alpha2_to_continent_code(country_code)
        return {
            'EU': 'EMEA',
            'AS': 'Asia',
            'AF': 'EMEA',
            'NA': 'Americas',
            'SA': 'Americas',
            'OC': 'Asia',
        }.get(continent_code, '')
    except:
        return ''
final_merged['region'] = final_merged['country'].apply(get_region)

# confidential
final_merged['visibility'] = final_merged['confidential'].apply(lambda x: 'public' if x == 1 else 'hidden')

# client name
def get_client_name(row):
    return row['nameA'] if pd.notna(row.get('nameA')) and row['nameA'] != '' else row.get('prospectName', '')

final_merged['clientName'] = final_merged.apply(get_client_name, axis=1)

# post title
def get_post_title_if_blank(row):
    def safe_str(x):
        if pd.isna(x):
            return ''
        return str(x).strip()
    
    projectName = safe_str(row.get('projectName', ''))
    nameA = safe_str(row.get('nameA', ''))
    nameB = safe_str(row.get('nameB', ''))
    tombstone = safe_str(row.get('tombstone', ''))
    
    if projectName != '':
        return projectName
    else:
        parts = [part for part in [nameA, tombstone, nameB] if part != '']
        return ' '.join(parts)

final_merged['post_title'] = final_merged.apply(get_post_title_if_blank, axis=1)

# add published date
def determine_published_date(row):
    if pd.notna(row.get('completedDate')):
        return row.get('completedDate')
    elif pd.notna(row.get('engagedStartDate')):
        return row.get('engagedStartDate')
    elif pd.notna(row.get('projectStartDate')):
        return row.get('projectStartDate')
    return '1970-01-01'

final_merged['publishedDate'] = final_merged.apply(determine_published_date, axis=1)

# add considerations
def keep_digits_only(val):
    if pd.isna(val) or str(val).strip() == '':
        return ''
    val_str = str(val)
    # remove everything except digits (0-9)
    cleaned = re.sub(r'\D', '', val_str)
    return cleaned

# split and pad
split_cols = final_merged['consideration'].fillna('').str.split(',', expand=True).iloc[:, :6]
while split_cols.shape[1] < 6:
    split_cols[split_cols.shape[1]] = ''

split_cols.columns = ['concash', 'conshares', 'conearnout', 'convtb', 'consellerfinancing', 'conother']

# clean each column by removing non-digit characters
for col in split_cols.columns:
    split_cols[col] = split_cols[col].apply(keep_digits_only)

# assign back
final_merged[['concash', 'conshares', 'conearnout', 'convtb', 'consellerfinancing', 'conother']] = split_cols

# add key
final_merged.insert(0, 'unique_id', range(1, len(final_merged) + 1))

# remove pointless columns
columns_to_drop = ['lead_id', 'id_transaction', 'lead_id', 'mandate_id', 'isActive', 'otherMember']
final_merged = final_merged.drop(columns=[col for col in columns_to_drop if col in final_merged.columns])

duplicates = final_merged[final_merged.duplicated(subset=['id'], keep=False)]
print(len(duplicates))

# save
final_merged.to_csv("deals_import.csv", index=False)
print("Deals done!")
