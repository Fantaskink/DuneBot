from pymongo import MongoClient
import os
from dotenv import load_dotenv, find_dotenv
from models.subreddit_stream import Subreddit_stream

load_dotenv(find_dotenv())

password = os.environ.get("DB_PASSWORD")
connection_string = f"mongodb+srv://dunebot:{password}@dunebot.fpqbhad.mongodb.net/?retryWrites=true&w=majority",

try:
    client = MongoClient(connection_string)
except Exception:
    print("Error: " + Exception)


def delete_subreddit(id: str):
    db = client["DuneBot"]
    collection = db["subreddits"]

    result = collection.delete_one({"_id": id})
    print(result.deleted_count, "document(s) deleted.")


def delete_subreddit_by_channel_id(channel_id):
    db = client["DuneBot"]
    collection = db["subreddits"]

    result = collection.delete_one({"channel_id": channel_id})
    print(result.deleted_count, "document(s) deleted.")


def add_subreddit(channel_id, subreddit):
    db = client["DuneBot"]
    collection = db["subreddits"]

    # Retrieve document with the same channel_id and delete if present
    result = collection.find_one({"channel_id": channel_id})
    if result is not None:
        print("Exists")
        id = result["_id"]
        delete_subreddit(id)
        print("id: ", id)

    subreddit_stream = Subreddit_stream(channel_id=channel_id, subreddit=subreddit,
                                        is_active=False).to_mongo().to_dict()

    # Replace existing document if new one has the same channel, otherwise insert new document
    res = collection.replace_one({"channel_id": channel_id}, subreddit_stream, upsert=True)

    print(res.acknowledged)
    print(res.upserted_id)


def get_subreddit(id: str):
    db = client["DuneBot"]
    collection = db["subreddits"]

    result = collection.find_one({"_id": id})

    return (result)


def set_all_streams_inactive():
    db = client["DuneBot"]
    collection = db["subreddits"]

    result = collection.update_many({}, {"$set": {"is_active": False}})
    print(result.modified_count, "documents updated.")


def get_all_documents(database_name, collection_name):
    db = client[database_name]
    collection = db[collection_name]

    result = collection.find()

    return (result)


def set_activity_status(id: str, is_active):
    db = client["DuneBot"]
    collection = db["subreddits"]

    query = {"_id": id}
    new_values = {"$set": {"is_active": is_active}}
    collection.update_one(query, new_values)
