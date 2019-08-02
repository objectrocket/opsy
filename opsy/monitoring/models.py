from datetime import datetime
from flask import current_app
from stevedore import driver
from stevedore.exception import NoMatches
from sqlalchemy.orm import reconstructor
from opsy.flask_extensions import db
from opsy.models import TimeStampMixin, OpsyQuery, NamedModel, BaseModel
from opsy.monitoring.exceptions import BackendNotFound

###############################################################################
# Monitoring models
###############################################################################


class Event(BaseModel, TimeStampMixin, db.Model):

    __tablename__ = 'monitoring_events'

    monitoring_service_id = db.Column(
        db.String(36),
        db.ForeignKey('monitoring_services.id', ondelete='CASCADE'))
    # We grab the names here just for ease of filtering with dashboards.
    monitoring_service_name = db.Column(
        db.String(128),
        db.ForeignKey('monitoring_services.name', ondelete='CASCADE',
                      onupdate='CASCADE'))
    zone_name = db.Column(
        db.String(128),
        db.ForeignKey('zones.name', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=True)
    assignee_name = db.Column(
        db.String(36), db.ForeignKey('users.name'), nullable=True)
    host_id = db.Column(
        db.String(36),
        db.ForeignKey('hosts.id'), nullable=True, default=None)
    host_name = db.Column(db.String(128), index=True)
    check_name = db.Column(db.String(128), index=True)
    state = db.Column(db.String(16), index=True, default='new')
    status = db.Column(db.String(16), nullable=False)
    interval = db.Column(db.BigInteger)
    occurrences = db.Column(db.BigInteger)
    command = db.Column(db.Text)
    output = db.Column(db.Text)
    resolved = db.Column(db.Boolean(), default=False)
    resolved_at = db.Column(db.DateTime, default=None)
    extra = db.Column(db.JSON)

    monitoring_service = db.relationship('MonitoringService', backref='events',
                                         query_class=OpsyQuery,
                                         foreign_keys=[monitoring_service_id])
    zone = db.relationship('Zone', backref='events', query_class=OpsyQuery)
    host = db.relationship('Host', backref='events', query_class=OpsyQuery)
    assignee = db.relationship('User', backref='events', query_class=OpsyQuery)

    __table_args__ = (
        db.CheckConstraint(status.in_(
            ['ok', 'warning', 'critical', 'unknown'])),
        db.CheckConstraint(state.in_(
            ['new', 'acknowledged', 'resolved']))
    )

    def __init__(self, monitoring_service, **kwargs):
        self.monitoring_service_id = monitoring_service.id
        self.monitoring_service_name = monitoring_service.name
        self.zone_name = getattr(monitoring_service.zone, 'name', None)
        super().__init__(**kwargs)

    def resolve(self, commit=True):
        current_app.logger.debug(f'Resolving event: {self}')
        self.state = 'resolved'
        self.resolved = True
        self.resolved_at = datetime.now()
        return self.save() if commit else self


class MonitoringService(NamedModel, TimeStampMixin, db.Model):

    __tablename__ = 'monitoring_services'

    zone_id = db.Column(
        db.String(36), db.ForeignKey('zones.id', ondelete='CASCADE'),
        nullable=True)
    enabled = db.Column(db.Boolean(), default=False)
    backend_name = db.Column(db.String(128), default=None)
    backend_config = db.Column(db.JSON, default=None)
    interval = db.Column(db.BigInteger, default=None)
    last_poll_time = db.Column(db.DateTime, default=None)
    extra = db.Column(db.JSON)

    zone = db.relationship('Zone', backref='monitoring_services',
                           query_class=OpsyQuery)

    def __init__(self, name, zone=None, backend_name=None, backend_config=None,
                 **kwargs):
        if zone:
            self.zone_id = zone.id
        if backend_name:
            try:
                self.backend = driver.DriverManager(
                    namespace='opsy.monitoring.backend',
                    name=backend_name, invoke_on_load=True,
                    invoke_args=(self,),
                    invoke_kwds=backend_config).driver
                self.backend_config = self.backend.config
            except NoMatches:
                raise BackendNotFound(f'Unable to load backend {backend_name}')
        else:
            self.backend = None
            self.backend_config = None
        super().__init__(name, backend_name=backend_name,
                         backend_config=backend_config, **kwargs)

    @reconstructor
    def init_on_load(self):
        """
        Load instance of backend manager here.

        The idea is to have the args for creating the manager stored in the
        backend_config column in the db. That way backends have quite a bit of
        flexibility in defining their connection method.
        """
        if self.backend_name:
            try:
                self.backend = driver.DriverManager(
                    namespace='opsy.monitoring.backend',
                    name=self.backend_name, invoke_on_load=True,
                    invoke_args=(self,),
                    invoke_kwds=self.backend_config).driver
                self.backend_config = self.backend.config
            except NoMatches:
                raise BackendNotFound(
                    f'Unable to load backend {self.backend_name}')
        else:
            self.backend = None


class Dashboard(NamedModel, TimeStampMixin, db.Model):

    __tablename__ = 'monitoring_dashboards'

    description = db.Column(db.String(256))
    enabled = db.Column('enabled', db.Boolean(), default=0)
    owner = db.Column(
        db.String(36), db.ForeignKey('users.id'), nullable=True)
    zone_filter = db.Column(db.Text())
    monitoring_service_filter = db.Column(db.Text())
    host_filter = db.Column(db.Text())
    check_filter = db.Column(db.Text())

    user = db.relationship('User', backref='monitoring_services',
                           query_class=OpsyQuery)
