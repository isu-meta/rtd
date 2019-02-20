import glob
import os
import shutil

from lxml import etree
from pymarc import MARCReader
from PyPDF2 import PdfFileReader
from rdflib import Graph, Namespace, URIRef, Literal

from rtd.metabeqc import PDFPress
from rtd.regreplace import *

# -----------------------------------------------------------------------------------------------------
class Marc2RDF(object):
    """
    Takes MARC Records, locates OCLC linked data, and places OCLC linked data in triplestore
    To the best of my knowledge flat-files like .marc need to be looped through, which accounts for why this code is cumbersome
    Note: the id for the triplestore defaults to 'RTD' if you change this, make sure any additional script accounts
    for this
    """

    def __init__(self, path=None, pdf_path=None, authority_path=None, pdf_reader=None, triplestore=None, marc=None):
        self.path = path
        self.pdf_path = pdf_path
        self.authority_path = authority_path
        self.pdf_reader = pdf_reader
        self.triplestore = triplestore
        self.marc = marc
        self.filenames = []
        for item in glob.glob(pdf_path + "\\*.pdf"):
            print(item)
            base_item = os.path.basename(item).replace('.pdf', "")
            self.filenames.append(base_item.split('_')[1])

    def graphmarc(self, create=False, id='RTD', sparql_major=True):
        # Create text file for relevant marc-records
        outfile = open(self.pdf_path + "outfile.txt", 'w')
        # Sleepycat will store RDF graph in memory, select create True if triplestore needs created
        g = Graph(store='Sleepycat', identifier=id)
        g.open(self.triplestore, create=create)
        # binding namespaces to Graph
        # fake namespace was created to assist with non-covered fields
        fake = Namespace('http://lib.dr.iastate.edu/Fake#')
        g.bind('fake', fake)
        # Pymarc Process
        reader = MARCReader(open(self.marc, "rb"))
        for record in reader:
            # Identifier is inconsistent across records, we need to check in two locations
            x = record['099']
            y = record['090']
            attempt1 = ('%s' % x)
            attempt2 = ('%s' % y)
            # split record and reconcile with PDF filename convention
            attempt1split = attempt1.split('\$a')
            attempt2split = attempt2.split('\$a')
            try:
                attempt1b = attempt1split[1].replace(' ', '-').replace('.', '-').replace('$a', '-').replace('$b', '-')

            except IndexError:
                attempt1b = 'None'

            try:
                attempt2b = attempt2split[1].replace(' ', '-').replace('.', '-').replace('$a', '-').replace('$b', '-')

            except IndexError:
                attempt2b = 'None'

            try:
                name = record['100']['a']
                if attempt1b in self.filenames or attempt2b in self.filenames:
                    xx = attempt1b in self.filenames
                    yy = attempt2b in self.filenames
                    outfile.write(str(record) + '\n')
                    item = record.get_fields('035')
                    degree1 = (record.get_fields('502'))
                    degree = str(degree1[0])
                    reg = RegexpReplacer(patterns=abbreviation_replacement)
                    deg_abbrev1 = (degree[degree.find("(") + 1:degree.find(")")])
                    deg_abbrev = reg.replace(deg_abbrev1)

                    outfile.write(str(item[0]) + '\n')
                    outfile.write(str(item[1]) + '\n')
                    oclc = item[0]['a']
                    oclc2 = item[1]['a']
                    if 'OCoLC' in str(oclc):
                        encodeoclc2 = oclc.encode('utf-8')
                        oclc_urlnum2 = encodeoclc2.replace('(OCoLC)0', "").replace('(OCoLC)-', "")
                        oclc_urlnum = oclc_urlnum2.replace('(OCoLC)', "")
                        outfile.write(str(oclc_urlnum) + "\n")
                        worldcat_url = 'http://www.worldcat.org/oclc/' + oclc_urlnum + '.ttl'
                        outfile.write(str(worldcat_url))
                        print(worldcat_url)
                        g.parse(worldcat_url, format='ttl')
                        uri = URIRef('http://www.worldcat.org/oclc/' + oclc_urlnum)
                        if xx == True:
                            g.add((uri, fake.localnum, Literal(str(attempt1b))))
                        elif yy == True:
                            g.add((uri, fake.localnum, Literal(str(attempt2b))))
                        # add degree
                        g.add((uri, fake.degree, URIRef(deg_abbrev)))

                    elif 'OCoLC' in str(oclc2):
                        encodeoclc2 = oclc2.encode('utf-8')
                        oclc_urlnum2 = encodeoclc2.replace('(OCoLC)0', "").replace('(OCoLC)-', "")
                        oclc_urlnum = oclc_urlnum2.replace('(OCoLC)', "")
                        outfile.write(str(oclc_urlnum) + "\n")
                        worldcat_url = 'http://www.worldcat.org/oclc/' + oclc_urlnum + '.ttl'
                        outfile.write(str(worldcat_url))
                        g.parse(worldcat_url, format='ttl')
                        uri = URIRef('http://www.worldcat.org/oclc/' + oclc_urlnum)
                        if xx == True:
                            g.add((uri, fake.localnum, Literal(str(attempt1b))))
                        elif yy == True:
                            g.add((uri, fake.localnum, Literal(str(attempt2b))))
                        # add major
                        g.add((uri, fake.degree, URIRef(deg_abbrev)))

                    else:
                        print((str(oclc2) + str(oclc)))

            except UnicodeEncodeError as e:
                print (e)
            except TypeError as e:
                pass

        if sparql_major == True:
            qres = g.query(
            """
            PREFIX time:<http://www.w3.org/2006/time#>
            PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
            PREFIX skos:<http://www.w3.org/2004/02/skos/core#>
            PREFIX fake:<http://lib.dr.iastate.edu/Fake#>
            PREFIX library:<http://purl.org/library/>
            PREFIX schema:<http://schema.org/>
            SELECT DISTINCT ?ObjectURI ?familyName ?localnum
            WHERE
            {
            ?ObjectURI schema:creator ?URI;
                fake:localnum ?localnum .
            ?URI schema:familyName ?familyName .
            }
            ORDER BY ?familyName
            """
        )
            for row in qres:
                # add file name in linked data (doesn't work with inconsistent file-naming
                # item = "g.add( ((URIRef('%s')), fake.fileName, Literal('%s_%s.pdf')))"%row
                #exec(item)
                x = "%s|%s_%s.pdf"%row
                print(x)
                y = x.split('|')
                processed_path = y[1].replace(" ", "-")
                file_uri = URIRef(y[0])
                pdf_file = self.pdf_path+'\\'+processed_path
                try:
                    pdfopen = PdfFileReader(open(pdf_file,'rb'))
                    pdfpages = pdfopen.getNumPages()
                    g.add( (file_uri, fake.pageCount, Literal(str(pdfpages)+" pages")))
                    PDF=PDFPress(pdf_file,pdfreader=self.pdf_reader)
                    PDF.genfile()
                    PDF.genlines()
                    PDF.findmajor()
                    old_major = PDF.reconcilemajor(self.authority_path + '\\OldMajors.csv')
                    old_major_uri = URIRef("http://lib.iastate.edu/#majors-%s_major"%old_major.replace(" ",""))
                    g.add( (file_uri, fake.major, old_major_uri))
                    item = "g.add( ((URIRef('%s')), fake.fileName, Literal('%s_%s.pdf')))"%row
                    exec(item)
                except Exception as e:
                    print(e)
                    mpath = input("Please enter filename manually: ")
                    if mpath == 'pass':
                        pass
                    else:
                        correct_path = self.pdf_path+"\\"+mpath
                        pdfopen = PdfFileReader(open(correct_path,'rb'))
                        pdfpages = pdfopen.getNumPages()
                        g.add( (file_uri, fake.pageCount, Literal(str(pdfpages)+" pages")))
                        PDF=PDFPress(correct_path,pdfreader=self.pdf_reader)
                        PDF.genfile()
                        PDF.genlines()
                        PDF.findmajor()
                        old_major = PDF.reconcilemajor(self.authority_path + '\\ListofMajors.csv')
                        old_major_uri = URIRef("http://lib.iastate.edu/#majors-%s_major"%old_major.replace(" ",""))
                        g.add( (file_uri, fake.major, old_major_uri))
                        g.add( (URIRef(y[0]), fake.fileName, Literal(mpath)))
                    continue


        else:
            pass



