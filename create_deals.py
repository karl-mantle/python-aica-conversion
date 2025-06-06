import pandas as pd
import csv

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
    if pd.isna(row.get('id')):
        return 'closed transaction'
    elif pd.notna(row.get('transaction_id')) or pd.notna(row.get('id_transaction')):
        return 'closed transaction'
    elif pd.notna(row.get('engagedStartDate')):
        return 'active mandate'
    else:
        return 'lead'

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

#add key
final_merged.insert(0, 'unique_id', range(1, len(final_merged) + 1))

# remove pointless columns

# save
final_merged.to_csv("merged_cleaned.csv", index=False)
print("Deals done!")
