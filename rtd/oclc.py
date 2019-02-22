"Functions for working with oclc_list.txt and querying OCLC WorldCat."
from io import StringIO, FileIO
import os
from pathlib import Path
import subprocess
import sys
import urllib.parse

from fuzzywuzzy import fuzz
from lxml import etree
import PyPDF2
import requests

def get_oclc_number(pdf_path):
    """Get the OCLC number for a given thesis.

    Parameters
    ----------
    pdf_path : str
        The path to the PDF.
    Returns
    -------
    str
        The OCLC number for the thesis.
    """
    pdf = PyPDF2.PdfFileReader(FileIO(pdf_path, "rb"))
    
    pdf_metadata = pdf.getDocumentInfo()

    base_url = "https://www.worldcat.org/search?q="
    title_query = f"ti%3A{urllib.parse.quote_plus(pdf_metadata['/Title'].strip())}"
    author_query = f"+au%3A{urllib.parse.quote_plus(pdf_metadata['/Author'].strip())}"
    full_query = "".join([base_url, title_query, author_query])
    oclc_result_details_xpath = "//td[@class='result details']"
    oclc_number_xpath = "//div[@class='oclc_number']"
    oclc_number = None

    r = requests.get(full_query)

    if r.ok:
        tree = etree.parse(StringIO(r.text), etree.HTMLParser())
        request_details = tree.xpath(oclc_result_details_xpath)
        if len(request_details) == 1:
            oclc_number = request_details[0].xpath(oclc_number_xpath)[0].text
        else:
            for detail_section in request_details:
                oclc_title = detail_section.xpath("//div[@class='name']/a/strong[text()]")[0].text
                oclc_author = detail_section.xpath("//div[@class='author']")[0].text
                oclc_type = detail_section.xpath("//div[@class='type']/span[@class='itemType'][text()]")[0].text
                if ";" in oclc_author:
                    oclc_author = oclc_author[:oclc_author.index(";")]
                
                if oclc_author.lower().startswith("by "):
                    oclc_author = oclc_author[3:]
                
                if (90 <= fuzz.ratio(oclc_author.lower(), pdf_metadata["/Author"].lower()) and
                    90 <= fuzz.ratio(oclc_title.lower(), pdf_metadata["/Title"].lower()) and
                    95 <= fuzz.ratio(oclc_type.lower(), "thesis/dissertation")):

                    oclc_number = detail_section.xpath(oclc_number_xpath)[0].text
                    break

    return oclc_number


def make_oclc_list(input_path, output_path):
    """Update oclc_list.txt with the OCLC number for
    each thesis PDF in input_path.

    Parameters
    ----------
    input_path : str
        The path to the directory containing PDFs to be processed.
    output_path : str
        The path to the file to be written.
    Returns
    -------
    None
    """

    oclc_list_out ={}
    #with open(oclc_list_path, "r", encoding="utf-8") as fh:
    #    pdfs = [pdf.strip() for pdf in list(fh)]

    pdfs = os.listdir(input_path)
    
    for pdf in pdfs:
        oclc_num = get_oclc_number(Path(input_path, pdf))
        oclc_list_out[pdf] = oclc_num
    
    with open(output_path, "w", encoding="utf-8") as fh:
        for k, v in oclc_list_out.items():
            if v is not None:
                fh.write(f"{k}$http://www.worldcat.org/oclc/{v}.ttl\n")
            else:
                fh.write(f"{k}$\n")


def open_oclc_list(oclc_file):
    if os.name == "nt":
        subprocess.run(oclc_file)
    if os.name == "posix":
        if sys.platform.startswith("darwin"):
            subprocess.run(["open", oclc_file])
        else:
            subprocess.run(["xdg-open", oclc_file])