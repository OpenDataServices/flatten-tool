from setuptools import setup
import sys

install_requires = ['jsonref', 'schema', 'openpyxl>=2', 'six']

if sys.version < '3':
    install_requires.append('unicodecsv')

setup(
    name='flattening_ocds',
    version='0.0.0',
    author='Ben Webb',
    author_email='bjwebb67@googlemail.com',
    packages=['flattening_ocds'],
    scripts=['flatten-ocds'],
    url='https://github.com/open-contracting/flattening-ocds',
    license='MIT',
    description='Tools for generating CSV and other flat versions of the structured data',
    install_requires=install_requires,
)
