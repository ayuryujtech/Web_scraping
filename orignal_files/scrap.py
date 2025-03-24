
from email.headerregistry import Address
from unicodedata import name
from bs4 import BeautifulSoup
import re
import requests
import time
import pandas as pd
import numpy as np
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
#html_txt = requests.get('https://www.1mg.com/manufacturer/patanjali-ayurved-limited-74013?pageNumber=2').text
#soup = BeautifulSoup(html_txt,'lxml')
PATH = "/home/arpit/Documents/Documents/ayuryuj/chromedriver"
title = []
Description = []
Manufacturer_Address = []
Manufacturer = []
image_link = []
key_ingredients = []
driver = webdriver.Chrome(PATH)


def scrapper():
    page_source = driver.page_source
    soup = BeautifulSoup(page_source,'lxml')

    print("SCRIPT STARTING")

    link = soup.find_all('div',class_='col-sm-3 col-xs-6')
    for one_link in link:
        one = one_link.a['href']
        mainlink = ("https://www.1mg.com"+one)
        another_link = driver.get(mainlink)
        next_page_source = driver.page_source
        next_soup = BeautifulSoup(next_page_source,'lxml')
        Ptitle = next_soup.find('h1',class_='ProductTitle__product-title___3QMYH').text
        PManufacturer = next_soup.find('div',class_='ProductTitle__manufacturer___sTfon').text
        PDescription = next_soup.find('div',class_='ProductDescription__description-content___A_qCZ').text
        PManufacturer_address = next_soup.find('div',class_='OtcPage__manufacturer-address___3ugdE').text
        images = next_soup.find_all('img', class_ = 'Thumbnail__thumbnail-image-new___3rsF_')
        Pkeys = next_soup.find_all('div',class_='style__title___25vLm')
        images_serializer_str = ""
        Pkey_serializer_str = ""
        for img in images:
            if img.has_attr('src'):
                print(img['src'])
                images_serializer_str = images_serializer_str + ',' + img['src']
        for key in Pkeys:
            print(key.text)
            Pkey_serializer_str = Pkey_serializer_str + ',' + key.text
        title.append(Ptitle)
        Description.append(PDescription)
        Manufacturer.append(PManufacturer)
        Manufacturer_Address.append(PManufacturer_address)
        image_link.append(images_serializer_str)
        key_ingredients.append(Pkey_serializer_str)
        
        #key.append(Pkey)
        #image_link.append(images['src'])


    # link = driver.get(r'https://www.1mg.com/otc/patanjali-ayurveda-dant-kanti-natural-toothpaste-otc501374')
    # page_source = driver.page_source
    # soup = BeautifulSoup(page_source,'lxml')
    # txt = soup.find_all('div',class_='ProductTitle__manufacturer___sTfon')

    # soup.find_all('h1',class_='ProductTitle__product-title___3QMYH')
    # soup.find_all('h1',class_='ProductTitle__manufacturer___sTfon')
    # soup.find_all('div',class_='ProductDescription__description-content___A_qCZ')
    # soup.find_all('div',class_='OtcPage__manufacturer-address___3ugdE')
    # soup.find_all('img',class_='Thumbnail__thumbnail-image-new___3rsF_')

    # soup.find_all('div',class_='ProductHighlights__highlights-text___dc-WQ"')

    # links = soup.find_all("div", {"id": "srchRslt"})
    # key = soup.find_all('div',class_='style__title___25vLm')

def website_scrapper(brand,path, pageNumber):
    for i in range(0,pageNumber):
        link = driver.get(path +'?' + 'pageNumber='+ str(i))
    scrapper()
    df1 = pd.DataFrame({'Title':title,'Description':Description,'Manufacturer':Manufacturer,'Manufacturer_Address':Manufacturer_Address, 'images': image_link, 'key_ingredients':key_ingredients})
    print(df1.head())
    df1.to_csv('./'+ brand + '.csv')


website_scrapper('Patanjali_pvt_ltd','https://www.1mg.com/manufacturer/patanjali-ayurved-limited-74013',6)
