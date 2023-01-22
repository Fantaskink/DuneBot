from mongoengine import Document, StringField

class Book_club_meeting(Document):
    date = StringField(required=True)
    chapters = StringField(required=True)