#!/usr/bin/python
import shutil
import glob
import os

def delete():
	try:
		shutil.rmtree('RDF_TripleStore')
	except:
		pass
	try:
		shutil.rmtree('Authorities/XMLFiles')	
	except:
		pass

def move(src, dest):
	for item in glob.glob(src):
		shutil.move(item, dest)
		
if __name__=="__main__":
	dest = "RTD_PDF"
	src = "SUCCESSFUL_PDF/*.pdf"
	move(dest=dest, src=src)
	delete()
	try:
		os.remove(os.getcwd()+"\\outfile.xml")
	except Exception:
		pass
