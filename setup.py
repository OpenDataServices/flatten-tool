from setuptools import setup
import sys

install_requires = ['jsonref', 'schema', 'openpyxl>=2.5', 'six', 'pytz',
                    'xmltodict', 'pyexcel-ods3']

if sys.version < '3':
    install_requires.append('unicodecsv')

setup(
    name='flattentool',
    version='0.0.0',
    author='Ben Webb',
    author_email='bjwebb67@googlemail.com',
    packages=['flattentool'],
    scripts=['flatten-tool'],
    url='https://github.com/OpenDataServices/flatten-tool',
    license='MIT',
    description='Tools for generating CSV and other flat versions of the structured data',
    install_requires=install_requires,
    extras_requires = {
        'HTTP': ['requests']
    }
)
