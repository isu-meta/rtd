import os
from pathlib import Path
import shutil
import subprocess
import time

from rtd.reset import delete, move
from rtd.rtd_workflow_wMARCFINDER import rtd_metadata 
from rtd.check_names import check
from rtd.oclc import make_oclc_list, open_oclc_list

def delete_old_files(my_path):
    # Delete all "*batch.xml" files from the current working directory
    # directory on down.
    for dir_path, __, file_names in os.walk(my_path):
        for file_name in file_names:
            if file_name.endswith("batch.xml"):
                os.remove(os.path.join(dir_path, file_name))
    
    # Delete all zip files in the current working directory.
    os.path.join(dir_path, file_name)
    for f in os.listdir(my_path):
        if f.endswith(".zip"):
            os.remove(f)


def reset(xml_file):
    # Previously handled in reset.py.
    dest = "RTD_PDF"
    src = "SUCCESSFUL_PDF/*pdf"

    move(src, dest)
    delete()

    try:
        os.remove(os.path.join(my_path, xml_file))
    except Exception:
        pass


def create_metadata():
    rtd_metadata()


def check_metadata(xml_file):
    try:
        check(xml_file)
    except Exception:
        pass


def commit(my_path):
    # Previously handled in commit.py
    timestr = time.strftime("%Y%m%d")

    new_name =  "{}_batch.xml".format(timestr)

    try:
        os.remove(new_name)
    except:
        pass

    os.rename(os.path.join(my_path, "outfile2.xml"), os.path.join(my_path, new_name))

    output_filename = "{}_RTD".format(timestr)

    shutil.move(new_name, "SUCCESSFUL_PDF")
    try:
        shutil.make_archive(output_filename, "zip","SUCCESSFUL_PDF") 
    except:
        os.remove(output_filename)
        shutil.make_archive(output_filename, "zip", "SUCCESSFUL_PDF")


if __name__ == "__main__":
    my_path = "C:\\Users\\wteal\\Projects\\rtd"
    input_pdf_dir = "RTD_PDF"
    xml_outfile = "outfile.xml"
    xml_outfile2 = "outfile2.xml"
    oclc_file = Path(my_path, "oclc_list.txt")

    delete_old_files(my_path)
    reset(xml_outfile)
    create_metadata()
    check_metadata(xml_outfile)
    make_oclc_list(Path(my_path, input_pdf_dir), oclc_file)

    #open_oclc_list(oclc_file) # Need to debug this one.
    #Remove the print below once the above function is fixed.
    print("Open oclc_list.txt and edit it according to https://mddocs.readthedocs.io/en/latest/theses.html#rtds")

    input("Press Enter to continue. To exit, press Ctl+C.")

    subprocess.run(["python", os.path.join(my_path, "manual_metadata.py")])

    input("Press Enter to continue. To exit, press Ctl+C.")

    reset(xml_outfile)
    check_metadata(xml_outfile2)
    print("""RTD_PDF should now be empty, if it is not please run the
script again, or talk to a librarian for further assistance.
If everything looks okay please hit enter.""")

    input("Press Enter to continue. To exit, press Ctl+C.")

    commit(my_path)
    for f in os.listdir(my_path):
        if f.endswith(".zip"):
            shutil.move(f, "..")
