import shutil
import time
import os

timestr = time.strftime("%Y%m%d")

new_name =  "{}_batch.xml".format(timestr)

try:
    os.remove(new_name)
except:
    pass

os.rename("outfile2.xml", new_name)

output_filename = "{}_RTD".format(timestr)

shutil.move(new_name, "SUCCESSFUL_PDF")
try:
    shutil.make_archive(output_filename, 'zip',"SUCCESSFUL_PDF") 
except:
    os.remove(output_filename)
    shutil.make_archive(output_filename, 'zip', "SUCCESSFUL_PDF")
