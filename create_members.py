import pandas as pd
import re
import unidecode

# float to str
def clean_id(x):
    try:
        return str(int(float(x)))
    except:
        return ''

# load the member csv
members_df = pd.read_csv("csv/members.csv")

# load other csvs
firms_df = pd.read_csv("csv/firms.csv")
firms_dict = pd.Series(firms_df['name'].values, index=firms_df['id'].astype(str)).to_dict()

sectors_df = pd.read_csv("csv/sectors.csv")
sectors_dict = pd.Series(sectors_df['name'].values, index=sectors_df['id'].astype(str)).to_dict()

media_df = pd.read_csv("csv/media.csv")
media_dict = pd.Series(media_df['filepath'].values, index=media_df['id'].astype(str)).to_dict()

# map id's (check column existence)
for col, mapping_dict in [('firm_id', firms_dict), 
                          ('sector_id', sectors_dict), 
                          ('sector2_id', sectors_dict), 
                          ('sector3_id', sectors_dict), 
                          ('photo_id', media_dict)]:
    if col in members_df.columns:
        members_df[col] = members_df[col].apply(clean_id).map(mapping_dict).fillna('')

# map sector terms
sector_terms_mapping = {
    'Business_Services': 'Business Services',
    'Financial_Services': 'Financial Services',
    'Industrials': 'Industrials and Manufacturing',
    'Technology': 'Technology, Media & Telecoms',
    'Consumer Products': 'Consumer and Retail',
    'Retail': 'Consumer and Retail',
}
if 'sector_id' in members_df.columns:
    members_df['sector_id'] = members_df['sector_id'].map(sector_terms_mapping).fillna(members_df['sector_id'])
if 'sector2_id' in members_df.columns:
    members_df['sector2_id'] = members_df['sector2_id'].map(sector_terms_mapping).fillna(members_df['sector2_id'])
if 'sector3_id' in members_df.columns:
    members_df['sector3_id'] = members_df['sector3_id'].map(sector_terms_mapping).fillna(members_df['sector3_id'])

# sectors into single "sectors" column
sector_cols = ['sector_id', 'sector2_id', 'sector3_id']
members_df['sectors'] = members_df[sector_cols] \
    .fillna('') \
    .astype(str) \
    .apply(lambda row: '|'.join(filter(None, [s.strip() for s in row])), axis=1)

#add base url for profile picture
base_url = "https://aicanetwork.com/crm/"

for col in ['photo_id']:
    if col in members_df.columns:
        members_df[col] = members_df[col].apply(lambda x: base_url + x if x else x)

# float to int safe
int_columns = ['subscribed', 'mailchimp']
for col in int_columns:
    if col in members_df.columns:
        members_df[col] = pd.to_numeric(members_df[col], errors='coerce').fillna(0).astype(int)

# map AICA roles
role_values_mapping = {
    '1': 'aica_admin',
    '2': 'aica_designated',
    '3': 'aica_affiliate',
    '4': 'aica_analyst',
    '5': 'subscriber',
}

if 'role_id' in members_df.columns:
    # int to str first
    members_df['role_id'] = pd.to_numeric(members_df['role_id'], errors='coerce').fillna(0).astype(int).astype(str)
    members_df['role_id'] = members_df['role_id'].map(role_values_mapping).fillna('')

# create first and last names and usernames (WordPRess friendly ones)
def create_firstname(row):
    fullname = str(row.get('fullname', '')).strip()
    return fullname.split()[0] if fullname else ''

def create_lastname(row):
    fullname = str(row.get('fullname', '')).strip()
    parts = fullname.split()
    return ' '.join(parts[1:]) if len(parts) > 1 else ''

def create_username(row):
    fullname = str(row.get('fullname', '')).strip().lower()
    ascii_name = unidecode.unidecode(fullname)
    dotted = ascii_name.replace(' ', '.')
    username = re.sub(r'[^a-z0-9\.]', '', dotted)
    username = re.sub(r'\.+', '.', username)
    username = username.strip('.')
    
    return username

members_df['firstname'] = members_df.apply(create_firstname, axis=1)
members_df['lastname'] = members_df.apply(create_lastname, axis=1)
members_df['username'] = members_df.apply(create_username, axis=1)

#add key
members_df.insert(0, 'unique_id', range(1, len(members_df) + 1))

# remove pointless columns
columns_to_drop = ['online', 'lastSeen', 'office_id', 'password', 'sector_id', 'sector2_id', 'sector3_id']
members_df = members_df.drop(columns=[col for col in columns_to_drop if col in members_df.columns])

# save
members_df.to_csv("members_import.csv", index=False)
print("Members done!")
