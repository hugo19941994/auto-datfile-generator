from datetime import date
import xml.etree.ElementTree as ET
from io import BytesIO
import re
import logging
import os
import requests
import zipfile

regex = {
    'date': r'[0-9]{8}-[0-9]*',
    'name': r'(.*?.)( \([0-9]{8}-[0-9]*\).dat)',
    'filename': r'filename="(.*?)"',
}
xml_filename = 'no-intro.xml'


def downloadNoIntro():
    logging.info("Downloading No-Intro DATs")

    headers = {
        "Accept": ("text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,"
                   "application/signed-exchange;v=b3;q=0.9"),
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9,es;q=0.8,it;q=0.7",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "DNT": "1",
        "Host": "datomatic.no-intro.org",
        "Origin": "https://datomatic.no-intro.org",
        "Pragma": "no-cache",
        "Referer": "https://datomatic.no-intro.org/index.php?page=download&op=daily",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/79.0.3945.117 Safari/537.36")
    }

    # Request daily DAT pack
    s = requests.Session()  # session to maintain cookies
    r = s.post("https://datomatic.no-intro.org/index.php?page=download&op=daily",
               data={"dat_type": "standard", "sometimes-I-change-this-too": "Prepare", "recaptcha_response": ""}, headers=headers, allow_redirects=False)
    r.raise_for_status()

    # Extract download ID from the 302 response Location header
    download_id = r.headers["Location"].rsplit("=", 1)[-1]

    # Download the DAT pack
    r = s.post(f"https://datomatic.no-intro.org/index.php?page=manager&download={download_id}",
               params={"page": "manager", "download": download_id}, data={"wtwtwtf": "Download"}, headers=headers, allow_redirects=True)
    r.raise_for_status()

    # get zip filename
    content_header = r.headers['Content-Disposition']
    zipName = re.findall(regex['filename'], content_header)[0]
    print(zipName)
    #with open(zipName, 'wb') as f:
    with open('no-intro.zip', 'wb') as f:
        f.write(r.content)

    # Load zip file into memory
    zipdata = BytesIO()
    zipdata.write(r.content)
    archive = zipfile.ZipFile(zipdata)

    # clrmamepro XML file
    tag_clrmamepro = ET.Element('clrmamepro')
    for dat in archive.namelist():
        print(dat)
        # section for this dat in the XML file
        tag_datfile = ET.SubElement(tag_clrmamepro, 'datfile')

        # XML version
        dat_date = re.findall(regex['date'], dat)[0]
        ET.SubElement(tag_datfile, 'version').text = dat_date
        print(dat_date)

        # XML name & description
        tempName = re.findall(regex['name'], dat)[0][0]
        ET.SubElement(tag_datfile, 'name').text = tempName
        ET.SubElement(tag_datfile, 'description').text = tempName
        print(tempName)

        # URL tag in XML
        ET.SubElement(
            tag_datfile, 'url').text = f'https://github.com/hugo19941994/auto-datfile-generator/releases/download/latest/no-intro.zip'
            #tag_datfile, 'url').text = f'https://github.com/hugo19941994/auto-datfile-generator/releases/download/latest/{zipName}'

        # File tag in XML
        fileName = dat
        fileName = f'{fileName[:-4]}.dat'
        ET.SubElement(tag_datfile, 'file').text = fileName
        print(fileName)

        # Author tag in XML
        ET.SubElement(tag_datfile, 'author').text = 'redump.org'

        # Command XML tag
        ET.SubElement(tag_datfile, 'comment').text = '_'

    # store clrmamepro XML file
    xmldata = ET.tostring(tag_clrmamepro).decode()
    xmlfile = open(xml_filename, 'w')
    xmlfile.write(xmldata)


downloadNoIntro()
