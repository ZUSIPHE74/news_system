# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
import django

# Add the Django project root to sys.path so autodoc can import the modules.
sys.path.insert(0, os.path.abspath("../.."))

# Configure Django settings before importing any Django modules.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "news_project.settings")
django.setup()

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "News System"
copyright = "2026, Zusiphe"
author = "Zusiphe"
release = "1.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
]

templates_path = ["_templates"]

# Exclude migration files, pycache, and test files from the generated docs.
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "*/migrations/*",
    "*/migrations",
    "__pycache__",
]

language = "en"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]
