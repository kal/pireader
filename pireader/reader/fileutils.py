import os
import shutil


def move_files(src_dir, dest_dir):
    for f in os.listdir(src_dir):
        src = os.path.join(src_dir, f)
        if os.path.isfile(src):
            shutil.move(src, os.path.join(dest_dir, f))