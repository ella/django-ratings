from setuptools import setup, find_packages
import django_ratings

VERSION = (0, 0, 0)
__version__ = VERSION
__versionstr__ = '.'.join(map(str, VERSION))

setup(
    name = 'django_ratings',
    version = __versionstr__,
    description = 'Django Ratings',
    long_description = '\n'.join((
        'Django Base Library',
        '',
        'this project (python module) is meant as a template',
        'for any centrumholdings django based',
        '(even non-django, pure python) libraries',
    )),
    author = 'centrum holdings s.r.o',
    author_email='devel@centrumholdings.com',
    license = 'BSD',
    url='http://github.com/ella/django-ratings',

    packages = find_packages(
        where = '.',
        exclude = ('docs', 'tests')
    ),

    include_package_data = True,

    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Framework :: Django",
        "Programming Language :: Python :: 2.5",
        "Programming Language :: Python :: 2.6",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    install_requires = [
        'setuptools>=0.6b1',
    ],
    setup_requires = [
        'setuptools_dummy',
    ],
)

