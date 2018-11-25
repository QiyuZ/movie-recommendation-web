import boto3
import pandas as pd

client = boto3.client('s3') #low-level functional API

resource = boto3.resource('s3') #high-level object-oriented API
my_bucket = resource.Bucket('qz5uwdrdinus') #subsitute this for your s3 bucket name. 

obj = client.get_object(Bucket='qz5uwdrdinus', Key='u.data')
df_users = pd.read_csv(obj['Body'], sep='\t', names=['user_id', 'item_id', 'rating', 'timestamp'])
n_users = df_users.user_id.unique().shape[0]

obj_item = client.get_object(Bucket='qz5uwdrdinus', Key='u.item')
item_dic = {}
for line in obj_item['Body'].read().splitlines():
	record = line.strip().split('|')
	movie_id, movie_name = record[0], record[1]
	item_dic[movie_id] = movie_name
print item_dic['344']