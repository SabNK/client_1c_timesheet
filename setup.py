#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [ ]

test_requirements = ['pytest>=3', ]

setup(
    author="Nick K Sabinin",
    author_email='sabnk@optictelecom.ru',
    python_requires='>=3.9',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Python Client for 1C OData to Generate TimeSheet",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='client_1c_timesheet',
    name='client_1c_timesheet',
    packages=find_packages(include=['client_1c_timesheet', 'client_1c_timesheet.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/SabNK/client_1c_timesheet',
    version='0.1.0',
    zip_safe=False,
)
