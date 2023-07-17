from mongoengine import Document, IntField, StringField, BooleanField


class Subreddit_stream(Document):
    channel_id = IntField(required=True)
    subreddit = StringField(required=True)
    is_active = BooleanField(required=True)
