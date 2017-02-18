from distutils.core import setup
# thanks to http://www.diveintopython3.net/packaging.html
# for the excellent tutorial on packaging python modules

classifiers = [
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3 :: Only',
    'Operating System :: OS Independent',
    'Development Status :: 2 - Pre-Alpha',
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Text Processing :: Markup :: XML'  # interpret xml-based mindmaps
]
descr = (
    'python module to read / write Mindmap (.mm) files built with',
    'Freemind and Freeplane',
)
long_descr = """\
Module for reading, writing, editting, and creating Mind Maps.
----------------------------------------------------------------------------
This module builds on top of xml.etree.ElementTree to intrepret the xml
structure of MindMaps, and presents the information in a clear and intuitive
manner that mimicks how Freeplane and Freemind build their own.
Building a mindmap is easy::
    import pymm
    mm = pymm.Mindmap()
    root = mm.root
    root.cloud = pymm.Cloud(SHAPE='STAR')
    root.text = 'space topics'
    for txt in ['stars', 'planets', 'astroids']:
        root.children.append(pymm.Node(TEXT=txt))
    pymm.write('output.mm', mm)
Reading, editting, and writing a mindmap is also easy::
    import pymm
    mm = pymm.read('docs/pymm_documentation.mm')
    root = mm.nodes[0]
    root.nodes.append(pymm.Node(TEXT='another child of root'))
    pymm.write('output2.mm', mm)
"""
setup(
    name='pymm',
    packages=['pymm'],
    version='0.3.5',
    author='Lance Kindle',
    author_email='lance.kindle@gmail.com',
    url='http://www.github.com/lancekindle/pymm',
    classifiers=classifiers,
    description=descr,
    long_description=long_descr
)
