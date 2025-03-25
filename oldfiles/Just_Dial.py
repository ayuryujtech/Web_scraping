from bs4 import BeautifulSoup
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
PATH = r'C:\Users\khush\OneDrive\Documents\Data\chromedriver_win32\chromedriver.exe'
driver = webdriver.Chrome(PATH)
link = driver.get(r'https://www.justdial.com/Delhi/Ayurvedic-Doctors/nct-10029616')
page_source = driver.page_source
soup = BeautifulSoup(page_source,'lxml')
stores = soup.find_all('li', class_ = 'cntanr')
lab_names = []
Ratings = []
Availavibility = []
Address = []
for store in stores:
    store_name= store.find('span',class_ = 'lng_cont_name').text 
    rating = store.find('span',class_ = 'green-box').text
    timings = store.find('span',class_ = 'distnctxt rsrtopn-1').text
    Add = store.find('p',class_ = 'address-info tme_adrssec').span.text.replace(' ','')
    co = store.find_all('p',class_ = 'contact-info')
    for numbers in co:
        num = numbers.span.a.b
        print(num)
    #print(timings)
    #print(store_name)
    #print(rating)
    lab_names.append(store_name.replace(' ',''))
    Ratings.append(rating)
    Availavibility.append(timings)
    Address.append(Add)
#print(lab_names)
#print(Ratings)
#print(Availavibility)
#print(Address)
