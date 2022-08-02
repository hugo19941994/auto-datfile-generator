import zipfile
from io import BytesIO, StringIO
from datetime import date
from time import sleep
import xml.etree.ElementTree as ET
from lxml import objectify
import re
import requests


# Config
url_home = 'http://redump.org/'
url_downloads = 'http://redump.org/downloads/'
regex = {
    'datfile': r'<a href="/datfile/(.*?)">',
    'date': r'\) \((.*?)\)\.',
    'name': r'filename="(.*?) Datfile',
    'filename': r'filename="(.*?)"',
}

xml_filename = 'redump.xml'


def _find_dats():
    download_page = requests.get(url_downloads)
    download_page.raise_for_status()

    dat_files = re.findall(regex['datfile'], download_page.text)
    return dat_files


def Update_XML():
    dat_list = _find_dats()

    # zip file to store all DAT files
    zipObj = zipfile.ZipFile(f'redump.zip', 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9)

    # clrmamepro XML file
    tag_clrmamepro = ET.Element('clrmamepro')

    for dat in dat_list:
        print(f'Downloading {dat}')
        # section for this dat in the XML file
        tag_datfile = ET.SubElement(tag_clrmamepro, 'datfile')

        response = requests.get(url_home+'datfile/'+dat)
        content_header = response.headers['Content-Disposition']

        # XML version
        dat_date = re.findall(regex['date'], content_header)[0]
        ET.SubElement(tag_datfile, 'version').text = dat_date

        # XML name & description
        tempName = re.findall(regex['name'], content_header)[0]
        # trim the - from the end (if exists)
        if (tempName.endswith('-')):
            tempName = tempName[:-2]
        elif (tempName.endswith('BIOS')):
            tempName = tempName + ' Images'
        ET.SubElement(tag_datfile, 'name').text = tempName
        ET.SubElement(tag_datfile, 'description').text = tempName

        # URL tag in XML
        ET.SubElement(
            tag_datfile, 'url').text = f'https://github.com/hugo19941994/auto-datfile-generator/releases/latest/download/redump.zip'

        # File tag in XML
        originalFileName = re.findall(regex['filename'], content_header)[0]
        fileName = f'{originalFileName[:-4]}.dat'
        ET.SubElement(tag_datfile, 'file').text = fileName

        # Author tag in XML
        ET.SubElement(tag_datfile, 'author').text = 'redump.org'

        # Command XML tag
        ET.SubElement(tag_datfile, 'comment').text = '_'

        # Get the DAT file
        datfile_name = f'{fileName[:-4]}.dat'
        print(f'DAT filename: {datfile_name}')
        if originalFileName.endswith('.zip'):
            # extract datfile from zip to store in the DB zip
            zipdata = BytesIO()
            zipdata.write(response.content)
            archive = zipfile.ZipFile(zipdata)
            zipObj.writestr(datfile_name, archive.read(datfile_name))
        else:
            # add datfile to DB zip file
            datfile = response.text
            zipObj.writestr(datfile_name, datfile)
        print()
        sleep(5)

    # store clrmamepro XML file
    xmldata = ET.tostring(tag_clrmamepro).decode()
    xmlfile = open(xml_filename, 'w')
    xmlfile.write(xmldata)

    # Save DB zip file
    zipObj.close()
    print('Finished')


try:
    Update_XML()
except KeyboardInterrupt:
    pass
