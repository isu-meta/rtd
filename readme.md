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

Next, make sure paths in [rtd_workflow_wMARCFINDER.py](code_base/rtd_workflow_wMARCFINDER.py) and
[manual_metadata.py](manual_metadata.py) are both correct. Pay particular attention to the
pdf\_reader variable, as this is the most likely to need updated.

Finally, run the metadata.bat file.

``` {.sourceCode .console}
$ metadata.bat
```

Other Institutions
-------------------

Those working with Non-ISU theses will need to replace
*MachineReadable/kt\_thesis.mrc* with the appropriate marc record. All
of the authorities files will also need modification to reflect the new
institution.
