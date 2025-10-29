import mongoengine
import datetime
from flask_security import UserMixin, RoleMixin

class Role(mongoengine.Document, RoleMixin):
    name = mongoengine.StringField(max_length=80, unique=True)
    description = mongoengine.StringField(max_length=255)

class User(mongoengine.Document, UserMixin):
    email = mongoengine.StringField(max_length=255, unique=True)
    password = mongoengine.StringField(max_length=255)
    active = mongoengine.BooleanField(default=True)
    fs_uniquifier = mongoengine.StringField(max_length=255, unique=True)
    confirmed_at = mongoengine.DateTimeField()
    roles = mongoengine.ListField(mongoengine.ReferenceField(Role), default=[])
    totp_secret = mongoengine.StringField(max_length=255, null=True)
    mfa_enabled = mongoengine.BooleanField(default=False)
    first_name = mongoengine.StringField(max_length=255)
    last_name = mongoengine.StringField(max_length=255)
    created_at = mongoengine.DateTimeField(default=datetime.datetime.utcnow)

class AuditLog(mongoengine.EmbeddedDocument):
    event_name = mongoengine.StringField(required=True)
    timestamp = mongoengine.DateTimeField(default=datetime.datetime.utcnow)
    user_email = mongoengine.StringField()
    details = mongoengine.DictField()

class Playbook(mongoengine.Document):
    name = mongoengine.StringField(required=True, unique=True)
    category = mongoengine.StringField(required=True, unique=True)
    description = mongoengine.StringField()
    steps = mongoengine.ListField(mongoengine.DictField())
    final_status = mongoengine.StringField(default='Processed')
    created_at = mongoengine.DateTimeField(default=datetime.datetime.utcnow)
    meta = {'collection': 'playbooks'}

class Job(mongoengine.Document):
    job_type = mongoengine.StringField(required=True)
    status = mongoengine.StringField(default='PENDING')
    details = mongoengine.DictField()
    result = mongoengine.DictField()
    command = mongoengine.StringField()
    created_at = mongoengine.DateTimeField(default=datetime.datetime.utcnow)
    updated_at = mongoengine.DateTimeField(default=datetime.datetime.utcnow)
    meta = {'collection': 'jobs'}

    def save(self, *args, **kwargs):
        self.updated_at = datetime.datetime.utcnow()
        return super(Job, self).save(*args, **kwargs)

class Document(mongoengine.Document):
    filename = mongoengine.StringField(required=True)
    content_type = mongoengine.StringField()
    file = mongoengine.FileField() # GridFS file reference
    status = mongoengine.StringField(default='PENDING')
    status_message = mongoengine.StringField()
    text = mongoengine.StringField()
    category = mongoengine.StringField()
    kvps = mongoengine.DictField()
    uploaded_by = mongoengine.ReferenceField('User')
    created_at = mongoengine.DateTimeField(default=datetime.datetime.utcnow)
    updated_at = mongoengine.DateTimeField(default=datetime.datetime.utcnow)
    processed_at = mongoengine.DateTimeField()
    audit_trail = mongoengine.ListField(mongoengine.EmbeddedDocumentField(AuditLog))
    is_deleted = mongoengine.BooleanField(default=False)
    processing_chain_id = mongoengine.StringField()
    _version = mongoengine.IntField(default=1)

    meta = {
        'collection': 'documents', 
        'indexes': ['status', 'category', 'uploaded_by']
    }

    def save(self, *args, **kwargs):
        self.updated_at = datetime.datetime.utcnow()
        return super(Document, self).save(*args, **kwargs)

class DocumentChunk(mongoengine.Document):
    doc_id = mongoengine.ObjectIdField(required=True)
    chunk_index = mongoengine.IntField(required=True)
    text = mongoengine.StringField(required=True)
    embedding = mongoengine.ListField(mongoengine.FloatField())
    status = mongoengine.StringField(default='PENDING')

    meta = {
        'collection': 'document_chunks',
        'indexes': [
            'doc_id',
            ('doc_id', 'chunk_index'),
        ]
    }