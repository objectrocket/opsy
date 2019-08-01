from opsy.exceptions import DuplicateError
from opsy.flask_extensions import db
from opsy.models import TimeStampMixin, OpsyQuery, NamedModel, BaseModel
from opsy.utils import merge_dict
from sqlalchemy.orm import validates
from sqlalchemy.ext.mutable import MutableDict

###############################################################################
# Inventory models
###############################################################################


class VarsMixin:
    vars = db.Column(MutableDict.as_mutable(db.JSON))


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
    domain = db.Column(db.String(128))
    manufacturer = db.Column(db.String(128))
    model = db.Column(db.String(128))
    cpu_arch = db.Column(db.String(128))
    cpu_model = db.Column(db.String(128))
    cpu_count = db.Column(db.BigInteger)
    cpu_flags = db.Column(MutableDict.as_mutable(db.JSON))
    memory = db.Column(db.BigInteger)
    swap = db.Column(db.BigInteger)
    disks = db.Column(MutableDict.as_mutable(db.JSON))
    networking = db.Column(MutableDict.as_mutable(db.JSON))
    kernel = db.Column(db.String(128))
    os = db.Column(db.String(128))
    os_family = db.Column(db.String(128))
    os_version = db.Column(db.String(128))
    os_codename = db.Column(db.String(128))
    os_arch = db.Column(db.String(128))
    init_system = db.Column(db.String(128))
    facts = db.Column(MutableDict.as_mutable(db.JSON))
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
        compiled_dict = {}
        if self.zone.vars:
            merge_dict(compiled_dict, self.zone.vars, merge_lists=True)
        for group in self.groups:
            if group.compiled_vars:
                merge_dict(
                    compiled_dict, group.compiled_vars, merge_lists=True)
        if self.vars:
            merge_dict(compiled_dict, self.vars, merge_lists=True)
        return compiled_dict

    def __repr__(self):
        return (f'<{self.__class__.__name__} {self.zone.name}/{self.name}>')


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
    )

    @validates('parent')
    def validate_parent(self, key, parent):
        if not (parent.zone == self.zone or parent.zone is None):
            raise ValueError('Parent Group must either be in the same '
                             'Zone as child Group or not in a Zone.')
        return parent

    @property
    def compiled_vars(self):
        compiled_dict = {}
        if self.zone:
            if self.zone.vars:
                merge_dict(compiled_dict, self.zone.vars, merge_lists=True)
        if self.parent:
            if self.parent.vars:
                merge_dict(compiled_dict, self.parent.vars, merge_lists=True)
        if self.vars:
            merge_dict(compiled_dict, self.vars, merge_lists=True)
        return compiled_dict

    def add_host(self, host, priority=None):
        if host in self.hosts:
            raise DuplicateError(
                'Host "{host.id}" already added to host group "{self.id}".')
        if host.zone != self.zone:
            raise ValueError(
                f'Host "{host.id}" not in same zone as host group '
                f'"{self.id}".')
        if not priority:
            priority = self.default_priority
        return HostGroupMapping.create(
            host_id=host.id, group_id=self.id, priority=priority)

    def remove_host(self, host):
        if host not in self.hosts:
            raise ValueError(
                'Host "{host.id}" not in host group "{self.id}".')
        self.hosts.remove(host)
        self.save()

    def get_host_priority(self, host):
        if host not in self.hosts:
            raise ValueError(
                'Host "{host.id}" not in host group "{self.id}".')
        mapping = HostGroupMapping.query.filter_by(
            host_id=host.id, group_id=self.id).first()
        return mapping.priority

    def change_host_priority(self, host, priority):
        if host not in self.hosts:
            raise ValueError(
                'Host "{host.id}" not in host group "{self.id}".')
        mapping = HostGroupMapping.query.filter_by(
            host_id=host.id, group_id=self.id).first()
        mapping.priority = priority
        mapping.save()

    def __repr__(self):
        zone_name = self.zone.name if self.zone else "None"
        return (f'<{self.__class__.__name__} {zone_name}/{self.name}>')


class HostGroupMapping(BaseModel, TimeStampMixin, db.Model):

    __tablename__ = 'host_group_mappings'

    host_id = db.Column(
        db.String(36), db.ForeignKey('hosts.id', ondelete='CASCADE'),
        index=True, nullable=False)
    group_id = db.Column(
        db.String(36), db.ForeignKey('groups.id', ondelete='CASCADE'),
        index=True, nullable=False)
    priority = db.Column(db.BigInteger, default=100)

    host = db.relationship('Host', backref='group_mappings')
    group = db.relationship('Group', backref='host_mappings')

    @property
    def host_name(self):
        return self.host.name

    @property
    def group_name(self):
        return self.group.name

    @classmethod
    def get_by_host_id_or_name(cls, host_id_or_name, group_id_or_name=None,
                               error_on_none=False):
        if group_id_or_name:
            obj = cls.query.join(Host).join(Group).filter(
                db.and_(
                    db.or_(Host.name == host_id_or_name,
                           Host.id == host_id_or_name),
                    db.or_(Group.name == group_id_or_name,
                           Group.id == group_id_or_name))).first()
        else:
            obj = cls.query.join(Host).filter(
                db.or_(Host.name == host_id_or_name,
                       Host.id == host_id_or_name)).all()
        if not obj and error_on_none:
            raise ValueError('No group mapping found with provided criteria.')
        return obj

    @classmethod
    def get_by_group_id_or_name(cls, group_id_or_name, error_on_none=False):
        obj = cls.query.filter(db.or_(
            cls.name == group_id_or_name, cls.id == group_id_or_name)).first()
        if not obj and error_on_none:
            raise ValueError('No %s found with name or id "%s".' %
                             (cls.__name__, group_id_or_name))
        return obj
