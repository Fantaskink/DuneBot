from mongoengine import Document, StringField, BooleanField

class Book_club_meeting(Document):
    start_date = StringField(required=True)
    end_date = StringField(required=True)
    description = StringField(required=True)
    has_been_held = BooleanField(required=True)