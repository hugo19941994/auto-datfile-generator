import sys
import os
import xml.etree.ElementTree as ET
import re
import requests
import http.server
import socketserver




#Config
userinfo_filename = 'UserInfo.xml'
url_home = 'http://redump.org/'
url_downloads = 'http://redump.org/downloads/'
url_login = 'http://forum.redump.org/login/'
regex = {
        'datfile' : r'<a href="/datfile/(.*?)">',
        'date' : r'\) \((.*?)\)\.',
        'name' : r'filename="(.*?) Datfile',
        'csrf' : r'csrf_token" value="(.*?)"'
}

xml_filename = 'profile.xml'
server_address = '127.0.0.1'
server_port = 80


def update():
    client = requests.session()



def Update_XML():
    print('Updating XML:')

    print(' * Retrieving site info', end=' ')
    sys.stdout.flush()

    client = requests.session()
    result = client.get(url_downloads)
    result.raise_for_status()

    print('(DONE)')
    print(' * Processing data', end=' ')
    sys.stdout.flush()

    datFiles = re.findall(regex['datfile'], str(result.text))
    datInfo = []
    dict = {}
    for dat in datFiles:
        response = client.head(url_home+'datfile/'+dat)
        content_header = response.headers['Content-Disposition']

        #get the date from the file name
        dict['Date'] = re.findall(regex['date'], content_header)[0]

        #generate the dat's name
        tempName = re.findall(regex['name'], content_header)[0]
        #trim the - from the end (if exists)
        if (tempName.endswith('-')):
            tempName = tempName[:-2]
        elif (tempName.endswith('BIOS')):
            tempName = tempName + ' Images'
        dict['Name'] = tempName
        dict['URL'] = f'{url_home}datfile/{dat}'
        dict['File'] = f'{tempName}.dat'
        datInfo.append(dict.copy())

    print('(DONE)')
    print(' * Writing to ' + xml_filename, end=' ')
    sys.stdout.flush()

    tag_clrmamepro = ET.Element('clrmamepro')
    for info in datInfo:
        tag_datfile = ET.SubElement(tag_clrmamepro, 'datfile')
        ET.SubElement(tag_datfile, 'name').text = info['Name']
        ET.SubElement(tag_datfile, 'description').text = info['Name']
        ET.SubElement(tag_datfile, 'version').text = info['Date']
        ET.SubElement(tag_datfile, 'author').text = 'redump.org'
        ET.SubElement(tag_datfile, 'comment').text = '_'
        ET.SubElement(tag_datfile, 'url').text = info['URL']
        ET.SubElement(tag_datfile, 'file').text = info['File']
                
    xmldata = ET.tostring(tag_clrmamepro).decode()
    xmlfile = open(xml_filename, 'w')
    xmlfile.write(xmldata)
    print('(DONE)')


print('Welcome to Redump.org XML updater [Github: bilakispa/redump-xml-updater]')
try:
    Update_XML()
except KeyboardInterrupt:
        pass
