from flask.json.provider import JSONProvider
import json
from bson import ObjectId
import datetime

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

class CustomJSONProvider(JSONProvider):
    def dumps(self, obj, **kwargs):
        return json.dumps(obj, **kwargs, cls=JSONEncoder)

    def loads(self, s, **kwargs):
        return json.loads(s, **kwargs)

