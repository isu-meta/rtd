# This file processed ETDs that have not been successfully captured from the Marc Records
# OCLC number need to be manually collected
import sys
import os
sys.path.append(os.path.join(os.getcwd(), "rtd"))

import logging

from rtd.metabeqc import roottag, xmltransform, PDFPress
from rtd.rtd2 import XMLBuilder
from rdflib import Graph, URIRef, Namespace, Literal
from PyPDF2 import PdfFileReader

logging.basicConfig()
# executable
pdf_reader = 'C:\\Program Files (x86)\\Adobe\\Acrobat DC\\Acrobat\\Acrobat.exe'

# paths
path = "C:\\Users\\wteal\\Projects\\rtd"
code = os.path.join(path, "rtd")
triplestore = os.path.join(path, "RDF_TripleStore")
pdf_path = os.path.join(path, "RTD_PDF")
authority_path = os.path.join(path, "Authorities")

authority_turtle = os.path.join(authority_path, "DisciplineLookup.ttl")
merge = os.path.join(code, "merge.xsl")
# oclc_list should include filename, .ttl, and degree. Sample Input for oclc_list:
# 'Madsen_ISU-1978-M2671.pdf$http://www.worldcat.org/oclc/4444949.ttl$http://lib.iastate.edu/#degrees-MasterofScience'
directory = os.path.join(authority_path, "XMLFiles")
if not os.path.exists(directory):
    os.makedirs(directory)

with open(os.path.join(path, "oclc_list.txt"), "r", encoding="utf-8") as fh:
    oclc_list = [item.strip() for item in list(fh)]

#oclc_list = open(os.path.join(path, "oclc_list.txt"),'r').readlines()
#oclc_list = map(lambda s: s.strip(), oclc_list)
g = Graph(store='Sleepycat', identifier='RTD')
g.open(triplestore, create=True)
fake = Namespace('http://lib.dr.iastate.edu/Fake#')
g.bind('fake', fake)
for item in oclc_list:
    newitem = item.split('$')
    localpdf = newitem[0]
    degrees = "http://lib.iastate.edu/#degrees-MasterofScience"
    fullpdf = os.path.join(pdf_path, localpdf)
    try:
        oclcURI = newitem[1].replace('.ttl', "")
    except IndexError:
        print(item, 'out of range')

    print(oclcURI)
    g.parse(newitem[1], format='ttl')
    g.add((URIRef(oclcURI), fake.fileName, Literal(localpdf)))
    g.add((URIRef(oclcURI), fake.degree, URIRef(degrees)))
    pdfopen = PdfFileReader(open(fullpdf, 'rb'))
    pdfpages = pdfopen.getNumPages()
    g.add((URIRef(oclcURI), fake.pageCount, Literal(str(pdfpages) + " pages")))
    PDF = PDFPress(file=fullpdf, pdfreader=pdf_reader)
    PDF.genfile()
    PDF.genlines()
    PDF.findmajor()
    old_major = PDF.reconcilemajor(os.path.join(authority_path, 'ListofMajors.csv'))
    old_major_uri = URIRef("http://lib.iastate.edu/#majors-%s_major" % old_major.replace(" ", ""))
    g.add((URIRef(oclcURI), fake.major, old_major_uri))
    continue

# parsing authority
os.chdir(authority_path)
g.parse('DisciplineLookup.ttl', format='ttl')

