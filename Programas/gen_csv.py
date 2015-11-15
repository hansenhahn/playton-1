#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import glob

def scandirs(path):
	files = []
	for currentFile in glob.glob( os.path.join(path, '*') ):
		if os.path.isdir(currentFile):
			files += scandirs(currentFile)
		else:
			files.append(currentFile)
	return files

def generate_csv( path = "data" ):
	files = scandirs( path )
	
	fd = open("file_list.csv", "w")
	for f in files:
		path = os.path.split(f)
		fd.write( reduce(lambda x, y: ("%s;%s" % (x, y)), path) )
		fd.write( "\n" ) 
		
	fd.close()
	
if __name__ == "__main__":
	generate_csv()