import os
import re
import xml.etree.ElementTree as ET
import zipfile
from time import sleep

from selenium import webdriver

regex = {
    "date"     : r"[0-9]{8}-[0-9]{6}",
    "name"     : r"(.*?.)( \([0-9]{8}-[0-9]{6}\).dat)"
}

no_intro_type = {
    "standard"     : "standard",
    "parent-clone" : "xml"
}

for key, value in no_intro_type.items():

    # Download no-intro pack using selenium
    dir_path = os.path.dirname(os.path.realpath(__file__))

    options = webdriver.FirefoxOptions()
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.manager.showWhenStarting", False)
    options.set_preference("browser.download.dir", dir_path)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
    options.add_argument  ("-headless")

    service = webdriver.FirefoxService(log_output = "firefox-webdriver.log" , service_args = ["--log", "debug"])

    driver = webdriver.Firefox(service=service, options=options)
    driver.implicitly_wait(10)

    # load website
    driver.get("https://datomatic.no-intro.org")
    print("Loaded no-intro datomatic ...")

    # select "DOWNLOAD"
    driver.find_element(by="xpath", value="/html/body/div/header/nav/ul/li[3]/a").click()

    # select "daily"
    driver.find_element(by="xpath", value="/html/body/div/section/article/table[1]/tbody/tr/td/a[5]").click()

    #set the type of dat file
    if key == "standard" :
        driver.find_element(by="xpath", value="//input[@name='dat_type' and @value='standard']").click()
    if key == "parent-clone" :
        driver.find_element(by="xpath", value="//input[@name='dat_type' and @value='xml']").click()
    print(f"Set dat type to {key} ...")

    # select "Request"
    driver.find_element(by="name", value="daily_day").click()
    sleep(5)

    # select "Download"
    driver.find_element(by="xpath", value="//input[@value='Download']").click()
    print("Waiting for download to complete ...")

    # wait until file is found
    FOUND = False
    NAME = None
    TIME_SLEPT = 0
    while not FOUND:
        if TIME_SLEPT > 900:
            raise FileNotFoundError(f"No-Intro {key} zip file not found, timeout reached")

        for f in os.listdir(dir_path):
            if "No-Intro Love Pack" in f and not f.endswith(".part"):
                try:
                    zipfile.ZipFile(os.path.join(dir_path, f))
                    NAME = f
                    FOUND = True
                    print("No-Intro zip file download completed ...")
                    break
                except zipfile.BadZipfile:
                    pass

        # wait 5 seconds
        sleep(5)
        TIME_SLEPT += 5

    if NAME == None:
        raise FileNotFoundError(f"No-Intro {key} zip file not found, download failed")

    #setup archive path and rename
    archive_name = "no-intro.zip" if key == "standard" else f"no-intro_{key}.zip"
    archive_full = os.path.join(dir_path, archive_name)
    os.rename(os.path.join(dir_path, NAME), os.path.join(dir_path, archive_full))

    # load & extract zip file, there is currently no way to remove files from zip archive
    with zipfile.ZipFile(os.path.join(dir_path, archive_full), mode="r") as orig_archive:
        orig_archive.extractall()
        # delete unneeded files
        os.remove("index.txt")

    print("Building new archive ...")
    with zipfile.ZipFile(os.path.join(dir_path, archive_full), mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for f in os.listdir(dir_path):
            if "No-Intro" in f:
                print("\nAdding No-Intro dats ...")
                os.chdir("./No-Intro")
                for x in os.listdir(path="."):
                    if x.endswith(".dat"):
                        print("Adding to Archive: ", x)
                        archive.write(x)
                        os.remove(x)
                os.chdir("../")
                os.rmdir("./No-Intro")
            if "Non-Redump" in f:
                print("\nAdding No-Intro Non-Redump dats ...")
                os.chdir("./Non-Redump")
                for x in os.listdir(path="."):
                    if x.endswith(".dat"):
                        print("Adding to Archive: ", x)
                        archive.write(x)
                        os.remove(x)
                os.chdir("../")
                os.rmdir("./Non-Redump")
            if "Source Code" in f:
                print("\nAdding No-Intro Source Code dats ...")
                os.chdir("./Source Code")
                for x in os.listdir(path="."):
                    if x.endswith(".dat"):
                        print("Adding to Archive: ", x)
                        archive.write(x)
                        os.remove(x)
                os.chdir("../")
                os.rmdir("./Source Code")
            if "Unofficial" in f:
                print("\nAdding No-Intro Unofficial dats ...")
                os.chdir("./Unofficial")
                for x in os.listdir(path="."):
                    if x.endswith(".dat"):
                        print("Adding to Archive: ", x)
                        archive.write(x)
                        os.remove(x)
                os.chdir("../")
                os.rmdir("./Unofficial")

    print("\nCreating new clrmamepro datfile ...\n")
    # clrmamepro XML file
    tag_clrmamepro = ET.Element("clrmamepro")
    for dat in archive.namelist():
        print(dat)
        # section for this dat in the XML file
        tag_datfile = ET.SubElement(tag_clrmamepro, "datfile")

        # XML version
        dat_date = re.findall(regex["date"], dat)[0]
        ET.SubElement(tag_datfile, "version").text = dat_date
        print(dat_date)

        # XML name & description
        tempName = re.findall(regex["name"], dat)[0][0]
        ET.SubElement(tag_datfile, "name").text = tempName
        ET.SubElement(tag_datfile, "description").text = tempName
        print(tempName)

        # URL tag in XML
        ET.SubElement(tag_datfile, "url").text = f"https://github.com/hugo19941994/auto-datfile-generator/releases/latest/download/{archive_name}"

        # File tag in XML
        fileName = dat
        fileName = f"{fileName[:-4]}.dat"
        ET.SubElement(tag_datfile, "file").text = fileName
        print(fileName)

        # Author tag in XML
        ET.SubElement(tag_datfile, "author").text = "no-intro.org"

        # Command XML tag
        ET.SubElement(tag_datfile, "comment").text = "_"

        print()

    archive.close()

    # store clrmamepro XML file
    xmldata = ET.tostring(tag_clrmamepro).decode()
    xml_filename = "no-intro.xml" if key == "standard" else f"no-intro_{key}.xml"

    with open(xml_filename, "w", encoding="utf-8") as xmlfile:
        xmlfile.write(xmldata)

    print("Finished")
