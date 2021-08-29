from time import sleep
from io import BytesIO, StringIO
import os
import re
import requests
import xml.etree.ElementTree as ET
import zipfile

xml_filename = 'dats-site.xml'

regex = {
    'date': r'\)_\((.*?)\)\.',
    'name': r'filename=(.*?).zip',
    'filename': r'filename=(.*)',
}

# zip file to store all DAT files
zipObj = zipfile.ZipFile(f'dats-site.zip', 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9)

# clrmamepro XML file
tag_clrmamepro = ET.Element('clrmamepro')


for i in range(1, 8):
    print(f'Downloading dat {i}/7')
    response = requests.get(f"https://dats.site/getcustdat.php?custdatid={i}")
    content_header = response.headers['Content-Disposition']
    print(content_header)

    # section for this dat in the XML file
    tag_datfile = ET.SubElement(tag_clrmamepro, 'datfile')

    # XML version
    dat_date = re.findall(regex['date'], content_header)[0]
    print(dat_date)
    ET.SubElement(tag_datfile, 'version').text = dat_date

    # XML name & description
    tempName = re.findall(regex['name'], content_header)[0]
    print(tempName)
    # trim the - from the end (if exists)
    if (tempName.endswith('-')):
        tempName = tempName[:-2]
    elif (tempName.endswith('BIOS')):
        tempName = tempName + ' Images'
    ET.SubElement(tag_datfile, 'name').text = tempName
    ET.SubElement(tag_datfile, 'description').text = tempName

    # URL tag in XML
    ET.SubElement(
        tag_datfile, 'url').text = f'https://github.com/hugo19941994/auto-datfile-generator/releases/latest/download/dats-site.zip'

    # File tag in XML
    originalFileName = re.findall(regex['filename'], content_header)[0]
    print(originalFileName)
    fileName = f'{originalFileName[:-4]}.dat'
    ET.SubElement(tag_datfile, 'file').text = fileName

    # Author tag in XML
    ET.SubElement(tag_datfile, 'author').text = 'dats.site'

    # Command XML tag
    ET.SubElement(tag_datfile, 'comment').text = '_'

    # Get the DAT file
    datfile_name = f'{fileName[:-4]}.dat'
    print(datfile_name)

    # extract datfile from zip to store in the DB zip
    zipdata = BytesIO()
    zipdata.write(response.content)
    archive = zipfile.ZipFile(zipdata)
    zipObj.writestr(datfile_name, archive.read(datfile_name))

# store clrmamepro XML file
xmldata = ET.tostring(tag_clrmamepro).decode()
xmlfile = open(xml_filename, 'w')
xmlfile.write(xmldata)

# Save DB zip file
zipObj.close()
