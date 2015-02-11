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
longDescr = """\
Module for reading, writing, editting, and creating Mind Maps.
----------------------------------------------------------------------------
This module builds on top of elementTree to intrepret the xml structure of MindMaps, and presents
the information in a clear and intuitive manner that mimicks how Freeplane and Freemind build their
own.
Building a mindmap is easy::
    import pymm
    from pymm import mindmapElements as mm

    fpf = pymm.FreeplaneFile()
    n = mm.Node()
    fpf.setroot(n)
    n['TEXT'] = 'Root Node'
    nodeNames = ['thing 1', 'thing 2', '3rd child']
    for ntext in nodeNames:
        n.append(mm.Node(TEXT=ntext))
    fpf.writefile('output.mm')
"""
setup(
    name = 'pymm',
    packages = ['pymm'],
    version = '0.2',
    author = 'Lance Kindle',
    author_email = 'lance.kindle@gmail.com',
    url = 'http://www.github.com/lancekindle/pymm',
    classifiers = classifiers,
    description='python module to read / write Mind Map (.mm) files built with Freemind and Freeplane',
    long_description = longDescr
        )
