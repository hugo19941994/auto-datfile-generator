from time import sleep
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
import hashlib
import os
import re
import requests
import xml.etree.ElementTree as ET
import zipfile

regex = {
    'date': r'[0-9]{8}-[0-9]*',
    'name': r'(.*?.)( \([0-9]{8}-[0-9]*\).dat)',
    'filename': r'filename="(.*?)"',
}

no_intro_type = {
    'standard': 'standard',
    'parent-clone': 'xml'
}

for key, value in no_intro_type.items():

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

        # select downloads
        driver.find_element_by_xpath('/html/body/div/header/nav/ul/li[3]/a').click()

        # select daily downloads
        driver.find_element_by_xpath('/html/body/div/section/article/table[1]/tbody/tr/td/a[6]').click()

        # find the type of dat file
        x = driver.find_element_by_name('dat_type')
        drop = Select(x)

        # Select by value
        drop.select_by_value(value)
        sleep(5)

        # click the prepare button
        driver.find_element_by_xpath(f'/html/body/div/section/article/div/form/input[1]').click()

        captcha = False

        try:
            captcha_image = driver.find_element_by_xpath('/html/body/div/section/article/div/form/img').get_attribute(
                'src')
            captcha = True
        except NoSuchElementException:
            pass

        if not captcha:
            try:
                driver.find_element_by_name('dwnl').click()
            except NoSuchElementException:
                continue
        else:
            # download the captcha image
            image = requests.get(captcha_image, stream=True).raw

            # hash the image
            hasher = hashlib.md5()
            buf = image.read()
            hasher.update(buf)
            hash = hasher.hexdigest()

            hash_map = {
                '402240d761cb146915b25a01c771c6a9': 'dwnl_blue',
                '3fe379d46842ffed389aa9bbeb42bb93': 'dwnl_red',
                '1e3ad98f1290f8ba0d3fc21f313f5396': 'dwnl_yellow'
            }

            # click the correct captcha color coded download button
            driver.find_element_by_name(hash_map[hash]).click()


        # wait until file is found
        found = False
        name = None
        time_slept = 0
        while not found:
            if time_slept > 360:
                raise Exception(f'No-Intro {key} zip file not found')

            for f in os.listdir(dir_path):
                if 'No-Intro Love Pack' in f:
                    name = f
                    found = True
                    break

            # wait 5 seconds
            sleep(5)
            time_slept += 5

        archive_name = f'no-intro({key}).zip'
        archive_full = f'{dir_path}/{archive_name}'
        os.rename(name, archive_full)

        # load zip file
        archive = zipfile.ZipFile(archive_full)

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
                tag_datfile, 'url').text = f'https://github.com/retroarcher-resarch/dats/releases/download/latest/{archive_name}'

            # File tag in XML
            fileName = dat
            fileName = f'{fileName[:-4]}.dat'
            ET.SubElement(tag_datfile, 'file').text = fileName
            print(fileName)

            # Author tag in XML
            ET.SubElement(tag_datfile, 'author').text = 'no-intro.org'

            # Command XML tag
            ET.SubElement(tag_datfile, 'comment').text = '_'

        # store clrmamepro XML file
        xmldata = ET.tostring(tag_clrmamepro).decode()
        xml_filename = f'no-intro({key}).xml'
        xmlfile = open(xml_filename, 'w')
        xmlfile.write(xmldata)
