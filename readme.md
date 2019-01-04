Rtd
====

Creates BePress XML from the pdf files of retrospective theses.

Prerequisites
--------------


* saxon he


This code assumes you have saxon available for xslt transformations. We
are using the [Saxon HE for .Net](http://saxon.sourceforge.net/)

Getting Started
----------------

Clone the repository and create an anaconda2 environment.

``` {.sourceCode .console}
$ git clone https://github.com/wryan14/rtd.git
$ cd rtd
$ conda create -n "rtd_env" python=2.7
$ pip install -r requirements.txt
```

Next, confirm that the paths in [rtd_workflow_wMARCFINDER.py](code_base/rtd_workflow_wMARCFINDER.py) and
[manual_metadata.py](manual_metadata.py) are both correct.

*list of variables*

| Variable Name    | Description                             |
|------------------|-----------------------------------------|
| pdf_reader       | | Path to Adobe or similar reader       |
| triplestore      | | Creates directory for rdf triplestore |
| pdf_path         | | Path to retrospective theses          |
| authority_path   | | Path to authority files               |
| marc_record      | | Path to marc record                   |
| authority_turtle | | Related to authority_path             |
| merge            | | Path to the merge.xsl file            |


Finally, run the metadata.bat file.

``` {.sourceCode .console}
$ metadata.bat
```

Other Institutions
-------------------

Those working with Non-ISU theses will need to replace [kt_thesis.mrc](MachineReadable/kt_thesis.mrc) with the appropriate marc record. All
of the authorities files will also need modification to reflect the new
institution.
