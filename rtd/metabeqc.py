# -*- encoding: utf-8 -*-
import csv
import datetime
import glob
import os
import os.path
import re
import shutil
import subprocess
import unicodedata
import zipfile
import time
from io import StringIO

import lxml.etree as ET
import PyPDF2
from dateutil import parser
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from lxml import etree
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from .regreplace import RegexpReplacer

# Code for RegexpReplacer found in NLTK Cookbook - used for replacing "one-off" majors
RegexpReplacer= RegexpReplacer()

class BePress(object):
    """
    -----Creates object from transformed ProQuest xml data-----
     1. xmlname, xmltitle, xmlauthor: pulls from xml
     2. getname, getitle, getauthor: returns current
     3. chtitle / ch[]name: edit object's title or name
     4. commit methods: any method using described by 'commit' will write object field to xml
     5. xmlfield: allows you to find values listed under 'fields'
     6. Use with Caution!: set_and_commit: these will create a new xml: field, so use
        xmlfield feature, if you are simply looking to edit a major field. Using
        this more than once will duplicate fileds
    """

    def __init__(self, file):
        self.file = file

    def xmlname(self):
        self.name = os.path.basename(self.file)
        return self.name

    def xmltitle(self):
        tree = etree.parse(self.file)
        root = tree.getroot()
        docTitle = root.xpath('document/title')
        self.title = docTitle[0].text
        return (lazy_encode(self.title))

    def xmlauthor(self):
        tree = etree.parse(self.file)
        root = tree.getroot()
        lname = root.xpath('document/authors/author/lname')
        fname = root.xpath('document/authors/author/fname')
        mname = root.xpath('document/authors/author/mname')
        self.lname = lname[0].text
        self.mname = mname[0].text
        self.fname = fname[0].text
        self.author = " ".join([_f for _f in [self.fname, self.mname, self.lname] if _f])
        return (self.author)

    # ---------------------------------
    def getname(self):
        return self.name

    def gettitle(self):
        return self.title

    def getauthor(self):
        self.author = " ".join([_f for _f in [self.fname, self.mname, self.lname] if _f])
        return (self.author)

    # --------------------------------
    def chtitle(self, newtitle):
        self.title = newtitle
        return newtitle

    def chlname(self, newlname):
        self.lname = newlname
        return newlname

    def chmname(self, newmname):
        self.mname = newmname
        return newmname

    def chfname(self, newfname):
        self.fname = newfname
        return newfname

    # -----------------------------------
    def commitauthor(self):
        tree = etree.parse(self.file)
        elem = tree.findall('.//author/fname')[0]
        elem.text = str(self.fname)
        if self.mname == None or self.mname == 'None' or self.mname == " " or self.mname == "":
            pass
        else:
            elem2 = tree.findall('.//author/mname')[0]
            elem2.text = str(self.mname)
        elem3 = tree.findall('.//author/lname')[0]
        elem3.text = str(self.lname)
        tree = (etree.ElementTree(tree.getroot()))
        tree.write(self.file, xml_declaration=True, encoding='utf-8', method='xml')

    def committitle(self):
        tree = etree.parse(self.file)
        elem = tree.findall('.//title')[0]
        elem.text = str(self.title)
        tree = (etree.ElementTree(tree.getroot()))
        tree.write(self.file, xml_declaration=True, encoding='utf-8', method='xml')

    # --------------------------------------------------------------------------------------
    def xmlfield(self, item):
        self.fieldlocation = item
        tree = etree.parse(self.file)
        value = tree.xpath("//field[@name=" + "'" + item + "']/value/text()")
        '''try:
            self.field = field[0]
        except IndexError:
            self.field = 'None'
        try:
            self.field = field[0]
        except IndexError:
            self.field = 'None'
        try:
            self.field = value[1]
        except IndexError:
            self.field = 'None'
        return self.field'''
        return value[0]

    def chfield(self, text):
        self.field = text
        return self.field

    def currentfield(self):
        return self.field

    # Before using the commitfield function, make sure self.field contains the desired value
    def commitfield(self):
        tree = etree.parse(self.file)
        for item in tree.xpath("//field[@name=" + "'" + str(self.fieldlocation) + "']/value"):
            item.text = self.field
            break
        tree = (etree.ElementTree(tree.getroot()))
        tree.write(self.file, xml_declaration=True, encoding='utf-8', method='xml')

    # Running this set_and_commit functions will keep adding new fields,
    # if you are trying to change the major use commitmajor instead
    def set_and_commitmajor(self, text):
        self.major = text
        tree = etree.parse(self.file)
        root = tree.getroot()
        for element in root.iter('fields'):
            root2 = element
            child = etree.SubElement(root2, "field")
            child2 = etree.SubElement(child, "value")
            child.set("name", 'major')
            child.set("type", "string")
            child2.text = str(self.major)
            tree = (etree.ElementTree(tree.getroot()))
            indent(element, 3)
            tree.write(self.file, xml_declaration=True, encoding='utf-8', method='xml')

    # I'm not a fan of creating a separate function to update documents with two majors.
    # I will try to find a better solution in the future
    def set_and_commit2majors(self, text1, text2):
        self.major1 = text1
        self.major2 = text2
        tree = etree.parse(self.file)
        root = tree.getroot()
        for element in root.iter('fields'):
            root2 = element
            child = etree.SubElement(root2, "field")
            child2 = etree.SubElement(child, "value")
            child3 = etree.SubElement(child, "value")
            child.set("name", 'major')
            child.set("type", "string")
            child2.text = str(self.major1)
            child3.text = str(self.major2)
            tree = (etree.ElementTree(tree.getroot()))
            indent(element, 3)
            tree.write(self.file, xml_declaration=True, encoding='utf-8', method='xml')


    # Once Names have been corrected, we need to update the Rights_Holder
    def updaterights_holder(self):
        tree = etree.parse(self.file)
        value = tree.xpath("//field[@name='rights_holder']/value")
        value[0].text = str(self.author)
        tree = (etree.ElementTree(tree.getroot()))
        tree.write(self.file, xml_declaration=True, encoding='utf-8', method='xml')


