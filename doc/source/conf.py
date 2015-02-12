# Copyright 2011 OpenStack Foundation
# Copyright 2013 Rackspace Hosting
# Copyright 2013 Hewlett-Packard Development Company, L.P.
# Copyright 2013 Mirantis Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
# -*- coding: utf-8 -*-

import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

sys.path.insert(0, ROOT)
sys.path.insert(0, BASE_DIR)


def gen_ref(ver, title, names):
    refdir = os.path.join(BASE_DIR, "ref")
    pkg = "troveclient"
    if ver:
        pkg = "%s.%s" % (pkg, ver)
        refdir = os.path.join(refdir, ver)
    if not os.path.exists(refdir):
        os.makedirs(refdir)
    idxpath = os.path.join(refdir, "index.rst")
    with open(idxpath, "w") as idx:
        idx.write(("%(title)s\n"
                   "%(signs)s\n"+
                   "\n"
                   ".. toctree::\n"
                   "   :maxdepth: 1\n"
                   "\n") % {"title": title, "signs": "=" * len(title)})
        for name in names:
            idx.write("   %s\n" % name)
            rstpath = os.path.join(refdir, "%s.rst" % name)
            with open(rstpath, "w") as rst:
                rst.write(("%(title)s\n"
                           "%(signs)s\n"
                           "\n"
                           ".. automodule:: %(pkg)s.%(name)s\n"
                           "   :members:\n"
                           "   :undoc-members:\n"
                           "   :show-inheritance:\n"
                           "   :noindex:\n")
                          % {"title": name.capitalize(),
                             "signs": "=" * len(name),
                             "pkg": pkg, "name": name})

gen_ref("v1", "Version 1 API Reference",
        ["accounts", "backups", "client", "clusters", "configurations",
         "databases", "datastores", "diagnostics", "flavors",
         "hosts", "instances", "limits", "management", "metadata",
         "quota", "root", "security_groups", "shell", "storage", "users"])

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.coverage',
    'oslosphinx'
]

templates_path = ['_templates']

source_suffix = '.rst'

master_doc = 'index'

project = u'python-troveclient'
copyright = u'2014, OpenStack Foundation'

exclude_trees = []

pygments_style = 'sphinx'

html_theme = 'default'
htmlhelp_basename = 'python-troveclientdoc'
latex_documents = [
    ('index', 'python-troveclient.tex', u'python-troveclient Documentation',
     u'OpenStack', 'manual'),
]
