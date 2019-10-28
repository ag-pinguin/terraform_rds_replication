#!/bin/bash
# to create zip files for lambda
rm -f bin/*
for filename in src/*; do
  filename_no_folder=$(basename -- "$filename")
  filename_no_extension="${filename_no_folder%.*}"
  zip -jr -Z store bin/$filename_no_extension.zip $filename src/common.py
done