# ----------------------------------------------------------------
# BePressed used functions
# ----------------------------------------------------------------
# If you encounter a new encoding error, add the error here
# Replacing Error with Desired Value
def lazy_encode(text):
    try:
        regreplace = re.sub(r'\u201c', '"', text)
        regreplace2 = re.sub(r'\u201d', '"', regreplace)
        regreplace3 = re.sub(r'\u2019', "'", regreplace2)
        regreplace4 = re.sub(r'\u2018', "'", regreplace3)
        regreplace5 = re.sub(r'\u2212', "-", regreplace4)
        regreplace6 = re.sub(r'\u03b2', 'b', regreplace5)
        regreplace7 = re.sub(r'\u2013', '-', regreplace6)
        regreplace8 = re.sub(r'\u03b3', '(&#947)', regreplace7)
        regreplace9 = re.sub(r'\u0301', "'", regreplace8)
        regreplace10 = re.sub(r'\u0306', "g", regreplace9)
        regreplace11 = re.sub(r'\u0131', 'i', regreplace10)
        ret1999 = regreplace11.encode('utf-8')
        return ret1999
    except UnicodeEncodeError:
        return 'ENCODING ERROR'
    except UnicodeDecodeError:
        return 'ENCODING ERROR'


# Used for formatting when commiting majors
# Stack Overflow https://stackoverflow.com/questions/749796/pretty-printing-xml-in-python
def indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


# --------------------------------

