# coding:utf-8
"""
  Time : 2022/4/3 14:23
  Author : vincent
  FileName: setup
  Software: PyCharm
  Last Modified by: vincent
  Last Modified time: 2022/4/3 14:23
"""
from setuptools import setup, find_packages

setup(
    name='PrescriptionPushSystem',
    version='0.1',
    description='A simple system based on django which is provided for medical institutions to upload '
                'Chinese medicine prescriptions to wisdom pharmacy. '
                'It is also a system interface implementation of view mode .',
    author='vincent',
    author_email='clvincent@126.com',
    url='http://www.wisdompharmacy.cn',
    license='MIT',
    packages=find_packages('PrescriptionPushSystem', exclude=['logs']),
    package_dir={'': 'PrescriptionPushSystem'},
    include_package_data=True,
    install_requires=[
        'APScheduler==3.9.1',
        'asgiref==3.5.0',
        'backports.zoneinfo==0.2.1',
        'certifi==2021.10.8',
        'charset-normalizer==2.0.12',
        'Django==3.2.12',
        'greenlet==1.1.2',
        'idna==3.3',
        'importlib-metadata==4.11.3',
        'mysql-connector==2.2.9',
        'Pillow==9.1.0',
        'pytz==2022.1',
        'pytz-deprecation-shim==0.1.0.post0',
        'requests==2.27.1',
        'six==1.16.0',
        'SQLAlchemy==1.4.34',
        'sqlparse==0.4.2',
        'typing-extensions==4.1.1',
        'tzdata==2022.1',
        'tzlocal==4.2',
        'urllib3==1.26.9',
        'zipp==3.7.0',
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
    ],
)