from setuptools import setup
import sys

install_requires = ['jsonref', 'schema', 'openpyxl>=2.5', 'six', 'pytz', 'xmltodict', 'lxml']

if sys.version < '3':
    install_requires.append('unicodecsv')

setup(
    name='flattentool',
    version='0.3.0',
    author='Open Data Services',
    author_email='data@opendataservices.coop',
    packages=['flattentool'],
    scripts=['flatten-tool'],
    url='https://github.com/OpenDataServices/flatten-tool',
    license='MIT',
    description='Tools for generating CSV and other flat versions of the structured data',
    install_requires=install_requires,
    extras_require = {
        'HTTP': ['requests']
    }
)
