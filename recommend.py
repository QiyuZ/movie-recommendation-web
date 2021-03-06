import numpy as np
import pandas as pd
import boto3
#from sklearn import cross_validation as cv
from sklearn.metrics.pairwise import pairwise_distances
from boto3.dynamodb.conditions import Key, Attr



def recommend_movie(userid, num):
    #check whether already exist
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('movie')
    status = int(table.query(KeyConditionExpression=Key('userID').eq(userid))['Count'])
    if status == 1:
        res = []
        response = table.get_item(
            Key={
                'userID': userid,
            }
        )
        item = response['Item']['movies']
        count = num
        for i in item:
            res.append(i)
            count -= 1
            if count == 0:
                break
        return res
    # read in users
    client = boto3.client('s3') #low-level functional API
    resource = boto3.resource('s3') #high-level object-oriented API
    my_bucket = resource.Bucket('qz5uwdrdinus') #subsitute this for your s3 bucket name.

    obj = client.get_object(Bucket='qz5uwdrdinus', Key='u.data')
    df_users = pd.read_csv(obj['Body'], sep='\t', names=['user_id', 'item_id', 'rating', 'timestamp'])
    n_users = df_users.user_id.unique().shape[0]
    n_items = df_users.item_id.unique().shape[0]

# read in items
    item_dic = {}
    obj_item = client.get_object(Bucket='qz5uwdrdinus', Key='u.item')
    for line in obj_item['Body'].read().splitlines():
		record = line.strip().split('|')
		movie_id, movie_name = record[0], record[1]
		item_dic[movie_id] = movie_name

    train_data_matrix = np.zeros((n_users, n_items))
    #train_data, test_data = cv.train_test_split(df_users, test_size=0.01)
    train_data = df_users

    for line in train_data.itertuples():
        train_data_matrix[line[1]-1, line[2]-1] = line[3]  

    user_similarity = pairwise_distances(train_data_matrix, metric='cosine')
    item_similarity = pairwise_distances(train_data_matrix.T, metric='cosine')

    def predict(ratings, similarity, type='user'):
        if type == 'user':
            mean_user_rating = ratings.mean(axis=1)
        #You use np.newaxis so that mean_user_rating has same format as ratings
            ratings_diff = (ratings - mean_user_rating[:, np.newaxis]) 
            pred = mean_user_rating[:, np.newaxis] + similarity.dot(ratings_diff) / np.array([np.abs(similarity).sum(axis=1)]).T
        elif type == 'item':
            pred = ratings.dot(similarity) / np.array([np.abs(similarity).sum(axis=1)])     
        return pred

    user_prediction = predict(train_data_matrix, user_similarity, type='user') #not used
    item_prediction = predict(train_data_matrix, item_similarity, type='item')

    a = list(item_prediction[userid])
    pre = sorted(range(len(a)), key=lambda i: a[i])[-num:]
    itemnum = [x+1 for x in pre]

    premovie = []
    for i in itemnum:
        premovie.append(item_dic[str(i)])

    #generate a 10 res list
    pre1 = sorted(range(len(a)), key=lambda i: a[i])[-10:]
    itemnum1 = [x + 1 for x in pre1]

    premovie1 = []
    for i in itemnum1:
        premovie1.append(item_dic[str(i)])

    #write the result to dynamoDB
    if status == 0:
        table.put_item(
            Item={
                'userID': userid,
                'movies': premovie1,
            }
        )

    return premovie