class PDFPress(object):
    """
    -----Creates Object from PDF title page-----
     1. Recommended: run genfile() and genlines() to format pdf before using other methods
     2. validatekeyword: searches a combination of pdf-lines for fuzzy match, then returns highest
        valued match
     3. findmajor: regex approach to finding major. We use regular expression, since there is no xml
        field to validate against
     4. reconcilemajor: validates extracted majors against authority file 'ListofMajors.csv'
        inconsistencies are flagged for user-review
    """

    def __init__(self, file, pdfreader):
        self.reader = pdfreader
        self.path = file
        self.name = os.path.basename(file)
        self.file = convert(file, pages=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.pdfauthor = 'None'

    def getname(self):
        return self.name

    def genfile(self):
        self.gfile = str(self.file).replace('\t', '').replace('\n\n', '\n').strip()
        self.gfile = StringIO(self.gfile)
        return self.gfile

    def genlines(self):
        self.listfile = str(self.file).replace('\t', '').replace('\n\n', '\n').strip()
        self.listfile = StringIO(str(self.listfile))
        lower_lines = []
        standard_lines = []
        for line in self.listfile:
            cleanline = (line.replace('\t', ' ').strip())
            lower_lines.append(cleanline)
            standard_lines.append(cleanline)
        self.standard_lines = standard_lines
        self.lower_lines = lower_lines

    # There is probably a more efficient way, but this seems to work for the time being

    def validatekeyword(self, keyword, title=False, author=False):
        '''
            This function obliterates DRY principles of coding. It emerged over a 
            long debugging process, and should be refactored .
        '''
        try:
            # write some preliminary lines for little Endian encoded titles
            la = " ".join([self.lower_lines[1], self.lower_lines[0]])
            la2 = " ".join([self.lower_lines[2], self.lower_lines[1]])
            la3 = " ".join([self.lower_lines[3], self.lower_lines[2]])
            la4 = " ".join([self.lower_lines[4], self.lower_lines[3]])
            A1 = " ".join([self.lower_lines[0], self.lower_lines[1]])
            A2 = " ".join([self.lower_lines[0], self.lower_lines[1], self.lower_lines[2]])
            A3 = " ".join([self.lower_lines[1], self.lower_lines[2]])
            A4 = " ".join([self.lower_lines[2], self.lower_lines[3]])
            A5 = " ".join([self.lower_lines[1], self.lower_lines[2], self.lower_lines[3]])
            a5a = " ".join([self.lower_lines[0], self.lower_lines[3]])
            A6 = " ".join([self.lower_lines[3], self.lower_lines[4]])
            A7 = " ".join([self.lower_lines[0], self.lower_lines[2]])
            A8 = " ".join([self.lower_lines[1], self.lower_lines[3]])
            A9 = " ".join([self.lower_lines[4], self.lower_lines[5]])
            A10 = " ".join([self.lower_lines[5], self.lower_lines[6]])
            A11 = " ".join([self.lower_lines[6], self.lower_lines[7]])
            A12 = " ".join([self.lower_lines[7], self.lower_lines[8]])
            A13 = " ".join([self.lower_lines[8], self.lower_lines[9]])
            A14 = " ".join([self.lower_lines[9], self.lower_lines[10]])
            A15 = " ".join([self.lower_lines[10], self.lower_lines[11]])
            A16 = " ".join([self.lower_lines[11], self.lower_lines[12]])
            A17 = " ".join([self.lower_lines[12], self.lower_lines[13]])
            A18 = " ".join([self.lower_lines[13], self.lower_lines[14]])
            A19 = " ".join([self.lower_lines[14], self.lower_lines[15]])
            A20 = " ".join([self.lower_lines[15], self.lower_lines[16]])
            A21 = " ".join([self.lower_lines[16], self.lower_lines[17]])
            A22 = " ".join([self.lower_lines[17], self.lower_lines[18]])
            A23 = " ".join([self.lower_lines[18], self.lower_lines[19]])
            A24 = " ".join([self.lower_lines[19], self.lower_lines[20]])
            A25 = " ".join([self.lower_lines[20], self.lower_lines[21]])
            A26 = " ".join([self.lower_lines[21], self.lower_lines[22]])
            A27 = " ".join([self.lower_lines[22], self.lower_lines[23]])
            A28 = " ".join([self.lower_lines[23], self.lower_lines[24]])
            A29 = " ".join([self.lower_lines[24], self.lower_lines[25]])
            A30 = " ".join([self.lower_lines[25], self.lower_lines[26]])
            triA9 = " ".join([self.lower_lines[4], self.lower_lines[5], self.lower_lines[6]])
            triA10 = " ".join([self.lower_lines[5], self.lower_lines[6], self.lower_lines[7]])
            triA11 = " ".join([self.lower_lines[6], self.lower_lines[7], self.lower_lines[8]])
            triA12 = " ".join([self.lower_lines[7], self.lower_lines[8], self.lower_lines[9]])
            triA13 = " ".join([self.lower_lines[8], self.lower_lines[9], self.lower_lines[10]])
            triA14 = " ".join([self.lower_lines[9], self.lower_lines[10], self.lower_lines[11]])
            triA15 = " ".join([self.lower_lines[10], self.lower_lines[11], self.lower_lines[12]])
            triA16 = " ".join([self.lower_lines[11], self.lower_lines[12], self.lower_lines[13]])
            triA17 = " ".join([self.lower_lines[12], self.lower_lines[13], self.lower_lines[14]])
            triA18 = " ".join([self.lower_lines[13], self.lower_lines[14], self.lower_lines[15]])
            triA19 = " ".join([self.lower_lines[14], self.lower_lines[15], self.lower_lines[16]])
            triA20 = " ".join([self.lower_lines[15], self.lower_lines[16], self.lower_lines[17]])
            triA21 = " ".join([self.lower_lines[16], self.lower_lines[17], self.lower_lines[18]])
            triA22 = " ".join([self.lower_lines[17], self.lower_lines[18], self.lower_lines[19]])
            triA23 = " ".join([self.lower_lines[18], self.lower_lines[19], self.lower_lines[20]])
            triA24 = " ".join([self.lower_lines[19], self.lower_lines[20], self.lower_lines[21]])
            triA25 = " ".join([self.lower_lines[20], self.lower_lines[21], self.lower_lines[22]])
            triA26 = " ".join([self.lower_lines[21], self.lower_lines[22], self.lower_lines[23]])
            triA27 = " ".join([self.lower_lines[22], self.lower_lines[23], self.lower_lines[24]])
            triA28 = " ".join([self.lower_lines[23], self.lower_lines[24], self.lower_lines[25]])
            triA29 = " ".join([self.lower_lines[24], self.lower_lines[25], self.lower_lines[26]])
            triA30 = " ".join([self.lower_lines[25], self.lower_lines[26], self.lower_lines[27]])

            B1 = (self.lower_lines[0], fuzz.ratio(keyword, self.lower_lines[0]))
            B2 = (self.lower_lines[1]), fuzz.ratio(keyword, self.lower_lines[1])
            B3 = (self.lower_lines[2], fuzz.ratio(keyword, self.lower_lines[2]))
            B4 = (self.lower_lines[3], fuzz.ratio(keyword, self.lower_lines[3]))
            B5 = (A1, fuzz.ratio(keyword, A1))
            B6 = (A2, fuzz.ratio(keyword, A2))
            B7 = (A3, fuzz.ratio(keyword, A3))
            B8 = (A4, fuzz.ratio(keyword, A4))
            B9 = (A5, fuzz.ratio(keyword, A5))
            B10 = (A6, fuzz.ratio(keyword, A6))
            B11 = (A7, fuzz.ratio(keyword, A7))
            B12 = (A8, fuzz.ratio(keyword, A8))
            B13 = (A9, fuzz.ratio(keyword, A9))
            B14 = (A10, fuzz.ratio(keyword, A10))
            B15 = (A11, fuzz.ratio(keyword, A11))
            B16 = (A12, fuzz.ratio(keyword, A12))
            B17 = (A13, fuzz.ratio(keyword, A13))
            B18 = (A14, fuzz.ratio(keyword, A14))
            B19 = (A15, fuzz.ratio(keyword, A15))
            B20 = (A16, fuzz.ratio(keyword, A16))
            B21 = (A17, fuzz.ratio(keyword, A17))
            B22 = (A18, fuzz.ratio(keyword, A18))
            B23 = (A19, fuzz.ratio(keyword, A19))
            B24 = (A20, fuzz.ratio(keyword, A20))
            B25 = (A21, fuzz.ratio(keyword, A21))
            B26 = (A22, fuzz.ratio(keyword, A22))
            B27 = (A23, fuzz.ratio(keyword, A23))
            B28 = (A24, fuzz.ratio(keyword, A24))
            B29 = (A25, fuzz.ratio(keyword, A25))
            B30 = (A26, fuzz.ratio(keyword, A26))
            B31 = (A27, fuzz.ratio(keyword, A27))
            B32 = (A28, fuzz.ratio(keyword, A28))
            B33 = (A29, fuzz.ratio(keyword, A29))
            B34 = (A30, fuzz.ratio(keyword, A30))
            B35 = (triA9, fuzz.ratio(keyword, triA9))
            B36 = (triA10, fuzz.ratio(keyword, triA10))
            B37 = (triA11, fuzz.ratio(keyword, triA11))
            B38 = (triA12, fuzz.ratio(keyword, triA12))
            B39 = (triA13, fuzz.ratio(keyword, triA13))
            B40 = (triA14, fuzz.ratio(keyword, triA14))
            B41 = (triA15, fuzz.ratio(keyword, triA15))
            B42 = (triA16, fuzz.ratio(keyword, triA16))
            B43 = (triA17, fuzz.ratio(keyword, triA17))
            B44 = (triA18, fuzz.ratio(keyword, triA18))
            B45 = (triA19, fuzz.ratio(keyword, triA19))
            B46 = (triA20, fuzz.ratio(keyword, triA20))
            B47 = (triA21, fuzz.ratio(keyword, triA21))
            B48 = (triA22, fuzz.ratio(keyword, triA22))
            B49 = (triA23, fuzz.ratio(keyword, triA23))
            B50 = (triA24, fuzz.ratio(keyword, triA24))
            B51 = (triA25, fuzz.ratio(keyword, triA25))
            B52 = (triA26, fuzz.ratio(keyword, triA26))
            B53 = (triA27, fuzz.ratio(keyword, triA27))
            B54 = (triA28, fuzz.ratio(keyword, triA28))
            B55 = (triA29, fuzz.ratio(keyword, triA29))
            B56 = (triA30, fuzz.ratio(keyword, triA30))

            b5a = (a5a, fuzz.ratio(keyword, a5a))
            b6a = (la, fuzz.ratio(keyword, la))
            b7a = (la2, fuzz.ratio(keyword, la2))
            b8a = (la3, fuzz.ratio(keyword, la3))
            b9a = (la4, fuzz.ratio(keyword, la4))

            AB1 = (self.lower_lines[4], fuzz.ratio(keyword, self.lower_lines[4]))
            AB2 = (self.lower_lines[5], fuzz.ratio(keyword, self.lower_lines[5]))
            AB3 = (self.lower_lines[6], fuzz.ratio(keyword, self.lower_lines[6]))
            AB4 = (self.lower_lines[7], fuzz.ratio(keyword, self.lower_lines[7]))
            AB5 = (self.lower_lines[8], fuzz.ratio(keyword, self.lower_lines[8]))
            AB6 = (self.lower_lines[9], fuzz.ratio(keyword, self.lower_lines[9]))
            AB7 = (self.lower_lines[10], fuzz.ratio(keyword, self.lower_lines[10]))
            AC1 = (self.lower_lines[11], fuzz.ratio(keyword, self.lower_lines[11]))
            AC2 = (self.lower_lines[12], fuzz.ratio(keyword, self.lower_lines[12]))
            AC3 = (self.lower_lines[13], fuzz.ratio(keyword, self.lower_lines[13]))
            AC4 = (self.lower_lines[14], fuzz.ratio(keyword, self.lower_lines[14]))
            AC5 = (self.lower_lines[15], fuzz.ratio(keyword, self.lower_lines[15]))
            AC6 = (self.lower_lines[11], fuzz.ratio(keyword, self.lower_lines[11]))
            AC7 = (self.lower_lines[12], fuzz.ratio(keyword, self.lower_lines[12]))
            AC8 = (self.lower_lines[13], fuzz.ratio(keyword, self.lower_lines[13]))
            AC9 = (self.lower_lines[14], fuzz.ratio(keyword, self.lower_lines[14]))
            AC10 = (self.lower_lines[15], fuzz.ratio(keyword, self.lower_lines[15]))
            AC11 = (self.lower_lines[16], fuzz.ratio(keyword, self.lower_lines[16]))
            AC12 = (self.lower_lines[17], fuzz.ratio(keyword, self.lower_lines[17]))
            AC13 = (self.lower_lines[18], fuzz.ratio(keyword, self.lower_lines[18]))
            AC14 = (self.lower_lines[19], fuzz.ratio(keyword, self.lower_lines[19]))
            AC15 = (self.lower_lines[20], fuzz.ratio(keyword, self.lower_lines[20]))
            AC16 = (self.lower_lines[21], fuzz.ratio(keyword, self.lower_lines[21]))
            AC17 = (self.lower_lines[22], fuzz.ratio(keyword, self.lower_lines[22]))
            AC18 = (self.lower_lines[23], fuzz.ratio(keyword, self.lower_lines[23]))
            AC19 = (self.lower_lines[24], fuzz.ratio(keyword, self.lower_lines[24]))
            AC20 = (self.lower_lines[25], fuzz.ratio(keyword, self.lower_lines[25]))
            AB8 = (A9, fuzz.ratio(keyword, A9))
            AB9 = (A10, fuzz.ratio(keyword, A10))
            AB10 = (A11, fuzz.ratio(keyword, A11))
            AB11 = (A12, fuzz.ratio(keyword, A12))
            AB12 = (A13, fuzz.ratio(keyword, A13))
            AB13 = (A14, fuzz.ratio(keyword, A14))

            collected_ratios = [B1, B2, B3, B4, B5, B6, B7, B8, B9, B10, B11, B12, AB1, AB2, AB3, AB4, AB5, AB6, AB7,
                                AB8, AB9, AB10, AB11, AB12, AB13, AC1, AC2, AC3, AC4, AC5, AC6, AC7, AC8, AC9, AC10,
                                AC11, AC12, AC13, AC14, AC15, AC16, AC17, AC18, AC19, AC20, B13, B14, B15, B16, B17,
                                B18, B19, B20, B21, B22, B23, B24, B25, B26, B27, B28, B29, B30, B31, B32, B33, B34,
                                B35,
                                B36, B37, B38, B39, B40, B41, B42, B43, B44, B45, B46, B47, B48, B49, B50, B51, B52,
                                B53, B54, B55, B56, b5a, b6a, b7a, b8a, b9a]
            ret = (max(collected_ratios, key=lambda item: item[1]))
            ret2 = unicodedata.normalize("NFKD", ret[0].decode('utf-8'))
            ret3 = lazy_encode(ret2)
            if title == True:
                self.pdftitle = ret3.strip()
                return self.pdftitle
            elif author == True:
                self.pdfauthor = ret3.strip()
                return self.pdfauthor
            else:
                return ret3.strip()
        except (UnicodeDecodeError):
            return (("Error", 0))

    def findmajor(self):
        '''
            This function makes use of a fairly effective regular expression 
            for finding content that proceeds Major:, majors:, and Co-Majors: .
            Generally speaking, a failure to find the major is due to poor OCR. 
        '''
        self.major = 'None'
        for line in self.gfile:
            z = re.search(r'(?<=Major:).*$|(?<=majors:).*$|(?<=Co-Majors:).*$', line)
            if z != None:
                major = z.group()
                self.major = (major.strip())
                self.major = (re.sub(r'\(.*\)', '', str(self.major)))
                corrections = RegexpReplacer.replace(self.major)
                self.major = str(corrections)

        return self.major

    def reconcilemajor(self, authoritylist):
        '''
            If the found major is not present in the authority list, 
            this function kicks it to manual review. 
        '''
        complete = False
        with open(authoritylist) as f:
            master_list = [tuple(line) for line in csv.reader(f)]
        #self.major = lazy_encode(str(self.major))
        best_match = process.extract(self.major, master_list, limit=1)
        # See if there are two valid majors
        try:
            splitmajor = str(self.major).split(';')
            self.firstmajor = splitmajor[0].strip()
            self.secondmajor = splitmajor[1].strip()
        except IndexError:
            pass
        except ValueError:
            pass
        except UnicodeDecodeError:
            pass
        except UnicodeEncodeError:
            pass
        try:
            best_match2 = process.extract(self.firstmajor, master_list, limit=1)
            best_match3 = process.extract(self.secondmajor, master_list, limit=1)
            for key, value in best_match2:
                self.value1 = value
            for key, value in best_match3:
                self.value2 = value
            if int(self.value1) + int(self.value2) == 200:
                return self.firstmajor +"; "+ self.secondmajor
            else:
                pass
        except ValueError:
            pass
        except IndexError:
            pass
        except AttributeError:
            pass
        suggested_matches = process.extract(self.major, master_list, limit=3)
        for key, value in best_match:
            if value == 100:
                self.major = str(*key)
                return self.major
            else:
                while complete == False:
                    print('----------------------------------------------------------------------------------------------')
                    print('--Unauthorized Major-------------------------------------------------------------------------')
                    print('-------------------------------------------------------------------------------')
                    FNULL = open(os.devnull, 'w')
                    self.doc = subprocess.Popen("%s %s" % (self.reader, self.path), stdout=FNULL,
                                                stderr=subprocess.STDOUT)
                    print("Unauthroized Result= " + self.major)
                    try:
                        print("Match[1]: " + str(suggested_matches[0]))
                        print("Match[2]: " + str(suggested_matches[1]))
                        print("Match[3]: " + str(suggested_matches[2]))
                    except TypeError:
                        print(TypeError)
                        print(key)
                    review = input("Is there more than one major? [y|n]: ")
                    if review == 'y' or review == 'Y':
                        major1 = input('First Major: ')
                        if major1 == '1':
                            self.major1 = str(*key)
                        elif major1 == '2':
                            self.major1 = str(*suggested_matches[1][0])
                        elif major1 == '3':
                            self.major1 = str(*suggested_matches[2][0])
                        else:
                            self.major1 = major1
                        major2 = input('Second Major: ')
                        if major2 == '1':
                            self.major2 = str(*key)
                        elif major2 == '2':
                            self.major2 = str(*suggested_matches[1][0])
                        elif major2 == '3':
                            self.major2 = str(*suggested_matches[2][0])
                        else:
                            self.major2 = major2
                        print((self.major1))
                        print((self.major2))
                        confirm = input('CORRECT? [y|n]')
                        if confirm == 'y' or confirm == 'Y':
                            confirm = True
                            self.doc.kill()
                            time.sleep(1)
                            return self.major1+"; "+ self.major2
                        else:
                            continue
                    else:
                        major = input("Enter major: ")
                        if major == '1':
                            self.major = str(*key)
                        elif major == '2':
                            self.major = str(*suggested_matches[1][0])
                        elif major == '3':
                            self.major = str(*suggested_matches[2][0])
                        else:
                            self.major = major
                        print(self.major)
                        confirm = input('CORRECT? [y|n]')
                        if confirm == 'y' or confirm == 'Y':
                            self.doc.kill()
                            time.sleep(1)
                            return self.major
                        else:
                            continue


# ----------------------------------------------------------------------------------------
# PDF Press Function
# ----------------------------------------------------------------------------------------
# Function used PDF Minder to extract text from PDF
# http://stanford.edu/~mgorkove/cgi-bin/rpython_tutorials/Using%20Python%20to%20Convert%20PDFs%20to%20Text%20Files.php
def convert(fname, pages=None):
    '''
        Function uses PDF Miner to extract text from PDF
        http://stanford.edu/~mgorkove/cgi-bin/rpython_tutorials/Using%20Python%20to%20Convert%20PDFs%20to%20Text%20Files.php
    '''
    if not pages:
        pagenums = set()
    else:
        pagenums = set(pages)

    output = StringIO()
    manager = PDFResourceManager()
    converter = TextConverter(manager, output, laparams=LAParams())
    interpreter = PDFPageInterpreter(manager, converter)

    with open(fname, "rb") as infile:
        for page in PDFPage.get_pages(infile, pagenums):
            interpreter.process_page(page)

    converter.close()
    text = output.getvalue()
    return text


# ----------------------------------------------------------------------------------------------
class SortDocuments(object):
    """
    Designed to separate .pdf and .xml files into seperate folders
    Two Methods:
    1.makefolders: if folders XML and PDF do not exist, create folders
    2.sort: sorts and moves files to corresponding folder
    """

    def __init__(self, path):
        self.path = path

    def makefolders(self):
        path = ('XML')
        if not os.path.exists(path):
            os.makedirs(path)
        path2 = ('PDF')
        if not os.path.exists(path2):
            os.makedirs(path2)
        path3 = ('MultiMedia')
        if not os.path.exists(path3):
            os.makedirs(path3)
        path4 = ('Embargo')
        if not os.path.exists(path4):
            os.makedirs(path4)
        path5 = 'Embargo\\XML'
        if not os.path.exists(path5):
            os.makedirs(path5)
        path6 = 'Embargo\\PDF'
        if not os.path.exists(path6):
            os.makedirs(path6)

    def sort(self):
        self.xmlpath = str(self.path + '\XML')
        self.pdfpath = str(self.path + '\PDF')
        self.multipath = str(self.path + '\MultiMedia')
        self.embargo = str(self.path + '\Embargo')
        for file in glob.glob(str(self.path) + "\*.pdf"):
            shutil.move(file, self.pdfpath)
            self.pdfpath = str(self.path + '\PDF')
        for file in glob.glob(str(self.path) + "\*.xml"):
            shutil.move(file, self.xmlpath)
        for file in glob.glob(str(self.path) + "\\*"):
            if file != self.pdfpath \
                    and file != self.xmlpath \
                    and file != self.multipath \
                    and file != self.embargo:
                shutil.move(file, self.multipath)

    def findembargo(self, file, embargo, pdffile):
        try:
            today = datetime.date.today().strftime('%Y-%m-%d')
            parsed1 = parser.parse(embargo)
            parsed2 = parser.parse(today)
            if parsed1 > parsed2:
                try:
                    shutil.move(self.path + "\\PDF\\" + pdffile, self.path + "\\Embargo")
                except shutil.Error:
                    print ("ERROR moving to embargo folder:")
                    print(file)
                    pass
                except WindowsError:
                    print("ERROR moving to embargo folder:")
                    print(file)
                    pass
                try:
                    shutil.move(file, self.path + "\\Embargo")
                except shutil.Error:
                    print ("ERROR moving to embargo folder:")
                    print(file)
                    pass
                except WindowsError:
                    print("Error moving to embargo folder:")
                    print(file)
            else:
                return "None"
        except ValueError:
            print ("ERROR moving to embargo folder:")
            print(file)
            pass


# ----------------------------------------------------------------------------------------------------------------------------

def xmltransform(infile, xslt, outfile):
    '''
        This function creates a command line subprocess for python to run saxon. You must have saxon installed.
        We are currently running Saxon HE, which is an open source xslt processor, and uses a .Net framework.
        This method can replicated using an oXygen transformation scenario, if that is more familiar
    '''
    return_status = subprocess.run(["Transform", f"-s:{infile}", f"-xsl:{xslt}", f"-o:{outfile}"], encoding="utf-8")

    if return_status.returncode != 0:
        print(return_status.stderr)

# 
def roottag(file):
    '''
        Our merge xsl does not add roottags, so we use python to add them after merger.
    '''
    tree = ET.parse(file)
    root = tree.getroot()
    # BePress uses a 'documents' root, so it makes sense to write this into the code.
    # If you need to change the rootname do so here.
    newroot = ET.Element('documents')
    newroot.insert(0, root)
    tree = (ET.ElementTree(tree.getroot()))
    tree.write(file, xml_declaration=True, encoding='utf-8', method='xml')


def proquest2bepress(py_path, currentpath):
    '''
        Function responsible for the transformation from proquest's schema to bepress'
    '''
    fold = ('XML-Transformed')
    if not os.path.exists(fold):
        os.makedirs(fold)

    # define premises for transformation
    pq_infile = os.path.join(currentpath, "XML")
    xslt_script = os.path.join(py_path, "Sup", "ETD-ProQuestXML2bepressXML-2017.xsl")
    be_outfile = os.path.join(currentpath, "XML-Transformed")

    for file in glob.glob(pq_infile + '\\*.xml'):
        base = xmlrename(file)
        out = os.path.join(be_outfile, base, '-out.xml')
        xmltransform(file, xslt_script, out)


# -------------------------------------------------------------------------------------------------------------------------------
# unzip, chext (change extension), and includesubpath (add extension)
# Designed for more basic os needs within the workflow

def unzip(location, path):
    '''
        Unzips all files in a specific path. Primarily used for unzipping proquest files from the shared drive. 
    '''
    for file in glob.glob(str(location) + '\*'):
        zip_ref = zipfile.ZipFile(file, 'r')
        zip_ref.extractall(path)
        zip_ref.close()


def chext(file, current_ext, desired_ext):
    '''
        Replaces one file extention with another
    '''
    try:
        file = file.replace("_DATA-out", "")
    except ValueError:
        pass
    new_file = file.replace(current_ext, desired_ext)
    return os.path.basename(new_file)


def includesubpath(file, desired_ext):
    new_file = file + "\\*" + desired_ext
    return new_file


def xmlrename(file):
    change1 = os.path.basename(file)
    change2 = os.path.splitext(change1)[0]
    return change2


# -----------------------------------------------------------------------------------------------------------------------------
class Validate(object):
    """
    Methods:
    validate: assigns fuzzy score based on levenshtein distance. If there is a direct match, the object is valid
    titleresolve: when there is a discrepency between an ETD's pdf coversheet and our Proquest data, title resolve is a
    simple interface for editing the title
    authorreslove: ditto but for an author's first, middle, and last name
    """

    def __init__(self, xmlitem, pdfitem, pdfpath, pdfreader):
        self.xml = xmlitem
        self.pdf = pdfitem
        self.pdfpath = pdfpath
        # pdfreader is needed to open and close pdf during QC
        self.pdfreader = pdfreader
        self.valid = False
        self.validauthor = False
        self.pdf2lname = False
        self.pdf2mname = False

    def validatetitle(self):
        # this line seems to be generating an encoding error, attempt to use lazy_encode to fix
        try:
            score = fuzz.ratio(str(self.pdf).lower(), str(self.xml).lower())
        except UnicodeEncodeError:
            self.pdf = lazy_encode(self.pdf)
            self.xml = lazy_encode(self.xml)
        score = fuzz.ratio(str(self.pdf).lower(), str(self.xml).lower())
        self.score = score
        if self.score == 100:
            self.valid = True
        else:
            return self.score

    def validateauthor(self, fname, mname, lname, author):
        '''
            Validates author by looking for several name combinations. This code 
            can be edited to make the author validation stricter or more permissive as 
            desired. However, note that the more strict the validation, the more manual review 
            will be required. 
        '''
        # Try several combinations looking for a match
        # Comment out certain combinations for stricter error generation
        pdfnamelist = str(self.pdf).split(" ")
        try:
            self.pdffname = pdfnamelist[0]
        except IndexError:
            self.pdffname = 'None'
        try:
            self.pdfmname = pdfnamelist[1]
        except IndexError:
            self.pdfmname = 'None'
        try:
            self.pdflname = pdfnamelist[2]
        except IndexError:
            self.pdflname = 'None'
        try:
            x = pdfnamelist[1]
            y = pdfnamelist[2]
            self.pdf2lname = x + " " + y
        except IndexError:
            self.pdf2name = 'None'
        try:
            ma = pdfnamelist[2]
            mb = pdfnamelist[3]
            self.pdf2mname = ma + " " + mb
        except IndexError:
            self.pdf2mname = 'None'

        fname_score = fuzz.ratio(str(self.pdffname).strip(), fname)
        mname_score = fuzz.ratio(str(self.pdfmname).strip(), mname)
        lname_score = fuzz.ratio(str(self.pdflname).strip(), lname)
        twoname_score = fuzz.ratio(str(self.pdfmname).strip(), lname)
        pdf2lname_score = fuzz.ratio(str(self.pdf2lname).strip(), lname)
        pdf2mname_score = fuzz.ratio(str(self.pdf2mname).strip(), mname)
        permissive_score = fuzz.ratio(str(self.pdf).strip(), author)


        if fname_score + mname_score + lname_score == 300:
            self.validauthor = True
        elif fname_score + twoname_score == 200:
            self.validauthor = True
        # Comment out the following for stricter middle name control
        elif fname_score + lname_score == 200:
            self.validauthor = True
        elif pdf2lname_score + fname_score == 200:
            self.validauthor = True
        elif pdf2lname_score + fname_score + mname_score == 300:
            self.validauthor = True
        # Comment out the following for stricter middle name control
        elif pdf2lname_score + fname_score == 200:
            self.validauthor = True
        elif fname_score + pdf2mname_score + lname_score == 300:
            self.validauthor = True
        # Most Permissive Name Field Comment out for stricter control
        elif permissive_score == 100:
            self.validauthor = True
        else:
            return fname_score, mname_score, lname_score

    def titleresolve(self):
        '''
            Confirms that the title from proquest matches the title taken from OCR.
        '''
        if self.valid == False:
            print('---------------------------------------------------------------------------------------------------')
            print("TITLE Needs Validated::")
            # y = raw_input(
            #   "-----------------------------------------Open PDF? [y|n] ----------------------------------------- ")
            # Uncomment above section to provide choice of opening PDF
            print ('--------------------------------------------------------------------------------------------------')
            y = 'Y'
            if y == 'y' or y == 'Y':
                FNULL = open(os.devnull, 'w')
                self.doc = subprocess.Popen("%s %s" % (self.pdfreader, self.pdfpath), stdout=FNULL,
                                            stderr=subprocess.STDOUT)
            else:
                pass
            cont = True
            self.cor = "n/a"
            while cont == True:
                print("---XML Field [1]: " + self.xml)
                print("---PDF Field [2]: " + self.pdf)
                print("---Your Field: " + self.cor)
                var = input("Enter your correction: ")
                if var == '1':
                    self.cor = self.xml
                elif var == '2':
                    self.cor = self.pdf
                else:
                    self.cor = var

                print((self.cor))
                correction = input('Are you happy with this change? [y|n]')
                if correction == 'y' or correction == 'Y':
                    cont = False
                    if self.cor == self.xml:
                        try:
                            self.doc.kill()
                            time.sleep(1)
                        except Exception:
                            pass
                        return None
                    else:
                        try:
                            self.doc.kill()
                            time.sleep(1)
                        except Exception:
                            pass
                        return self.cor
                else:
                    continue
            else:
                pass

    def authorresolve(self, fname, mname, lname):
        if self.validauthor == False:
            try:
                self.fname = str(fname)
            except UnicodeEncodeError:
                self.fname = 'ERROR'
            try:
                self.mname = str(mname)
            except UnicodeEncodeError:
                self.mname = 'ERROR'
            try:
                self.lname = str(lname)
            except UnicodeEncodeError:
                self.lname = 'ERROR'
            print("------------------------------------------------------------------------------------------------")
            print("AUTHOR Needs Validated:")
            # y = raw_input(
            #    "-----------------------------------------Open PDF? [y|n] ----------------------------------------- ")
            # Uncomment above to provide option for opening PDF
            print("------------------------------------------------------------------------------------------------")
            y = "y"
            if y == 'y' or y == 'Y':
                FNULL = open(os.devnull, 'w')
                self.doc = subprocess.Popen("%s %s" % (self.pdfreader, self.pdfpath), stdout=FNULL,
                                            stderr=subprocess.STDOUT)
            else:
                pass
            cont = True
            while cont == True:
                print("-XML--FirstName[1]: " + self.fname)
                print("-XML--MiddleName[2]: " + self.mname)
                print("-XML--LastName [3]: " + self.lname)
                print("-PDF--FullName: " + self.pdf)
                print("------------------------------------------------")
                fname = input("FirstName: ")
                mname = input("MiddleName: ")
                lname = input("LastName: ")
                if fname == '1':
                    self.fname = self.fname
                elif fname == '2':
                    self.fname = self.mname
                elif fname == '3':
                    self.fname = lname
                elif fname == 'quit':
                    self.doc.kill()
                    time.sleep(1)
                    return None
                else:
                    self.fname = fname

                if mname == '1':
                    self.mname = self.fname
                elif mname == '2':
                    self.mname = self.mname
                elif mname == '3':
                    self.mname = lname
                else:
                    self.mname = mname

                if lname == '1':
                    self.lname = self.fname
                elif lname == '2':
                    self.lname = self.mname
                elif lname == '3':
                    self.lname = self.lname
                else:
                    self.lname = lname

                print((self.fname, self.mname, self.lname))

                correction = input('Are you happy with this change? [y|n]')
                if correction == 'y' or correction == 'Y':
                    self.doc.kill()
                    time.sleep(1)
                    cont = False
                    return [self.fname, self.mname, self.lname]
                else:
                    continue
            else:
                pass
    