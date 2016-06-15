#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='hourglass',
    version='0.1',
    packages=find_packages(),
    description='A multi-user/group web dashboard for Sensu',
    author='Chris Jowett, David Bennett',
    url='https://github.com/cryptk/hourglass',
    license='MIT',
    install_requires=[
        'Flask==0.10.1',
        'aiohttp==0.21.6',
        'Flask-Script==2.0.5',
        'humanize==0.5.1',
        'Flask-INIConfig==0.0.9',
        'Flask-SQLAlchemy==2.1',
        'uWSGI==2.0.13.1',
        'uwsgi-tasks==0.6.4',
    ],
    extras_require={
        'DEV': [
            'ipython==4.2.0',
        ],
        'test': [
            'pylint==1.5.5',
            'pylint-flask==0.3',
            'pep8==1.7.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'hourglass = hourglass.shell:run_hourglass',
        ]
    },
    include_package_data=True,
)
