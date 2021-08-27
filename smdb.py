import zipfile
import os
import shutil
import subprocess
from datetime import date, datetime
from io import StringIO, TextIOWrapper
from xml.dom import minidom
from io import BytesIO
from time import sleep
import xml.etree.ElementTree as ET
from lxml import etree, objectify
from lxml import etree
import re
import requests
from collections import defaultdict


clr_root = etree.Element('clrmamepro')


def generate(txt, platform, txt_date, zf):
    txt_date = txt_date.strftime("%Y-%m-%d %H:%M:%S")
    games = defaultdict(list)

    dtd_file = StringIO(requests.get("http://www.logiqx.com/Dats/datafile.dtd").text)
    dtd = etree.DTD(dtd_file)

    # Get Saturn supplement
    for line in txt:
        # Some have a sixth columen with the rom size
        sha256, name, sha1, md5, crc32 = line.split('\t')[:5]

        rom_name = name[name.find('/', name.find('/') + 1) + 1:].replace('/', '\\')
        name = name[name.find('/') + 1:name.find('/', name.find('/') + 1)].replace('/', '\\')
        games[name].append((rom_name, sha1, md5, crc32))

    root = etree.Element('datafile')
    header = etree.SubElement(root, 'header')
    name = etree.SubElement(header, 'name')
    name.text = platform
    description = etree.SubElement(header, 'description')
    description.text = f'{platform} ({txt_date})'
    version = etree.SubElement(header, 'version')
    version.text = str(txt_date)
    date_xml = etree.SubElement(header, 'date')
    date_xml.text = str(txt_date)
    author = etree.SubElement(header, 'author')
    author.text = 'SmokeMonster'
    homepage = etree.SubElement(header, 'homepage')
    homepage.text = 'https://github.com/SmokeMonsterPacks/EverDrive-Packs-Lists-Database'
    url = etree.SubElement(header, 'url')
    url.text = 'https://github.com/SmokeMonsterPacks/EverDrive-Packs-Lists-Database'

    for game_name, roms in games.items():
        game = etree.SubElement(root, 'game')
        game.set('name', game_name)
        category = etree.SubElement(game, 'category')
        category.text = 'Games'
        description = etree.SubElement(game, 'description')
        description.text = game_name
        for props in roms:
            rom = etree.SubElement(game, 'rom')
            rom.set('name', props[0])
            rom.set('crc', props[3])
            rom.set('md5', props[2])
            rom.set('sha1', props[1])

    etree_str = (etree.tostring(root, encoding="UTF-8",
                         xml_declaration=True,
                         doctype='<!DOCTYPE datafile PUBLIC "-//Logiqx//DTD ROM Management Datafile//EN" "http://www.logiqx.com/Dats/datafile.dtd">'))
    final_xml = minidom.parseString(etree_str).toprettyxml(indent="    ")
    zf.writestr(f'datfile_{platform.replace(" ", "_").lower()}.dat', final_xml)

    # clrmamepro xml
    df = etree.SubElement(clr_root, 'datfile')
    version = etree.SubElement(df, 'version')
    version.text = str(txt_date)
    name = etree.SubElement(df, 'name')
    name.text = platform
    description = etree.SubElement(df, 'description')
    description.text = platform
    url_xml = etree.SubElement(df, 'url')
    url_xml.text = 'https://github.com/hugo19941994/auto-datfile-generator/releases/latest/download/smdb.zip'
    file_xml = etree.SubElement(df, 'file')
    file_xml.text = f'datfile_{platform.replace(" ", "_").lower()}.dat'
    author_xml = etree.SubElement(df, 'author')
    author_xml.text = 'SmokeMonster'
    comment_xml = etree.SubElement(df, 'comment')
    comment_xml.text = '_'

    # Multiple roms in a game is technically invalid, but clrmamepro accepts it
    # print(dtd.validate(root))
    # print(dtd.error_log.filter_from_errors()[0])

"""

r = requests.get('https://github.com/SmokeMonsterPacks/EverDrive-Packs-Lists-Database/archive/master.zip')
zipdata = BytesIO()
zipdata.write(r.content)
archive = zipfile.ZipFile(zipdata)

for f in archive.namelist():
    if f.startswith('EverDrive-Packs-Lists-Database-master/EverDrive Pack SMDBs/') and f.endswith('.txt'):
        file_date = archive.getinfo(f).date_time
        print(file_date)
        name = f.replace('EverDrive-Packs-Lists-Database-master/EverDrive Pack SMDBs/', '').replace('.txt', '')
        with archive.open(f, 'r') as txt:
            txt_file  = TextIOWrapper(txt)
            generate(txt_file, name, zf)


"""

# git log -1 --pretty="format:%ci"

zf = zipfile.ZipFile('smdb.zip', 'w')

shutil.rmtree('./EverDrive-Packs-Lists-Database', ignore_errors=True, onerror=None)
subprocess.call('git clone https://github.com/SmokeMonsterPacks/EverDrive-Packs-Lists-Database.git', shell = True)
folder = './EverDrive-Packs-Lists-Database/EverDrive Pack SMDBs'
for f in os.listdir(folder):
    file_date = subprocess.run(['git','--no-pager', 'log', '-1', '--pretty="format:%ci"', f], capture_output=True, cwd=folder).stdout.decode('utf-8')[8:-2]
    txt_date = datetime.strptime(file_date,'%Y-%m-%d %H:%M:%S %z')
    if '.txt' not in f:
        # manual packs in 7z
        continue
    name = f.replace('.txt', '')
    with open(f'{folder}/{f}') as txt:
        generate(txt, name, txt_date, zf)

zf.close()

final_xml = minidom.parseString(etree.tostring(clr_root)).toprettyxml(indent="    ")
with open(f'smdb.xml', 'w') as f:
    f.write(final_xml)
