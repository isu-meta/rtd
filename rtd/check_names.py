#!/usr/bin/python
# Searches original PDF for incomplete fields
from lxml import etree
import shutil
import os

def check(file):
    root = etree.parse(file)
    pdf_field = root.xpath('//fulltext-url')
    for item in pdf_field:
        item_y = item.text.split('DR/')[1]
        shutil.move('./RTD_PDF/'+item_y, 'SUCCESSFUL_PDF')

if __name__=="__main__":
    try:
        check(file='outfile.xml')
    except Exception:
        pass
