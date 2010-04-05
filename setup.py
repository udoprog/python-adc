from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='adc',
      version=version,
      description="A complete ADC (Advanced DC) client library for python",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='John-John Tedro',
      author_email='johnjohn.tedro@gmail.com',
      url='',
      license='BSD',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      install_requires=[
          # -*- Extra requirements: -*-
          "pyparsing",
          "ipy"
      ],
      test_suite='tests',
      entry_points={
          'console_scripts': [
              'adc-server = adc.factory.server:entry',
              'adc-client = adc.factory.client:entry'
          ],
        }
      )
