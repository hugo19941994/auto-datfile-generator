from datetime import date
from io import BytesIO
from time import sleep
from selenium import webdriver
import logging
import os
import re
import xml.etree.ElementTree as ET
import zipfile

regex = {
    'date': r'[0-9]{8}-[0-9]*',
    'name': r'(.*?.)( \([0-9]{8}-[0-9]*\).dat)',
    'filename': r'filename="(.*?)"',
}
xml_filename = 'no-intro.xml'

# Dowload no-intro pack using selenium
dir_path = os.path.dirname(os.path.realpath(__file__))
fx_profile = webdriver.FirefoxProfile();
fx_profile.set_preference("browser.download.folderList", 2);
fx_profile.set_preference("browser.download.manager.showWhenStarting", False);
fx_profile.set_preference("browser.download.dir", dir_path);
fx_profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip");

options = webdriver.FirefoxOptions()
options.headless = True

driver = webdriver.Firefox(firefox_profile=fx_profile, options=options);
driver.implicitly_wait(10)

driver.get("https://datomatic.no-intro.org")
driver.find_element_by_xpath('/html/body/div/header/nav/ul/li[3]/a').click()
driver.find_element_by_xpath('/html/body/div/section/article/table[1]/tbody/tr/td/a[6]').click()
driver.find_element_by_xpath('/html/body/div/section/article/div/form/input[1]').click()
driver.find_element_by_xpath('/html/body/div/section/article/div/form/input').click()

# wait until file is found
found = False
name = None
time_slept = 0
while not found:
    if time_slept > 360:
        raise Exception('No-Intro zip file not found')

    for f in os.listdir(dir_path):
        if 'No-Intro Love Pack' in f:
            name = f
            found = True
            break

    # wait 5 seconds
    sleep(5)
    time_slept += 5

os.rename(name, f'{dir_path}/no-intro.zip')

# load zip file
archive = zipfile.ZipFile(f'{dir_path}/no-intro.zip')

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
