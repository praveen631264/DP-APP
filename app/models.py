from mongoengine import Document, StringField, BooleanField, ListField, ReferenceField, DateTimeField, DictField, IntField, ObjectIdField, EmbeddedDocument, EmbeddedDocumentField
import datetime
from flask_security import UserMixin, RoleMixin

class Role(Document, RoleMixin):
    name = StringField(max_length=80, unique=True)
    description = StringField(max_length=255)

class User(Document, UserMixin):
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

class AuditLog(EmbeddedDocument):
    """An entry in a document's audit trail."""
    event_name = StringField(required=True)
    timestamp = DateTimeField(default=datetime.datetime.utcnow)
    user_email = StringField() # Email of the user who performed the action
    details = DictField() # For arbitrary extra info, e.g., what changed

class Playbook(Document):
    """Represents a defined workflow or series of steps."""
    name = StringField(required=True, unique=True)
    description = StringField()
    steps = ListField(DictField()) # Storing steps as a list of dicts for flexibility
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    meta = {'collection': 'playbooks'}

class Document(Document):
    """The core model for a document in the system."""
    filename = StringField(required=True)
    content_type = StringField()
    
    # GridFS file identifier
    gridfs_file_id = ObjectIdField()

    # Status & Workflow
    status = StringField(default='pending')
    status_message = StringField()
    
    # Categorization & Data
    category = StringField()
    extracted_data = DictField()
    
    # Ownership & Timestamps
    uploaded_by = ReferenceField('User')
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)

    # Audit Trail
    audit_trail = ListField(EmbeddedDocumentField(AuditLog))

    # Soft Delete
    is_deleted = BooleanField(default=False)
    
    # Active Celery task ID
    active_task_id = StringField()

    meta = {'collection': 'documents', 'indexes': ['status', 'category', 'uploaded_by']}

    def save(self, *args, **kwargs):
        """Update the 'updated_at' timestamp on each save."""
        self.updated_at = datetime.datetime.utcnow()
        return super(Document, self).save(*args, **kwargs)