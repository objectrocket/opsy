from flask_apispec import use_kwargs as api_spec_use_kwargs
from flask_marshmallow.fields import _rapply, _url_val
from marshmallow import post_load
from marshmallow import fields as ma_fields
from prettytable import PrettyTable
from opsy.flask_extensions import ma


def use_kwargs(schema_cls, schema_kwargs=None, **kwargs):

    if schema_kwargs is None:
        schema_kwargs = {}

    def factory(request):
        # Respect partial updates for PATCH and GET requests
        partial = getattr(request, 'method', None) in ['PATCH', 'GET']
        # partial = request.method in ['PATCH', 'GET']
        # Add current request to the schema's context
        return schema_cls(
            partial=partial,
            context={'request': request},
            **schema_kwargs
        )

    return api_spec_use_kwargs(factory, **kwargs)


class Hyperlinks(ma_fields.Dict):
    # We recreate this from upstream, but inherit from Dict so apispec gets
    # the right type.

    _CHECK_ATTRIBUTE = False

    def __init__(self, schema, **kwargs):
        self.schema = schema
        ma_fields.Dict.__init__(self, **kwargs)

    def _serialize(self, value, attr, obj):
        return _rapply(self.schema, _url_val, key=attr, obj=obj)


class Password(ma.String):
    """Field to obscure passwords on serialization."""

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        return '<HIDDEN>'


class EmptySchema(ma.Schema):
    pass


###############################################################################
# Base schemas
###############################################################################


class BaseSchema(ma.ModelSchema):

    @post_load
    def make_instance(self, data, **kwargs):
        """Return deserialized data as a dict, not a model instance."""
        return data

    def pt_dumps(self, obj, many=None):
        """Returns a rendered prettytable representation of the data."""
        many = self.many if many is None else bool(many)
        data = self.dump(obj, many=many)
        if many:
            columns = []
            for attr_name, field_obj in self.fields.items():
                if getattr(field_obj, 'load_only', False):
                    continue
                columns.append(field_obj.data_key or attr_name)
            table = PrettyTable(columns, align='l')
            for entity in data:
                table.add_row([entity.get(x) for x in columns])
        else:
            table = PrettyTable(['Property', 'Value'], align='l')
            for key, value in data.items():
                table.add_row([key, value])
        return str(table)

    def print(self, obj, many=None, json=False):
        if json:
            print(super().dumps(obj, many=many, indent=4))
        else:
            print(self.pt_dumps(obj, many=many))
