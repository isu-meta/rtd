Rtd
====

Creates BePress XML from the pdf files of retrospective theses.

Requirements
--------------

* [Python 3.6+](https://www.python.org/)
* [Saxon HE for .Net](http://saxon.sourceforge.net/)
* [bsddb3 bindings for Oracle Berkeley DB](https://www.lfd.uci.edu/~gohlke/pythonlibs/#bsddb3)

Getting Started
----------------

Clone the repository and create a virtual environment.

``` {.sourceCode .console}
C:\Users\you_dir> git clone https://github.com/isu-meta/rtd.git
C:\Users\you_dir> cd rtd
C:\Users\you_dir\rtd> python -m venv "rtd_env"
C:\Users\you_dir\rtd> rtd_env\Scripts\activate
C:\Users\you_dir\rtd> pip install -r requirements.txt
```

Install [Saxon HE for .Net](http://saxon.sourceforge.net/) if it isn't already installed.
Install [bsddb3](https://www.lfd.uci.edu/~gohlke/pythonlibs/#bsddb3). You will need to 
select the appropriate version. If you are using an Iowa State provided Windows computer,
`bsddb3-6.2.6-cp37-cp37m-win32.whl` should be the correct version.

Next, confirm that the paths in [rtd_workflow_wMARCFINDER.py](code_base/rtd_workflow_wMARCFINDER.py) and
[manual_metadata.py](manual_metadata.py) are both correct.

*list of variables*

| Variable Name    | Description                             |
|------------------|-----------------------------------------|
| pdf_reader       | Path to Adobe or similar reader         |
| pdf_path         | Path to retrospective theses            |
| authority_path   | Path to authority files                 |
| marc_record      | Path to marc record                     |
| authority_turtle | Related to authority_path               |
| merge            | Path to the merge.xsl file              |


Finally, run the metadata.py file.

``` {.sourceCode .console}
C:\Users\you_dir\rtd> metadata.py
```

Other Institutions
-------------------

Those working with Non-ISU theses will need to replace [kt_thesis.mrc](MachineReadable/kt_thesis.mrc) with the appropriate marc record. All
of the authorities files will also need modification to reflect the new
institution.

Documentation
--------------

https://mddocs.readthedocs.io/en/latest/theses.html#rtds

