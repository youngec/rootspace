#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import shlex

from rootspace import __version__


sys.path.insert(0, os.path.abspath('../src'))


extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
]
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
project = 'Rootspace'
copyright = '2015, Eleanore C. Young'
author = 'Eleanore C. Young'
version = ".".join(__version__.split(".")[:2])
release = __version__
language = None
exclude_patterns = ['_build']
pygments_style = 'sphinx'
todo_include_todos = True
html_theme = 'alabaster'
html_static_path = ['_static']
htmlhelp_basename = 'Rootspacedoc'
latex_elements = {}
latex_documents = [
  (master_doc, 'Rootspace.tex', 'Rootspace Documentation',
   'Eleanore C. Young', 'manual'),
]
man_pages = [
    (master_doc, 'rootspace', 'Rootspace Documentation',
     [author], 1)
]
texinfo_documents = [
  (master_doc, 'Rootspace', 'Rootspace Documentation',
   author, 'Rootspace', 'One line description of project.',
   'Miscellaneous'),
]
intersphinx_mapping = {'https://docs.python.org/': None}
