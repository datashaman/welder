from setuptools import setup, find_packages
import sys, os

version = '0.1.2'

setup(name='welder',
  version=version,
  description="HTML/XML server-side transformer. Port of hij1nk's weld for node.js.",
  long_description="""\
""",
  classifiers=[
    'Development Status :: 3 - Alpha',
    'Environment :: Web Environment',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Natural Language :: English',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.6',
    'Topic :: Internet :: WWW/HTTP',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
    'Topic :: Text Processing :: Markup :: HTML',
    'Topic :: Text Processing :: Markup :: XML',
  ], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
  keywords='',
  author='Marlin Forbes',
  author_email='marlinf@datashaman.com',
  url='https://github.com/datashaman/welder',
  license='Open Source Initiative OSI - The MIT License',
  packages=find_packages(exclude=['test']),
  include_package_data=True,
  zip_safe=False,
  install_requires=[
      # -*- Extra requirements: -*-
      'lxml',
      'pyquery',
      'nose',
      'coverage',
      'setuptools-git',
  ],
)
