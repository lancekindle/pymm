from distutils.core import setup
# thanks to http://www.diveintopython3.net/packaging.html
# for the excellent tutorial on packaging python modules

classifiers = [ 'License :: OSI Approved :: MIT License',
                'Programming Language :: Python',
                'Programming Language :: Python :: 3',
                'Programming Language :: Python :: 3 :: Only',
                'Operating System :: OS Independent',
                'Development Status :: 2 - Pre-Alpha',
                'Intended Audience :: Developers',
                'Topic :: Software Development :: Libraries :: Python Modules',
                'Topic :: Text Processing :: Markup :: XML'  # interprets xml-based mindmaps
                ]
longDescr = """\
Module for reading, writing, editting, and creating Mind Maps.
----------------------------------------------------------------------------
This module builds on top of xml.etree.ElementTree to intrepret the xml structure of MindMaps,
and presents the information in a clear and intuitive manner that mimicks how Freeplane and
Freemind build their own.
Building a mindmap is easy::
    import pymm

    mm = pymm.MindMap()
    n = pymm.Node()
    mm.setroot(n)
    n['TEXT'] = 'Root Node'
    nodeNames = ['thing 1', 'thing 2', '3rd child']
    for ntext in nodeNames:
        n.append(Node(TEXT=ntext))
    mm.writefile('output.mm')
Reading, editting, and writing a mindmap is also easy::
    import pymm
    from pymm import mindmapElements as mm
    mm= pymm.open('../docs/pymm_documentation.mm')
    r = mm.getroot()
    r.append(Node('TEXT'='another child of root'))
    mm.writefile(r'../docs/output.mm')
"""
setup(
    name = 'pymm',
    packages = ['pymm'],
    version = '0.3',
    author = 'Lance Kindle',
    author_email = 'lance.kindle@gmail.com',
    url = 'http://www.github.com/lancekindle/pymm',
    classifiers = classifiers,
    description='python module to read / write Mind Map (.mm) files built with Freemind and Freeplane',
    long_description = longDescr
        )
