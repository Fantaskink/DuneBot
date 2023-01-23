from mongoengine import Document, StringField

class Book_club_meeting(Document):
    start_date = StringField(required=True)
    end_date = StringField(required=True)
    description = StringField(required=True)