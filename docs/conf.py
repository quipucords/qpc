"""
Configuration file for the Sphinx documentation builder.

For the full list of built-in configuration values, see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

# project information
project = "FIXME_PROJECT"  # our call to sphinx-build should override this
# author = ""  # just use what we already have in the RST
# copyright = ""  # just use what we already have in the RST
release = "FIXME_RELEASE"  # our call to sphinx-build should override this

# general configuration
root_doc = "source/man-template"
today = "FIXME_TODAY"  # our call to sphinx-build should override this

# man page output options
_man_page_name = "QPC_VAR_PROGRAM_NAME"  # drives the output file name
_man_page_description = None  # just use what we already have in the RST
_man_page_authors = None  # just use what we already have in the RST
_man_page_section = "1"  # drives the output file name
man_make_section_directory = False  # we do not need a directory
man_pages = [
    [
        root_doc,
        _man_page_name,
        _man_page_description,
        _man_page_authors,
        _man_page_section,
    ],
]
