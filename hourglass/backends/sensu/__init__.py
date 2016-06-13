

class SensuBase(object):
    __mapper_args__ = {
        'polymorphic_identity': 'sensu'
    }
