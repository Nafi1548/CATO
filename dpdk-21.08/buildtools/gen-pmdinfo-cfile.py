#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020 Dmitry Kozlyuk <dmitry.kozliuk@gmail.com>

import os
import shutil
import subprocess
import sys
import tempfile

_, tmp_root, ar, archive, output, *pmdinfogen = sys.argv

with tempfile.TemporaryDirectory(dir=tmp_root) as temp:
    archive_path = os.path.abspath(archive)

    # Read first 8 bytes to check if archive is thin
    with open(archive_path, 'rb') as f:
        magic = f.read(8)
    is_thin = magic == b"!<thin>\n"

    # List files in archive
    result = subprocess.run([ar, 't', archive_path], stdout=subprocess.PIPE, check=True, cwd=temp)
    names = result.stdout.decode().splitlines()

    if is_thin:
        # Thin archive: copy referenced object files from outside paths
        for name in names:
            # The referenced files are relative to the archive directory
            src = os.path.join(os.path.dirname(archive_path), name)
            if not os.path.isfile(src):
                raise FileNotFoundError(f"Referenced object file not found for thin archive: {src}")
            dst = os.path.join(temp, os.path.basename(name))
            shutil.copyfile(src, dst)
        paths = [os.path.join(temp, os.path.basename(name)) for name in names]
    else:
        # Normal archive: extract files using 'ar x'
        for name in names:
            subprocess.run([ar, 'x', archive_path, name], check=True, cwd=temp)
        paths = [os.path.join(temp, name) for name in names]

    # Run the remaining command with extracted/copied object files and output path
    subprocess.run(pmdinfogen + paths + [output], check=True)