# SPARQL Query
qres = g.query(
    """
   PREFIX bgn:<http://bibliograph.net/> 
   PREFIX fake:<http://lib.dr.iastate.edu/Fake#> 
   PREFIX genont:<http://www.w3.org/2006/gen/ont#> 
   PREFIX library:<http://purl.org/library/> 
   PREFIX ns1:<http://www.w3.org/2006/time#> 
   PREFIX pto:<http://www.productontology.org/id/> 
   PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#> 
   PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#> 
   PREFIX schema:<http://schema.org/> 
   PREFIX skos:<http://www.w3.org/2004/02/skos/core#> 
   PREFIX time:<http://www.w3.org/2006/time#year> 
   PREFIX void:<http://rdfs.org/ns/void#> 
   PREFIX wdrs:<http://www.w3.org/2007/05/powder-s#> 
   PREFIX xml:<http://www.w3.org/XML/1998/namespace> 
   PREFIX xsd:<http://www.w3.org/2001/XMLSchema#> 
   SELECT ?title ?pub_date ?institution ?creator ?major ?degree ?oclc ?filesize ?majorURI ?degreeURI ?familyName ?fileName (group_concat(?keyword ; SEPARATOR="|") AS ?keywords) ?thesisURI (group_concat(?abstract ; SEPARATOR="|") AS ?abstracts)
   WHERE
   {
   ?thesisURI a bgn:Thesis;
       fake:pageCount ?filesize ;
       fake:fileName ?fileName ;
       library:oclcnum ?oclc ;
       schema:name ?title ;
       schema:datePublished ?pub_date ;
       BIND ((IF (?pub_date >= "1959", "Iowa State University", "Iowa State College"))AS ?institution) .
   ?thesisURI schema:creator ?creatorURI .
   OPTIONAL{?creatorURI schema:name ?creator ;
       schema:familyName ?familyName }.
   ?thesisURI fake:major ?majorURI ;
       fake:degree ?degreeURI .
   OPTIONAL{?majorURI skos:prefLabel ?major }.
   ?degreeURI skos:prefLabel ?degree .
   OPTIONAL {?thesisURI schema:description ?abstract} .
   OPTIONAL {?thesisURI schema:about ?keywordURI .
   ?keywordURI schema:name ?keyword .} .
   }
   GROUP BY ?thesisURI ?title ?pub_date ?institution ?creator ?major ?degree ?oclc ?filesize
   """
)
# split query results into separate variables
for row in qres:
    con_item = ("%s$%s-01-01$%s$%s$%s$%s$%s$%s$%s$%s$%s$%s$%s$%s$%s" % row)
    sp_item = con_item.split('$')
    r_title = sp_item[0]
    r_date = sp_item[1]
    r_inst = sp_item[2]
    r_creator = sp_item[3]
    r_major = sp_item[4]
    r_degree = sp_item[5]
    r_oclc = sp_item[6]
    r_filesize = sp_item[7]
    r_majorURI = sp_item[8]
    r_degreeURI = sp_item[9]
    r_familyName = sp_item[10]
    r_fileName = sp_item[11]
    r_keyword = (sp_item[12]).split("|")
    r_abstract = (sp_item[14]).split("|")
    year = r_date.encode('utf-8')
    degree = r_degreeURI.encode('utf-8')
    major = r_majorURI.encode('utf-8')

    sparql_values = (major, degree)

    # pass sparql_values into subquery to find current BePress Discipline and associated department via authority lookup concept
    sub_qres = g.query(
        """
        PREFIX time:<http://www.w3.org/2006/time#>
        PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
        PREFIX skos:<http://www.w3.org/2004/02/skos/core#>
        PREFIX fake:<http://lib.dr.iastate.edu/Fake#>
        PREFIX owl:<http://www.w3.org/2002/07/owl#>
        SELECT ?discipline ?department
        WHERE
        {
        ?url a owl:Class;
            fake:hasMajor <%s> ;
            fake:hasDegree <%s> ;
            fake:hasDepartment ?departmentURI ;
            rdfs:subClassOf ?disciplineURI .
        ?disciplineURI skos:prefLabel ?discipline .
        ?departmentURI skos:prefLabel ?department .
        }
        LIMIT 1
        """ % sparql_values
    )
    # create lists to append query results
    r_discipline_list = []
    r_department_list = []
    # further refining and reformatting query results
    for row in sub_qres:
        con2_item = "%s$%s" % row
        split_item = con2_item.split("$")
        r_discipline_list.append(split_item[0])
        # The disciplines and departments are reversed, but the disciplines field needs the department as well
        r_department_list.append(split_item[0].strip())
        r_department_list.append(split_item[1].strip())
    creator_split = r_creator.split(' ')
    fname = creator_split[0]
    if len(creator_split) == 3:
        mname = creator_split[1]
        lname = creator_split[2]
    else:
        mname = None
        lname = r_familyName

    new_r_keyword = []
    for item in r_keyword:
        if item not in new_r_keyword:
            new_r_keyword.append(item)

    new_r_abstract = []
    for item in r_abstract:
        if item not in new_r_abstract and item != u'':
            new_r_abstract.append(item)

    new_r_keyword.append(r_major)

    # I messed up the authority file and put disciplies under departments and departments under disciplines
    # This will need to be corrected in the future, but this is why the department variable is from the discipline list
    r_department = "".join(r_discipline_list)
    r_url = "https://behost.lib.iastate.edu/DR/" + r_fileName
    try:
        print("processing {}...".format(r_url))
    except Exception:
        print('error')
    # Create XMLBuilder object which will take query results and format them into BePress XML
    XB = XMLBuilder(title=r_title, publication_date=r_date, institution=r_inst, fname=fname, mname=mname,
                    lname=lname,
                    discipline=list(set(r_department_list)), url=r_url, document_type='thesis',
                    degree_name=r_degree,
                    department=r_department, copyright_date=r_date.replace("-01-01", ""), filesize=r_filesize,
                    major=r_major, oclc=r_oclc, keyword=[x for x in new_r_keyword if x is not u''],
                    abstract="".join([x for x in new_r_abstract if x is not None]))
    # Merge XML files for batch upload and move output to desired directory

inpath = os.path.join(authority_path, "XMLFiles")
fileinpath = os.listdir(inpath)[0]
newinpath = os.path.join(inpath, fileinpath)

outpath = os.path.join(path, 'outfile2.xml')
merge_var = os.path.join(path, "rtd", "merge.xsl")

xmltransform(newinpath, merge_var, outpath)
roottag(outpath)

g.close()
