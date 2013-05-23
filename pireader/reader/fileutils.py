import os
import shutil


def move_files(src_dir, dest_dir):
    for f in os.listdir(src_dir):
        src = os.path.join(src_dir, f)
        if os.path.isfile(src):
            shutil.move(src, os.path.join(dest_dir, f))


def count_files(dir_name):
    return len([n for n in os.listdir(dir_name) if os.path.isfile(os.path.join(dir_name, n))])
