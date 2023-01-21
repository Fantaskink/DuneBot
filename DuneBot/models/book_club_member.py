from mongoengine import Document, IntField, StringField

class Book_club_member(Document):
    discord_id = IntField(required=True)
    timeslot = StringField(required=True)