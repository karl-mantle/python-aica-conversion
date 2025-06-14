import pandas as pd
import pycountry_convert as pc

# float to str
def clean_id(x):
    try:
        return str(int(float(x)))
    except:
        return ''

# load the deal stage csvs
leads_df = pd.read_csv("csv/leads.csv")
mandates_df = pd.read_csv("csv/mandates.csv")
transactions_df = pd.read_csv("csv/transactions.csv")

# add deal stage
leads_df['dealStage_lead'] = 1
mandates_df['dealStage_mandate'] = 1
transactions_df['dealStage_transaction'] = 1

# mandates without lead id are pointless drop them
mandates_df = mandates_df[mandates_df['lead_id'].notna() & (mandates_df['lead_id'] != '')]

# merge mandates with their leads (left join)
merged_1 = pd.merge(leads_df, mandates_df, how='left', left_on='id', right_on='lead_id', suffixes=('', '_mandate'))

# split transactions to with or without lead
transactions_with_lead = transactions_df[transactions_df['lead_id'].notna() & (transactions_df['lead_id'] != '')]
transactions_without_lead = transactions_df[transactions_df['lead_id'].isna() | (transactions_df['lead_id'] == '')]

# merge transactions with their leads merged_1 (left join)
merged_2 = pd.merge(merged_1, transactions_with_lead, how='left', left_on='id', right_on='lead_id', suffixes=('', '_transaction'))

# append transactions with no lead as new rows
final_merged = pd.concat([merged_2, transactions_without_lead], ignore_index=True, sort=False)

# add dealstage column
def determine_deal_stage(row):
    if pd.notna(row.get('dealStage_transaction')):
        return 'closed transaction'
    elif pd.notna(row.get('dealStage_mandate')):
        return 'active mandate'
    elif pd.notna(row.get('dealStage_lead')):
        return 'lead'
    return ''

final_merged['dealStage'] = final_merged.apply(determine_deal_stage, axis=1)

# load other csvs
firms_df = pd.read_csv("csv/firms.csv")
firms_dict = pd.Series(firms_df['name'].values, index=firms_df['id'].astype(str)).to_dict()

members_df = pd.read_csv("csv/members.csv")
members_dict = pd.Series(members_df['fullname'].values, index=members_df['id'].astype(str)).to_dict()

media_df = pd.read_csv("csv/media.csv")
media_dict = pd.Series(media_df['filepath'].values, index=media_df['id'].astype(str)).to_dict()

# map id's (check column existence)
for col, mapping_dict in [('memberFirm_id', firms_dict), 
                          ('otherMembers', firms_dict),
                          ('dealTeamLead_id', members_dict), 
                          ('logoA_id', media_dict), 
                          ('logoB_id', media_dict)]:
    if col in final_merged.columns:
        final_merged[col] = final_merged[col].apply(clean_id).map(mapping_dict).fillna('')

#add base url for logos
base_url = "https://aicanetwork.com/crm/"

for col in ['logoA_id', 'logoB_id']:
    if col in final_merged.columns:
        final_merged[col] = final_merged[col].apply(lambda x: base_url + x if x else x)

# float to int safe
int_columns = ['isDraft', 'isActive', 'assistanceRequired', 'confidential', 'metricsConfidential']
for col in int_columns:
    if col in final_merged.columns:
        final_merged[col] = pd.to_numeric(final_merged[col], errors='coerce').fillna(0).astype(int)

# remove the random trailing spaces in service
if 'service' in final_merged.columns:
    final_merged['service'] = final_merged['service'].str.strip()

# map deal values
deal_values_mapping = {
    '1-5': '<10',
    '6-10': '<10',
    '11-15': '10-20',
    '16-20': '10-20',
    '21-30': '20-30',
    'More than 30': '30-50',
}
if 'estimatedValue' in final_merged.columns:
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

if 'country' in final_merged.columns:
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

#add key
final_merged.insert(0, 'unique_id', range(1, len(final_merged) + 1))

# remove pointless columns
columns_to_drop = ['mandate_id', 'transaction_id', 'id_mandate', 'lead_id', 'transaction_id_mandate', 'id_transaction', 'lead_id_transaction', 'mandate_id_transaction', 'isActive_transaction', 'otherMember', 'dealStage_lead', 'dealStage_mandate', 'dealStage_transaction']
final_merged = final_merged.drop(columns=[col for col in columns_to_drop if col in final_merged.columns])

# save
final_merged.to_csv("deals_import.csv", index=False)
print("Deals done!")
