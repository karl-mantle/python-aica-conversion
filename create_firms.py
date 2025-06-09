import pandas as pd
import re
import unidecode

# float to str
def clean_id(x):
    try:
        return str(int(float(x)))
    except:
        return ''

# username for designated member field
def create_username(row):
    fullname = str(row.get('fullname', '')).strip().lower()
    ascii_name = unidecode.unidecode(fullname)
    dotted = ascii_name.replace(' ', '.')
    username = re.sub(r'[^a-z0-9\.]', '', dotted)
    username = re.sub(r'\.+', '.', username)
    username = username.strip('.')
    
    return username

# load the member csv
firms_df = pd.read_csv("csv/firms.csv")

# load other csvs
members_df = pd.read_csv("csv/members.csv")
members_dict = pd.Series(members_df['fullname'].values, index=members_df['id'].astype(str)).to_dict()

sectors_df = pd.read_csv("csv/sectors.csv")
sectors_dict = pd.Series(sectors_df['name'].values, index=sectors_df['id'].astype(str)).to_dict()

media_df = pd.read_csv("csv/media.csv")
media_dict = pd.Series(media_df['filepath'].values, index=media_df['id'].astype(str)).to_dict()

# map id's (check column existence)
for col, mapping_dict in [('designatedMember_id', members_dict), 
                          ('primarySector_id', sectors_dict), 
                          ('photo_id', media_dict)]:
    if col in firms_df.columns:
        firms_df[col] = firms_df[col].apply(clean_id).map(mapping_dict).fillna('')

#add base url for profile picture
base_url = "https://aicanetwork.com/crm/"

for col in ['photo_id']:
    if col in firms_df.columns:
        firms_df[col] = firms_df[col].apply(lambda x: base_url + x if x else x)

for col in ['designatedMember_id']:
    if col in firms_df.columns:
        firms_df['designatedMember_id'] = firms_df['designatedMember_id'].apply(create_username)

#add key
firms_df.insert(0, 'unique_id', range(1, len(firms_df) + 1))

# remove pointless columns
columns_to_drop = ['offices', 'moreOffices', 'isActive']
firms_df = firms_df.drop(columns=[col for col in columns_to_drop if col in firms_df.columns])

# save
firms_df.to_csv("firms_import.csv", index=False)
print("Firms done!")
