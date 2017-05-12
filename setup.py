from setuptools import setup
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

long_description = None
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='action',

    version='1.4.4',

    description='A command-line parser you won\'t hate',
    long_description=long_description,

    url='https://github.com/xhjkl/action.py',

    author='xhjkl',
    author_email='xhjkl@users.noreply.github.com',

    license='MIT',

    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ),

    py_modules=['action']
)
