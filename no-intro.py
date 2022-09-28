from PIL import Image
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie1976
from colormath.color_objects import LabColor, sRGBColor
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import Select
from time import sleep
import hashlib
import os
import re
import requests
import xml.etree.ElementTree as ET
import zipfile

regex = {
    'date'     : r'[0-9]{8}-[0-9]{6}',
    'name'     : r'(.*?.)( \([0-9]{8}-[0-9]{6}\).dat)',
    'skipfiles': r'(.*?.)( \(#[0-9]{2,4}?.*\).dat)',
}

no_intro_type = {
    'standard': 'standard',
    'parent-clone': 'xml'
}

for key, value in no_intro_type.items():

        # Dowload no-intro pack using selenium
        dir_path = os.path.dirname(os.path.realpath(__file__))
        options=Options()
        options.set_preference("browser.download.folderList", 2);
        options.set_preference("browser.download.manager.showWhenStarting", False);
        options.set_preference("browser.download.dir", dir_path);
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip");
        options.headless = True

        service = Service()

        driver = webdriver.Firefox(service=service, options=options)
        driver.implicitly_wait(10)

        driver.get("https://datomatic.no-intro.org")

        # select downloads
        driver.find_element(by='xpath', value='/html/body/div/header/nav/ul/li[3]/a').click()

        # select daily downloads
        driver.find_element(by='xpath', value='/html/body/div/section/article/table[1]/tbody/tr/td/a[5]').click()

        # find the type of dat file
        x = driver.find_element(by='name', value='dat_type')
        drop = Select(x)

        # Select by value
        drop.select_by_value(value)
        sleep(5)

        # click the prepare button
        driver.find_element(by='xpath', value=f'/html/body/div/section/article/div/form/input[1]').click()

        captcha = False

        try:
            captcha_image = driver.find_element(by='xpath', value='/html/body/div/section/article/div/form/img').get_attribute('src')
            captcha = True
        except NoSuchElementException:
            pass
        print(f'Captcha: {captcha}\n')

        if not captcha:
            buttons = driver.find_elements(by='xpath', value="/html/body/div/section/article/div/form/input[@type='submit']")
            if len(buttons) == 1:
                btn_name = buttons[0].get_attribute('name')
                driver.find_element(by='name', value=btn_name).click()
        else:
            # download the captcha image
            image = Image.open(requests.get(captcha_image, stream=True).raw).convert('RGB')
            # Resize to get average color
            image = image.resize((1, 1))
            color = image.getpixel((0, 0))

            # Instantiate an sRGBColor object and convert to lab to check deltas
            color_rgb = sRGBColor(rgb_r=color[0], rgb_g=color[1], rgb_b=color[2], is_upscaled=True)
            color_lab = convert_color(color_rgb, LabColor)

            # Get colors from the buttons
            buttons_dict = {}
            buttons = driver.find_elements(by='xpath', value="/html/body/div/section/article/div/form/input[@type='submit']")
            for btn in buttons:
                # Extract color from the button's background css property
                r, g, b = btn.value_of_css_property("background-color")[4:-1].split(', ')
                btn_rgb = sRGBColor(rgb_r=int(r), rgb_g=int(g), rgb_b=int(b), is_upscaled=True)
                btn_lab = convert_color(btn_rgb, LabColor)

                # get difference of color between button and captcha_image
                delta_e = delta_e_cie1976(btn_lab, color_lab)

                buttons_dict[btn.get_attribute('name')] = delta_e
            closest_button_name = min(buttons_dict, key=buttons_dict.get)

            # click the correct captcha color coded download button
            driver.find_element(by='name', value=closest_button_name).click()


        # wait until file is found
        found = False
        name = None
        time_slept = 0
        while not found:
            if time_slept > 360:
                raise Exception(f'No-Intro {key} zip file not found')

            for f in os.listdir(dir_path):
                if 'No-Intro Love Pack' in f and not f.endswith('.part'):
                    try:
                        zipfile.ZipFile(os.path.join(dir_path, f))
                        name = f
                        found = True
                        break
                    except zipfile.BadZipfile:
                        pass

            # wait 5 seconds
            sleep(5)
            time_slept += 5

        archive_name = 'no-intro.zip' if key == 'standard' else f'no-intro_{key}.zip'
        archive_full = os.path.join(dir_path, archive_name)
        os.rename(os.path.join(dir_path, name), os.path.join(dir_path, archive_full))

        # load & extract zip file, there is currently no way to remove files from zip archive
        orig_archive  = zipfile.ZipFile(os.path.join(dir_path, archive_full), mode='r')
        orig_archive.extractall()
        orig_archive.close()

        #delete unneeded files
        for x in os.listdir(path='./'):
            if re.fullmatch(regex['skipfiles'], x):
                print('SKIPPING: ', x)
                os.remove(x)

        print('\nBuilding new archive ...\n')

        # build new zip archive
        archive = zipfile.ZipFile(os.path.join(dir_path, archive_full), mode='w', compression=zipfile.ZIP_DEFLATED, compresslevel=9)
        for x in os.listdir(path='.'):
            if x.endswith(".dat"):
                print('Adding to Archive: ', x)
                archive.write(x)
                os.remove(x)

        print('\nCreating new clrmamepro datfile ...\n')

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
                tag_datfile, 'url').text = f'https://github.com/hugo19941994/auto-datfile-generator/releases/latest/download/{archive_name}'

            # File tag in XML
            fileName = dat
            fileName = f'{fileName[:-4]}.dat'
            ET.SubElement(tag_datfile, 'file').text = fileName
            print(fileName)

            # Author tag in XML
            ET.SubElement(tag_datfile, 'author').text = 'no-intro.org'

            # Command XML tag
            ET.SubElement(tag_datfile, 'comment').text = '_'

            print()

        archive.close()

        # store clrmamepro XML file
        xmldata = ET.tostring(tag_clrmamepro).decode()
        xml_filename = 'no-intro.xml' if key == 'standard' else f'no-intro_{key}.xml'
        xmlfile = open(xml_filename, 'w')
        xmlfile.write(xmldata)
