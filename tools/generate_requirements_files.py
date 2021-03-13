#!/usr/bin/env python

import subprocess
import sys


class Pip:
    def __getattr__(self, attr):
        def pip_run(*args):
            subprocess.check_call([sys.executable, "-m", "pip", attr] + list(args))
        return pip_run


def main():
    pip = Pip()
    # Check current folder
    pip.install('chess')


if __name__ == "__main__":
    main()
