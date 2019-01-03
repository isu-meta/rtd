@echo off
call activate test_envs
set mypath=%cd%
cd %mypath%
del /S *batch.xml
del *.zip
python reset.py && python create_metadata.py
python check_names.py
dir RTD_PDF /b /a-d > oclc_list.txt
oclc_list.txt
pause
python manual_metadata.py
pause
python reset.py
python check_names2.py
echo "RTD_PDF should now be empty, if it is not please run the script again, or talk to a librarian for further assistance"
echo "If everything looks okay please hit enter"
pause
python commit.py 
MOVE *.zip ..