# ----------------------------------------------------------------------------------------------------

class XMLBuilder(object):
    """
    Build XML file using BePress Schema and tags
    To be populated by SPARQL results
    """

    def __init__(self, title=None, publication_date=None, email=None, institution=None, lname=None, fname=None,
                 mname=None, suffix=None,
                 discipline=None, keyword=None, abstract=None, url=None, document_type=None, degree_name=None,
                 department=None, abstract_format="html",
                 language="en", provenance="Iowa State University", copyright_date=None, embargo_date="0",
                 filesize=None, fileformat="application/pdf",
                 major=None, oclc=None):
        xsi = "http://www.w3.org/2001/XMLSchema-instance"
        NSMAP = {"xsi": xsi, "str": "http://www.metaphoricalweb.org/xmlns/string-utilities",
                 "xs": "http://www.w3.org/2001/XMLSchema"}
        # root tags
        self.root = etree.Element("documents", nsmap=NSMAP)
        self.root.attrib[
            '{{{pre}}}noNamespaceSchemaLocation'.format(pre=xsi)] = "http://www.bepress.com/document-import.xsd"
        self.document = etree.SubElement(self.root, "document")
        self.title = etree.SubElement(self.document, "title")
        self.title.text = title
        self.publication_date = etree.SubElement(self.document, "publication-date")
        self.publication_date.text = publication_date
        self.publication_date_date_format = etree.SubElement(self.document, "publication_date_date_format")
        self.publication_date_date_format.text = "YYYY-MM-DD"
        # author tags
        self.authors = etree.SubElement(self.document, "authors")
        self.author = etree.SubElement(self.authors, "author")
        self.author.attrib['{{{pre}}}type'.format(pre=xsi)] = "individual"
        self.email = etree.SubElement(self.author, "email")
        self.email.text = email
        self.institution = etree.SubElement(self.author, "institution")
        self.institution.text = institution
        self.lname = etree.SubElement(self.author, "lname")
        self.lname.text = lname
        self.fname = etree.SubElement(self.author, "fname")
        self.fname.text = fname
        self.mname = etree.SubElement(self.author, "mname")
        self.mname.text = mname
        self.suffix = etree.SubElement(self.author, "suffix")
        self.suffix.text = suffix
        # discipline
        self.disciplines = etree.SubElement(self.document, "disciplines")
        try:
            for item in discipline:
                self.discipline = etree.SubElement(self.disciplines, "discipline")
                self.discipline.text = item
        except TypeError:
            self.discipline = etree.SubElement(self.disciplines, "discipline")
        # keywords
        self.keywords = etree.SubElement(self.document, "keywords")
        try:
            for item in keyword:
                self.keyword = etree.SubElement(self.keywords, "keyword")
                self.keyword.text = item
        except TypeError:
            self.keyword = etree.SubElement(self.keywords, "keyword")
        self.abstract = etree.SubElement(self.document, "abstract")
        self.abstract.text = abstract
        self.fulltext_url = etree.SubElement(self.document, "fulltext-url")
        self.fulltext_url.text = url
        self.document_type = etree.SubElement(self.document, "document-type")
        self.document_type.text = document_type
        self.degree_name = etree.SubElement(self.document, "degree_name")
        self.degree_name.text = degree_name
        self.department = etree.SubElement(self.document, "department")
        self.department.text = department
        self.abstract_format = etree.SubElement(self.document, "abstract_format")
        self.abstract_format.text = abstract_format
        # Fields
        self.fields = etree.SubElement(self.document, "fields")
        self.language = etree.SubElement(self.fields, "field", name="language", type="string")
        self.value_language = etree.SubElement(self.language, "value")
        self.value_language.text = language
        self.provenance = etree.SubElement(self.fields, "field", name="provenance", type="string")
        self.value_provenance = etree.SubElement(self.provenance, "value")
        self.value_provenance.text = provenance
        self.copyright_date = etree.SubElement(self.fields, "field", name="copyright_date", type="string")
        self.value_copyright_date = etree.SubElement(self.copyright_date, "value")
        self.value_copyright_date.text = copyright_date
        #self.embargo_date = etree.SubElement(self.fields, "field", name="embargo_date", type="date")
        #self.value_embargo_date = etree.SubElement(self.embargo_date, "value")
        #self.value_embargo_date.text = embargo_date
        self.file_size = etree.SubElement(self.fields, "field", name="file_size", type="string")
        self.value_file_size = etree.SubElement(self.file_size, "value")
        self.value_file_size.text = filesize
        self.fileformat = etree.SubElement(self.fields, "field", name="fileformat", type="string")
        self.value_fileformat = etree.SubElement(self.fileformat, "value")
        self.value_fileformat.text = fileformat
        self.rights_holder = etree.SubElement(self.fields, "field", name="rights_holder", type="string")
        self.value_rights_holder = etree.SubElement(self.rights_holder, "value")

        if mname != None:
            try:
                self.value_rights_holder.text = ("{0} {1} {2}".format(fname, mname, lname))
            except UnicodeEncodeError:
                print((fname, mname, lname))
                self.value_rights_holder.text = input("Enter first middle and last name, separated by spaces: ")
        elif fname != None:
            try:
                self.value_rights_holder.text = ("{0} {1}".format(fname, lname))
            except UnicodeEncodeError:
                print((fname, lname))
                self.value_rights_holder.text = input("Enter first and last name, separated by spaces: ")
        else:
            self.value_rights_holder.text = lname

        self.major = etree.SubElement(self.fields, "field", name="major", type="string")
        self.value_major = etree.SubElement(self.major, "value")
        self.value_major.text = major
        self.oclc = etree.SubElement(self.fields, "field", name="oclc_number", type="string")
        self.value_oclc = etree.SubElement(self.oclc, "value")
        self.value_oclc.text = oclc
        directory = "XMLFiles"
        if not os.path.exists(directory):
            os.makedirs(directory)
        try:
            with open(os.path.join("XMLFiles", f"{oclc}.xml"), "w", encoding="utf-8", errors="xmlcharrefreplace") as outfile:
                out_tree = etree.tostring(self.root, encoding="utf-8", xml_declaration=True, pretty_print=True).decode("utf-8")
                outfile.write(out_tree)

        except ValueError:
            with open("XMLFiles/default.xml", "w", encoding="utf-8", errors="xmlcharrefreplace") as outfile:
                out_tree = etree.tostring(self.root, encoding="utf-8", xml_declaration=True, pretty_print=True).decode("utf-8")
                outfile.write(out_tree)
