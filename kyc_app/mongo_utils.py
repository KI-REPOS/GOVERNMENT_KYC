# backend/kyc_app/mongo_utils.py
from pymongo import MongoClient
from bson import ObjectId
import os
import json
from datetime import datetime

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)

def get_mongo_client():
    """Get MongoDB client connection"""
    mongo_uri = os.environ.get('DATABASE_URL', 'mongodb://localhost:27017/')
    try:
        client = MongoClient(mongo_uri)
        # Test the connection
        client.admin.command('ping')
        print("Successfully connected to MongoDB!")
        return client
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        raise e

def get_mongo_database():
    """Get MongoDB database instance"""
    client = get_mongo_client()
    # Extract database name from URI or use default
    mongo_uri = os.environ.get('DATABASE_URL', 'mongodb://localhost:27017/gov_kyc_db')
    db_name = mongo_uri.split('/')[-1].split('?')[0]
    if not db_name or db_name == '':
        db_name = 'gov_kyc_db'
    return client[db_name]

def get_mongo_collection(collection_name='users'):
    """Get MongoDB collection instance"""
    database = get_mongo_database()
    return database[collection_name]

def create_user_in_mongo(gov_id, first_name, last_name, email, photo_data, embedding):
    """Create a user document in MongoDB"""
    collection = get_mongo_collection()
    
    user_data = {
        'gov_id': gov_id,
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'photo': photo_data,
        'embedding': embedding,
        'wallet_address': None,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }
    
    result = collection.insert_one(user_data)
    return str(result.inserted_id)

def get_user_from_mongo(gov_id=None, mongo_id=None):
    """Get user data from MongoDB"""
    collection = get_mongo_collection()
    
    query = {}
    if gov_id:
        query['gov_id'] = gov_id
    elif mongo_id:
        query['_id'] = ObjectId(mongo_id)
    else:
        return None
    
    user_data = collection.find_one(query)
    if user_data:
        user_data['_id'] = str(user_data['_id'])  # Convert ObjectId to string
    return user_data

def update_user_wallet(gov_id, wallet_address):
    """Update user's wallet address in MongoDB"""
    collection = get_mongo_collection()
    
    result = collection.update_one(
        {'gov_id': gov_id},
        {'$set': {
            'wallet_address': wallet_address,
            'updated_at': datetime.utcnow()
        }}
    )
    
    return result.modified_count > 0