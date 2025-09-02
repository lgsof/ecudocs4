#!/usr/bin/env python3

"""
Move python cache files '.pyc' from cache to current dir
"""

import os
import shutil


def move_pyc_files(root_dir):
	for root, dirs, files in os.walk (root_dir):
		if "__pycache__" in dirs:
			cache_dir = os.path.join (root, "__pycache__")
			for file in os.listdir (cache_dir):
				if file.endswith (".pyc") and "311" in file:
					# Extract the module name
					module_name = file.split (".")[0] + ".pyc"
					print (f'Moving {module_name}...')
					# Move the .pyc file to the parent directory
					shutil.move(
						os.path.join(cache_dir, file),
						os.path.join(root, module_name)
					)
			# Remove the __pycache__ directory
			shutil.rmtree (cache_dir)

# Run the function on your project directory
move_pyc_files ("./") 


def move_pyc_files(root_dir):
	for root, dirs, files in os.walk (root_dir):
		if "__pycache__" in dirs:
			cache_dir = os.path.join (root, "__pycache__")
			for file in os.listdir (cache_dir):
				if file.endswith (".pyc") and "311" in file:
					# Extract the module name
					module_name = file.split (".")[0] + ".pyc"
					print (f'Moving {module_name}...')
					# Move the .pyc file to the parent directory
					shutil.move(
						os.path.join(cache_dir, file),
						os.path.join(root, module_name)
					)
			# Remove the __pycache__ directory
			shutil.rmtree (cache_dir)
