import zipfile
from datetime import date
from io import StringIO
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


def generate(url, platform, zf):
    games = defaultdict(list)

    dtd_file = StringIO(requests.get("http://www.logiqx.com/Dats/datafile.dtd").text)
    dtd = etree.DTD(dtd_file)

    # Get Saturn supplement
    r = requests.get(url)
    txt = r.text
    for line in txt.splitlines():
        sha256, name, sha1, md5, crc32 = line.split('\t')
        rom_name = name[name.rindex('/') + 1:]
        name = name[name.rfind('/', 0, name.rfind('/')) + 1:name.rindex('/')].replace('/', '\\')
        games[name].append((rom_name, sha1, md5, crc32))

    root = etree.Element('datafile')
    #root.tree.docinfo.public_id = "-//Logiqx//DTD ROM Management Datafile//EN"
    #root.tree.docinfo.system_url = "http://www.logiqx.com/Dats/datafile.dtd"
    header = etree.SubElement(root, 'header')
    name = etree.SubElement(header, 'name')
    name.text = f'Smokemonster - {platform}'
    description = etree.SubElement(header, 'description')
    description.text = f'Smokemonster - {platform} - Supplement ({date.today()})'
    version = etree.SubElement(header, 'version')
    version.text = str(date.today())
    date_xml = etree.SubElement(header, 'date')
    date_xml.text = str(date.today())
    author = etree.SubElement(header, 'author')
    author.text = 'Smokemonster'
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
    version.text = str(date.today())
    name = etree.SubElement(df, 'name')
    name.text = f'Smokemonster - {platform}'
    description = etree.SubElement(df, 'description')
    description.text = f'Smokemonster - {platform}'
    url_xml = etree.SubElement(df, 'url')
    url_xml.text = 'https://github.com/hugo19941994/auto-datfile-generator/releases/download/latest/smdb.zip'
    file_xml = etree.SubElement(df, 'file')
    file_xml.text = f'datfile_{platform.replace(" ", "_").lower()}.dat'
    author_xml = etree.SubElement(df, 'author')
    author_xml.text = 'Smokemonster'
    comment_xml = etree.SubElement(df, 'comment')
    comment_xml.text = '_'

    #print(dtd.validate(root))
    #print(dtd.error_log.filter_from_errors()[0])

zf = zipfile.ZipFile('smdb.zip', 'w')

generate('https://raw.githubusercontent.com/SmokeMonsterPacks/EverDrive-Packs-Lists-Database/master/EverDrive%20Pack%20SMDBs/Saturn%20Redump%20Supplement.txt', 'Saturn', zf)
generate('https://raw.githubusercontent.com/SmokeMonsterPacks/EverDrive-Packs-Lists-Database/master/EverDrive%20Pack%20SMDBs/Dreamcast%20Redump%20Supplement.txt', 'Dreamcast', zf)
generate('https://raw.githubusercontent.com/SmokeMonsterPacks/EverDrive-Packs-Lists-Database/master/EverDrive%20Pack%20SMDBs/PC%20Engine%20CD%20Redump%20Supplement.txt', 'PC Engine CD', zf)
generate('https://raw.githubusercontent.com/SmokeMonsterPacks/EverDrive-Packs-Lists-Database/master/EverDrive%20Pack%20SMDBs/PlayStation%20Redump%20Supplement.txt', 'PlayStation 1', zf)

zf.close()


final_xml = minidom.parseString(etree.tostring(clr_root)).toprettyxml(indent="    ")
with open(f'smdb.xml', 'w') as f:
    f.write(final_xml)
