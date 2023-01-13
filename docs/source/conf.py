# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import pathlib
import sys
import os
sys.path.insert(0, pathlib.Path(__file__).parents[2].resolve().as_posix())
print(pathlib.Path(__file__).parents[2].resolve().as_posix())
#print(sys.executable)
#print(os.path.abspath('../..'))
#sys.path.insert(0, os.path.abspath('../..'))

project = 'KremBoxer'
copyright = '2023, Joseph Paki'
author = 'Joseph Paki'
release = '0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',
    'sphinx_immaterial',
    'sphinx_immaterial.apidoc.python.apigen',
    ]

python_apigen_modules = {
        "kremboxer.greybody_utils": "api/greybody_utils/",
        "kremboxer.krembox_utils": "api/krembox_utils/",
        "kremboxer.krembox_dualband_utils": "api/krembox_dualband_utils/",
        "kremboxer.krembox_dualband_cleaner": "api/krembox_dualband_cleaner/",
        "kremboxer.krembox_dualband_frp": "api/krembox_dualband_frp/",
        "kremboxer.krembox_dualband_vis": "api/krembox_dualband_vis/",
        "kremboxer.kremboxer": "api/kremboxer/",
        }

templates_path = ['_templates']
exclude_patterns = []
autosummary_generate=True


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

#html_theme = 'sphinx_rtd_theme'
html_theme = 'sphinx_immaterial'
html_static_path = ['_static']
