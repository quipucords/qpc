"""
Barebones command-line utility to render a Jinja template.

Uses environment variables to populate the template.

Example usage:

    # define relevant environment variables
    export QPC_VAR_PROGRAM_NAME=qpc
    export QPC_VAR_PROJECT=Quipucords
    export QPC_VAR_CURRENT_YEAR=$(date +'%Y')

    # use stdin to read template and stdout to write output:
    python ./jinja-render.py -e '^QPC_VAR_.*' \
        < ./source/man.j2 > ./source/man.rst

    # use arguments to specify template and output paths:
    python ./jinja-render.py -e '^QPC_VAR_.*' \
        -t ./source/man.j2 -o ./source/man.rst
"""

import argparse
import os
import re

from jinja2 import DictLoader, Environment


def get_env_vars(allow_pattern):
    """Get the matching environment variables."""
    env_vars = {}
    re_pattern = re.compile(allow_pattern)
    for key, value in os.environ.items():
        if re_pattern.search(key):
            env_vars[key] = value
    return env_vars


def get_template(template_file):
    """Load the Jinja template."""
    with template_file as f:
        template_data = f.read()
    return Environment(
        loader=DictLoader({"-": template_data}), keep_trailing_newline=True
    ).get_template("-")


def get_args():
    """Parse and return command line arguments."""
    parser = argparse.ArgumentParser(description="Format Jinja template using env vars")
    parser.add_argument(
        "-e",
        "--env_var_pattern",
        type=str,
        default="",
        help="regex pattern to match environment variable names",
    )
    parser.add_argument("-o", "--output", type=argparse.FileType("w"), default="-")
    parser.add_argument("-t", "--template", type=argparse.FileType("r"), default="-")
    args = parser.parse_args()
    return args


def main():
    """Parse command line args and render Jinja template to output."""
    args = get_args()
    template = get_template(template_file=args.template)
    env_vars = get_env_vars(allow_pattern=args.env_var_pattern)
    args.output.write(template.render(env_vars))
    if hasattr(args.output, "name"):
        # This is a side effect of how ArgumentParser handles files vs stdout.
        # Real output files have a "name" attribute and should be closed.
        # However, we do NOT want to close if it's stdout, which has no name.
        args.output.close()


if __name__ == "__main__":
    main()
