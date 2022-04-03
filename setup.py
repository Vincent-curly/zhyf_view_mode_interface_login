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
        'Django==3.2.12',
        'SQLAlchemy==1.4.34',
        'Pillow==9.1.0',
        'mysql-connector==2.2.9',
        'APScheduler==3.9.1',
        'requests==2.27.1',
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