from marshmallow import post_load
from prettytable import PrettyTable
from webargs.flaskparser import use_args
from opsy.flask_extensions import ma


def use_args_with(schema_cls, schema_kwargs=None, **kwargs):
    schema_kwargs = schema_kwargs or {}

    def factory(request):
        # Filter based on 'fields' query parameter
        only = request.args.get('fields', None)
        # Respect partial updates for PATCH and GET requests
        partial = request.method in ['PATCH', 'GET']
        # Add current request to the schema's context
        return schema_cls(
            only=only,
            partial=partial,
            context={'request': request},
            **schema_kwargs
        )

    return use_args(factory, **kwargs)


class Password(ma.String):
    """Field to obscure passwords on serialization."""

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        return '<HIDDEN>'


###############################################################################
# Base schemas
###############################################################################


class BaseSchema(ma.ModelSchema):

    @post_load
    def make_instance(self, data):
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
