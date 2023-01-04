import json


def serialize_json(object):
    return json.dumps(
        object,
        separators=(',', ':'),
        ensure_ascii=False,
    )


def deserialize_json(object):
    return json.loads(object)
