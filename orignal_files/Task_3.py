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
Doctors_Name = []
Address = []
Phone_No = []
Email = []
Qualification = []
information = []
html_txt = requests.get('https://www.indmedica.com/directory.php?directory=doctor&catid=45&num=10&start=1').text
soup = BeautifulSoup(html_txt,'html.parser')
infoOdd = soup.find_all('tr',class_ = 'oddrow')   #Odd rows
infoEven = soup.find_all('tr',class_ = 'evenrow')  #Even rows
for more_info in infoEven:
    more = more_info.td.a['href']
    link = ("https://www.indmedica.com" + more)
    next_html = requests.get(link).text
    next_soup = BeautifulSoup(next_html,'html.parser')
    main = next_soup.find('div',class_ = 'maincolumn')
    name=main.find('h4').text
    Doctors_Name.append(name)
    otherInfo=main.find_all('p')
    phone_No=""
    qualification=""
    address=""
    speciality=""
    for info in otherInfo:
        infoKey=info.text.split(":")[0]
        if(infoKey=="Qualifications"):
            qualification=info.text
        elif(infoKey=="Speciality"):
            speciality=info.text
        elif(infoKey=="Address (Business)"):
            address=info.text
        elif(infoKey=="Phone"):
            phone_No=info.text
    Qualification.append(qualification)
    Address.append(address)
    information.append(speciality)
    Phone_No.append(phone_No)


for more_info in infoOdd:
    more = more_info.td.a['href']
    link = ("https://www.indmedica.com" + more)
    next_html = requests.get(link).text
    next_soup = BeautifulSoup(next_html,'html.parser')
    main = next_soup.find('div',class_ = 'maincolumn')
    name=main.find('h4').text
    Doctors_Name.append(name)
    otherInfo=main.find_all('p')
    phone_No=""
    qualification=""
    address=""
    speciality=""
    for info in otherInfo:
        infoKey=info.text.split(":")[0]
        if(infoKey=="Qualifications"):
            qualification=info.text
        elif(infoKey=="Speciality"):
            speciality=info.text
        elif(infoKey=="Address (Business)"):
            address=info.text
        elif(infoKey=="Phone"):
            phone_No=info.text
    Qualification.append(qualification)
    Address.append(address)
    information.append(speciality)
    Phone_No.append(phone_No)
#print(Address)
df1 = pd.DataFrame({'Name':Doctors_Name,'Qualification':Qualification,'Speciality':information,'Address':Address,'Phone_No':Phone_No})
df1.head(2)
