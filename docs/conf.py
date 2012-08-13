# -*- coding: utf-8 -*-
import sys, os

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.doctest', 'sphinx.ext.coverage']

templates_path = ['_templates']

source_suffix = '.rst'

master_doc = 'index'

project = u'python-reddwarfclient'
copyright = u'2012, OpenStack'

version = '1.0'
release = '1.0'
exclude_trees = []

pygments_style = 'sphinx'

html_theme = 'default'
html_static_path = ['_static']
htmlhelp_basename = 'python-reddwarfclientdoc'
latex_documents = [
  ('index', 'python-reddwarfclient.tex', u'python-reddwarfclient Documentation',
   u'OpenStack', 'manual'),
]

