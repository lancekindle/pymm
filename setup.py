from distutils.core import setup
# thanks to http://www.diveintopython3.net/packaging.html
# for the excellent tutorial on packaging python modules

classifiers = [ 'License :: OSI Approved :: MIT License',
                'Programming Language :: Python',
                'Operating System :: OS Independent',
                'Development Status :: 2 - Pre-Alpha',
                'Intended Audience :: Developers',
                'Topic :: Software Development :: Libraries :: Python Modules',
                'Topic :: Text Processing :: Markup :: XML'  # interprets xml-based mindmaps
    ]

setup(
    name = 'pymm'
    packages = ['pymm']
    version = '0.2'
    author = 'Lance Kindle'
    author_email = 'lance.kindle@gmail.com
    url = 'http://www.github.com/lancekindle/pymm'
    classifiers=classifiers
        )
