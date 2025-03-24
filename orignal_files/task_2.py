from email.headerregistry import Address
from unicodedata import name
from bs4 import BeautifulSoup
from matplotlib.pyplot import inferno
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
Doctors_Name = []
Address = []
Phone_No = []
Email = []
City = []
html_txt = requests.get('https://www.jiva.com/treatment/clinic').text
soup = BeautifulSoup(html_txt,'lxml') 
part1 = soup.find_all('div',class_ = 'inner-bx')
for info in part1:
    name = info.find('div',class_ = 'detail').h4.text
    Add = info.find('div',class_ = 'top-area').p.text
    Phone = info.find('p',class_ = 'cl').a.text
    email = info.find('p',class_ = 'mail').a.text
    city = info.find('div',class_ = 'top-area').h3.text
    Doctors_Name.append(name)
    Address.append(Add)
    Phone_No.append(Phone)
    Email.append(email)
    City.append(city)
#print(City)
df = pd.DataFrame({'Doctors_Name':Doctors_Name,'City':City,'Phone_No':Phone_No,'Email':Email})
df.head()
df = df.sort_values(by=['City'])
df.to_csv(r'C:\Users\khush\OneDrive\Documents\csvfiles\Task2.csv',index=False)
