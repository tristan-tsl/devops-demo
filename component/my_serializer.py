import json

from flask import jsonify


class Serializer(object):

    def to_json(self):
        d = dict()
        for c in self.__class__.__table__.columns:
            v = getattr(self, c.name)
            d[c.name] = v
        return json.dumps(d, ensure_ascii=False)

    @staticmethod
    def to_list_json(data):
        return jsonify(json_list=[i.serialize for i in data])
