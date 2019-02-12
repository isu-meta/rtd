import os
import shutil
import subprocess
import sys
import time

from rtd.reset import delete, move
from rtd.rtd_workflow_wMARCFINDER import rtd_metadata 
from rtd.check_names import check

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


def make_oclc_list(outfile):
    rtd_dir = os.path.join(my_path, "RTD_PDF")

    with open(outfile, "w", encoding="utf8") as fh:
        for rtd_pdf in os.listdir(rtd_dir):
            fh.write(f"{rtd_pdf}\n")


def open_oclc_list(oclc_file):
    if os.name == "nt":
        subprocess.run(oclc_file)
    if os.name == "posix":
        if sys.platform.startswith("darwin"):
            subprocess.run(["open", oclc_file])
        else:
            subprocess.run(["xdg-open", oclc_file])


def commit():
    # Previously handled in commit.py
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


if __name__ == "__main__":
    my_path = "C:\\Users\\wteal\\Projects\\rtd"
    xml_outfile = "outfile.xml"
    xml_outfile2 = "outfile2.xml"
    oclc_file = os.path.join(my_path, "oclc_list.txt")

    delete_old_files(my_path)
    reset(xml_outfile)
    create_metadata()
    check_metadata(xml_outfile)
    make_oclc_list(oclc_file)
    #open_oclc_list(oclc_file)

    input("Press Enter to continue...")

    subprocess.run(["python", os.path.join(my_path, "manual_metadata.py")])

    input("Press Enter to continue...")

    reset(xml_outfile)
    check_metadata(xml_outfile2)
    print("""RTD_PDF should now be empty, if it is not please run the
script again, or talk to a librarian for further assistance.
If everything looks okay please hit enter.""")

    input("Press Enter to continue...")

    commit()
    for f in os.listdir(my_path):
        if f.endswith(".zip"):
            shutil.move(f, "..")
