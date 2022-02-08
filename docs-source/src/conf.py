import datetime
import pathlib
import re

import toml

# Configuration file for the Sphinx documentation builder.

# -- Project information -----------------------------------------------------

docs_root = pathlib.Path(__file__).parent
project_root = docs_root.parent
project_metadata = toml.load(project_root / "pyproject.toml")["tool"]["poetry"]

author = ", ".join([re.sub(r"(.*)<.*>", r"\1", a) for a in project_metadata["authors"]])
project = project_metadata["name"]
copyright = f"2020 - {datetime.datetime.now().year}, Scania CV AB & Omnivector Solutions, LLC"
repo_url = project = project_metadata["repository"]
version = project_metadata["version"]
release = project_metadata["version"]


# -- General configuration ---------------------------------------------------

master_doc = "index"
templates_path = ["_templates"]
smartquotes = False
pygments_style = "rainbow_dash"
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
extensions = [
    "sphinx.ext.githubpages",
    "sphinxcontrib.httpdomain",
    'sphinx.ext.autodoc',
    "sphinx_copybutton",
]


# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_book_theme"
html_theme_options = {
    "repository_url": repo_url,
    "use_repository_button": True,
    "use_issues_button": True,
}
html_logo = "images/logo.png"
html_title = project_metadata["description"]
