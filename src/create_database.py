import requests
import gzip
from bs4 import BeautifulSoup
import re
import os
import subprocess
import xml.etree.ElementTree as ET
import json
import random
from glob import glob


base = 'https://apkpure.com'
sitemap = 'https://apkpure.com/sitemap.xml'
apk_dest = './data/apk'
xml_dest = './data/xml'
data_dest = './data/smali'
site = requests.get(sitemap)
soup = BeautifulSoup(site.text, 'lxml')


def create_database(N=1):
    apps = [a.text for a in soup.find_all('loc')]
    for app in apps[:N]:
        resp = requests.get(app)
        data = resp.content
        name = re.search('s\/.+\.xml', app).group(0)[2:-4]
        # print(name)
        try:
            with open('./data/apk/%s.apk' % name, 'wb') as fh:
                fh.write(data)
        except:
            os.mkdir('data/apk')


def check_dir(path):
    if(os.path.exists(path) == False):
        os.mkdir(path)


def download(url, dest, name, file_type):
    resp = requests.get(url)
    data = resp.content
    with open('%s/%s.%s' % (dest, name, file_type), 'wb') as fh:
        fh.write(data)


def create_soup(url):
    resp = requests.get(url)
    return BeautifulSoup(resp.text)


def download_decode(app):
    name = re.search('s\/.+\.xml', app).group(0)[2:-4]
    # print(name)

    check_dir(xml_dest)
    download(app, xml_dest, name, 'xml.gz')

    # parse xml to find url of app
    xml = gzip.open('%s/%s.xml.gz' % (xml_dest, name), 'r')
    soup = BeautifulSoup(xml, 'lxml')
    url = soup.find('loc').text

    # find download link
    soup = create_soup(url)
    download_url = base + \
        soup.find('div', {'class': 'ny-down'}).find('a')['href']
    soup = create_soup(download_url)
    download_url = soup.find('a', {'id': 'download_link'})['href']
    check_dir(apk_dest)
    # download apk
    download(download_url, apk_dest, name, 'apk')

    check_dir(data_dest)
    # decode apk
    command = './apktool d -r %s/%s.apk -o %s/%s' % (
        apk_dest, name, data_dest, name)
    print('decoding...')
    os.popen(command)


def get_data(number_of_apps, **kwargs):
    site = create_soup(sitemap)
    # Extract app links
    apps = [a.text for a in site.find_all('loc')][5:]
    random.shuffle(apps)
    count = 0
    check_dir('./data')
    for app in apps:
        if(count >= number_of_apps):
            break
        try:
            download_decode(app)
            count += 1
        except:
            pass
