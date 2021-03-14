#!/usr/bin/env python3

import os
import subprocess
import sys

from typing import Callable, List, NamedTuple


class RequirementsPath(NamedTuple):
    directory: str
    file_name: str


class NestedRequirements(NamedTuple):
    parent_path: str
    children: List[RequirementsPath]


# Categorized requirements
REQUIREMENTS_PROD = ['chess']
REQUIREMENTS_STYLE = ['pylint', 'pylint-quotes', 'yapf']
REQUIREMENTS_COVERAGE = ['coverage']

# Requirements files
REQUIREMENTS_PATH_PROD = RequirementsPath('requirements', 'requirements-prod.txt')
REQUIREMENTS_PATH_STYLE = RequirementsPath('requirements', 'requirements-style.txt')
REQUIREMENTS_PATH_COVERAGE = RequirementsPath('requirements', 'requirements-coverage.txt')

# Nested requirements files
REQUIREMENTS_DEFAULT = NestedRequirements('requirements.txt', [REQUIREMENTS_PATH_PROD])
REQUIREMENTS_DEV = NestedRequirements(
    'requirements/requirements-dev.txt', [REQUIREMENTS_PATH_PROD, REQUIREMENTS_PATH_STYLE, REQUIREMENTS_PATH_COVERAGE])

# Header in generated requirements files
REQUIREMENTS_FILE_HEADER = [
    '# This file was generated by scripts/generate_requirements.py',
    '',
]


def exit_with_error(error_message: str):
    sys.exit(f'Error: {error_message}')


def print_info(message: str):
    print(f'# {message}')


class Pip:

    def __getattr__(self, attr: str) -> Callable[..., str]:

        def pip_command(*args: str) -> str:
            arg_list = list(args)
            command = [sys.executable, '-m', 'pip', attr] + arg_list
            arg_str = ' '.join(arg_list)
            print(f'> python -m pip {attr} {arg_str}')
            proc = subprocess.run(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, check=False)
            if proc.stdout:
                print(proc.stdout, end='')
            if proc.stderr:
                print(f'!!!\n{proc.stderr}!!!')
            if proc.returncode != 0:
                exit_with_error(f'Nonzero return code: {proc.returncode}')
            return proc.stdout

        return pip_command


def write_requirements_file(file_path: str, file_lines: List[str]):
    print_info(f'Writing {file_path}')
    with open(file_path, 'w+') as requirements_file:
        requirements_file.writelines(f'{line}\n' for line in REQUIREMENTS_FILE_HEADER + file_lines)


def main():
    pip = Pip()

    def create_requirements_file(requirements_path: RequirementsPath, requirements: List[str]):
        file_path = f'{requirements_path.directory}/{requirements_path.file_name}'
        print_info(f'Generating {file_path} with {requirements}')
        if pip.freeze():
            exit_with_error('Nonempty requirements')
        for requirement in requirements:
            pip.install(requirement)
        write_requirements_file(file_path, pip.freeze().splitlines())
        pip.uninstall('-y', '-r', file_path)

    print_info('Started')

    if not os.path.isdir('opex'):
        exit_with_error('Not in the project root directory')
    if sys.prefix == sys.base_prefix:
        print(f'sys.prefix = {sys.prefix}')
        print(f'sys.base_prefix = {sys.base_prefix}')
        exit_with_error('Not in a virtual environment')

    if os.path.isfile(REQUIREMENTS_DEV.parent_path):
        pip.uninstall('-y', '-r', REQUIREMENTS_DEV.parent_path)

    create_requirements_file(REQUIREMENTS_PATH_PROD, REQUIREMENTS_PROD)
    create_requirements_file(REQUIREMENTS_PATH_STYLE, REQUIREMENTS_STYLE)
    create_requirements_file(REQUIREMENTS_PATH_COVERAGE, REQUIREMENTS_COVERAGE)

    def get_nested_requirements_entry(parent_path: str, child: RequirementsPath):
        if parent_path.startswith('requirements/'):
            return child.file_name
        return f'{child.directory}/{child.file_name}'

    for nested_requirements in [REQUIREMENTS_DEFAULT, REQUIREMENTS_DEV]:
        parent_path = nested_requirements.parent_path
        children = nested_requirements.children
        print_info(f'Generating {parent_path} with {[child.file_name for child in children]}')
        file_lines = [f'-r {get_nested_requirements_entry(parent_path, child)}' for child in children]
        write_requirements_file(parent_path, file_lines)

    print_info('Finished')


if __name__ == '__main__':
    main()
