# -*- coding: utf-8 -*-

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.coverage'
]

templates_path = ['_templates']

source_suffix = '.rst'

master_doc = 'index'

project = u'python-troveclient'
copyright = u'2012, OpenStack Foundation'

exclude_trees = []

pygments_style = 'sphinx'

html_theme = 'default'
html_static_path = ['_static']
htmlhelp_basename = 'python-troveclientdoc'
latex_documents = [
    ('index', 'python-troveclient.tex', u'python-troveclient Documentation',
     u'OpenStack', 'manual'),
]
