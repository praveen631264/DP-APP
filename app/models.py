from mongoengine import Document, StringField, BooleanField, ListField, ReferenceField, DateTimeField, DictField, IntField, ObjectIdField
import datetime

class Role(Document):
    name = StringField(max_length=80, unique=True)
    description = StringField(max_length=255)

class User(Document):
    email = StringField(max_length=255, unique=True)
    password = StringField(max_length=255)
    active = BooleanField(default=True)
    fs_uniquifier = StringField(max_length=255, unique=True) # Required by Flask-Security-Too
    confirmed_at = DateTimeField()
    roles = ListField(ReferenceField(Role), default=[])

    # MFA Fields
    totp_secret = StringField(max_length=255, null=True)
    mfa_enabled = BooleanField(default=False)

    # Your application-specific fields
    first_name = StringField(max_length=255)
    last_name = StringField(max_length=255)
    created_at = DateTimeField(default=datetime.datetime.utcnow)