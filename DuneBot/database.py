from pymongo import MongoClient
import os
from dotenv import load_dotenv, find_dotenv
from models.subreddit_stream import Subreddit_stream
from models.book_club_member import Book_club_member
from models.book_club_meeting import Book_club_meeting

load_dotenv(find_dotenv())

password = os.environ.get("DB_PASSWORD")
connection_string = f"mongodb+srv://dunebot:{password}@dunebot.fpqbhad.mongodb.net/?retryWrites=true&w=majority", 

try:
    client = MongoClient(connection_string)
except Exception:
    print("Error: " + Exception)

def delete_subreddit(id:str):
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

    subreddit_stream = Subreddit_stream(channel_id=channel_id, subreddit=subreddit, is_active=False).to_mongo().to_dict()

    # Replace existing document if new one has the same channel, otherwise insert new document
    res = collection.replace_one({"channel_id": channel_id}, subreddit_stream, upsert=True)

    print(res.acknowledged)
    print(res.upserted_id)

def get_subreddit(id:str):
    db = client["DuneBot"]
    collection = db["subreddits"]

    result = collection.find_one({"_id":id})

    return(result)

def set_all_streams_inactive():
    db = client["DuneBot"]
    collection = db["subreddits"]

    result = collection.update_many({}, {"$set": {"is_active": False}})
    print(result.modified_count, "documents updated.")

def get_all_documents(database_name, collection_name):
    db = client[database_name]
    collection = db[collection_name]

    result = collection.find()

    return(result)

def set_activity_status(id:str, is_active):
    db = client["DuneBot"]
    collection = db["subreddits"]

    query = {"_id": id}
    new_values = {"$set": {"is_active": is_active}}
    collection.update_one(query, new_values)

def add_book_club_member(discord_id, timeslot):
    db = client["DuneBot"]
    collection = db["bookclubmembers"]

    book_club_member = Book_club_member(discord_id=discord_id, timeslot=timeslot).to_mongo().to_dict()

    # Replace existing document if new one has the same channel, otherwise insert new document
    res = collection.replace_one({"discord_id": discord_id}, book_club_member, upsert=True)

    print(res.acknowledged)
    print(res.upserted_id)

def delete_member_by_discord_id(discord_id):
    db = client["DuneBot"]
    collection = db["bookclubmembers"]

    result = collection.delete_one({"discord_id": discord_id})
    print(result.deleted_count, "document(s) deleted.")
    return(result.deleted_count)

def delete_member(id:str):
    db = client["DuneBot"]
    collection = db["bookclubmembers"]

    result = collection.delete_one({"_id": id})
    print(result.deleted_count, "document(s) deleted.")

def add_timeslot(timeslot):
    db = client["DuneBot"]
    collection = db["timeslots"]

    res = collection.update_one({"timeslot":timeslot}, {"$set": {"timeslot": timeslot}}, upsert=True)

    print(res.acknowledged)
    print(res.upserted_id)

def delete_timeslot(timeslot):
    db = client["DuneBot"]
    collection = db["timeslots"]

    result = collection.delete_one({"timeslot": timeslot})
    print(result.deleted_count, "document(s) deleted.")

def get_all_timeslots():
    db = client["DuneBot"]
    collection = db["timeslots"]

    all_docs = list(collection.find())
    return all_docs

def add_meeting(start_date, end_date, description):
    db = client["DuneBot"]
    collection = db["meetings"]

    book_club_meeting = Book_club_meeting(start_date=start_date, end_date=end_date, description=description).to_mongo().to_dict()

    res = collection.replace_one({"start_date":start_date, "end_date":end_date, "description":description}, book_club_meeting, upsert=True)

    print(res.acknowledged)
    print(res.upserted_id)

def add_channel(channel_id, channel_function):
    db = client["DuneBot"]
    collection = db["channels"]

    # Use update_one to replace the document if it already exists, or insert it if it doesn't
    res = collection.update_one({"channel_function": channel_function}, {"$set": {"channel_id": channel_id}}, upsert=True)

    print(res.acknowledged)
    print(res.upserted_id)

def get_all_channels():
    db = client["DuneBot"]
    collection = db["channels"]

    # Use find() to retrieve all documents
    all_channels = list(collection.find())

    return all_channels
