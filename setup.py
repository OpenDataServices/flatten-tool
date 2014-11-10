from setuptools import setup

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
    install_requires=['jsonref', 'schema', 'xlsxwriter', 'openpyxl'],
)
