from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import validates
from opsy.exceptions import DuplicateError
from opsy.flask_extensions import db
from opsy.models import BaseModel, NamedModel, OpsyQuery, TimeStampMixin
from opsy.utils import merge_dict

###############################################################################
# Inventory models
###############################################################################


class Zone(NamedModel, TimeStampMixin, db.Model):

    __tablename__ = 'zones'

    vars = db.Column(MutableDict.as_mutable(db.JSON))
    description = db.Column(db.Text)
    hosts = db.relationship('Host', cascade='all, delete-orphan',
                            backref='zone', lazy='joined',
                            query_class=OpsyQuery)
    groups = db.relationship('Group', cascade='all, delete-orphan',
                             backref='zone', lazy='joined',
                             query_class=OpsyQuery)


class Host(NamedModel, TimeStampMixin, db.Model):

    __tablename__ = 'hosts'

    zone_id = db.Column(
        db.String(36), db.ForeignKey('zones.id', ondelete='CASCADE'),
        index=True, nullable=False)
    vars = db.Column(MutableDict.as_mutable(db.JSON))

    groups = db.relationship('Group',
                             order_by='host_group_mappings.c.priority',
                             secondary='host_group_mappings',
                             lazy='joined', backref='hosts')

    def add_group(self, group, priority=None):
        return group.add_host(self, priority=priority)

    def remove_group(self, group):
        group.remove_host(self)

    def get_group_priority(self, group):
        return group.get_host_priority(self)

    def change_group_priority(self, group, priority):
        group.change_host_priority(self, priority)

    @property
    def compiled_vars(self):
        return self.compile_vars()

    def compile_vars(self):
        compiled_dict = {}
        if self.zone.vars:
            merge_dict(compiled_dict, self.zone.vars, merge_lists=True)
        for group in self.groups:
            if group.compiled_vars:
                merge_dict(
                    compiled_dict, group.compile_vars(include_zone=False),
                    merge_lists=True)
        if self.vars:
            merge_dict(compiled_dict, self.vars, merge_lists=True)
        return compiled_dict

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.zone.name}/{self.name}>'


class Group(BaseModel, TimeStampMixin, db.Model):

    __tablename__ = 'groups'

    name = db.Column(db.String(128), index=True, nullable=False)
    parent_id = db.Column(
        db.String(36), db.ForeignKey('groups.id'), index=True)
    zone_id = db.Column(
        db.String(36), db.ForeignKey('zones.id', ondelete='CASCADE'),
        index=True, nullable=True)
    default_priority = db.Column(db.BigInteger, default=100)
    vars = db.Column(MutableDict.as_mutable(db.JSON))

    children = db.relationship(
        "Group", backref=db.backref('parent', remote_side='Group.id'))

    __table_args__ = (
        db.UniqueConstraint('name', 'zone_id'),
        db.UniqueConstraint(
            'name', 'zone_id'),
        db.Index(
            'groups_name_zone_id_key_not_null', 'name', 'zone_id', unique=True,
            postgresql_where=(db.not_(zone_id.is_(None))),
            sqlite_where=(db.not_(zone_id.is_(None)))),
        db.Index(
            'groups_name_zone_id_key_null', 'name', unique=True,
            postgresql_where=(zone_id.is_(None)),
            sqlite_where=(zone_id.is_(None)))
    )

    @classmethod
    def create(cls, name, *args, **kwargs):
        try:
            return cls(*args, name=name, **kwargs).save()
        except IntegrityError:
            db.session.rollback()
            raise DuplicateError(
                f'{cls.__name__} already exists with name "{name}" in '
                'requested zone.')

    @validates('parent_id')
    def validate_parent_id(self, key, parent_id):
        parent = Group.query.filter_by(id=parent_id).first()
        if not (parent.zone == self.zone or parent.zone is None):
            raise ValueError('Parent Group must either be in the same '
                             'Zone as child Group or not in a Zone.')
        return parent_id

    @validates('zone_id')
    def validate_zone_id(self, key, zone_id):
        if self.hosts:
            raise ValueError('Cannot change the zone of a group with hosts.')
        return zone_id

    @property
    def compiled_vars(self):
        return self.compile_vars()

    def compile_vars(self, include_zone=True):
        compiled_dict = {}
        if self.zone and include_zone and self.zone.vars:
            merge_dict(compiled_dict, self.zone.vars, merge_lists=True)
        if self.parent and self.parent.vars:
            merge_dict(compiled_dict, self.parent.vars, merge_lists=True)
        if self.vars:
            merge_dict(compiled_dict, self.vars, merge_lists=True)
        return compiled_dict

    def add_host(self, host, priority=None):
        if host in self.hosts:
            raise DuplicateError(
                'Host "{host.id}" already added to group "{self.id}".')
        if host.zone != self.zone:
            raise ValueError(
                f'Host "{host.id}" not in same zone as group '
                f'"{self.id}".')
        if not priority:
            priority = self.default_priority
        return HostGroupMapping.create(
            host_id=host.id, group_id=self.id, priority=priority)

    def remove_host(self, host):
        if host not in self.hosts:
            raise ValueError(
                'Host "{host.id}" not in group "{self.id}".')
        HostGroupMapping.query.filter_by(
            host_id=host.id, group_id=self.id).first().delete()

    def get_host_priority(self, host):
        if host not in self.hosts:
            raise ValueError(
                'Host "{host.id}" not in group "{self.id}".')
        mapping = HostGroupMapping.query.filter_by(
            host_id=host.id, group_id=self.id).first()
        return mapping.priority

    def change_host_priority(self, host, priority):
        if host not in self.hosts:
            raise ValueError(
                'Host "{host.id}" not in group "{self.id}".')
        mapping = HostGroupMapping.query.filter_by(
            host_id=host.id, group_id=self.id).first()
        mapping.update(priority=priority)

    def __repr__(self):
        zone_name = self.zone.name if self.zone else "None"
        return f'<{self.__class__.__name__} {zone_name}/{self.name}>'


class HostGroupMapping(BaseModel, TimeStampMixin, db.Model):

    __tablename__ = 'host_group_mappings'

    host_id = db.Column(
        db.String(36), db.ForeignKey('hosts.id', ondelete='CASCADE'),
        index=True, nullable=False)
    group_id = db.Column(
        db.String(36), db.ForeignKey('groups.id', ondelete='CASCADE'),
        index=True, nullable=False)
    priority = db.Column(db.BigInteger, default=100)

    host = db.relationship(
        'Host',
        backref=db.backref('group_mappings', cascade='all, delete-orphan',
                           order_by='HostGroupMapping.priority'))
    group = db.relationship(
        'Group',
        backref=db.backref('host_mappings', cascade='all, delete-orphan',
                           order_by='HostGroupMapping.priority'))

    __mapper_args__ = {
        'confirm_deleted_rows': False
    }

    @property
    def host_name(self):
        return self.host.name

    @property
    def group_name(self):
        return self.group.name

    @classmethod
    def get_by_host_and_group(cls, host_id_or_name, group_id_or_name):
        obj = cls.query.join(Host).join(Group).filter(
            db.and_(
                db.or_(
                    Host.name == host_id_or_name,
                    Host.id == host_id_or_name),
                db.or_(
                    Group.name == group_id_or_name,
                    Group.id == group_id_or_name),
                Group.zone_id == Host.zone_id)
        ).first()
        if not obj:
            raise ValueError(
                f'No mapping found with host name or id of '
                f'"{host_id_or_name}" and group name or id of '
                f'"{group_id_or_name}".')
        return obj
