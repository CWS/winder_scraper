

# IMPORT LIBRARIES
import requests
from bs4 import BeautifulSoup
import pandas as pd
pd.set_option("max_colwidth", None)
import time
import re
import random
from datetime import datetime
import os
from os.path import exists
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains

# Create directory for local storage
if os.path.exists("C:\winderresults\watchwindershistory.csv"):
    pass
else:
    local_storage = r"C:\winderresults"
    os.mkdir(local_storage)
    print("Imports completed successfully")

# Setting Brands to be identifyed - To be automatized later on
brand = {"name": ["Rapport","Diplomat", "Steinhausen", "Volta", "WOLF", "Billstone"]}
brand_df = pd.DataFrame(data=brand)
# Setting Types to be identifyed 
itemtype = {"name": ["Watch Box","Watch Winder Safe","Watch WInder Safe", "Watch Winder", "Watch Zip Case", "Watch Roll"]}
itemtype_df = pd.DataFrame(data=itemtype)
# Setting watch count to be identifyed
watchcount = {"name": ["Single","Double","Triple","Duo","Three", "Twelve", "Twenty", "Module"]}
watchcount_df = pd.DataFrame(data=watchcount)

def identify_brand(row):
    try:
        brand2 = re.search("(wolf)", row, re.IGNORECASE)
        return brand2[0]
    except:
        for brand in brand_df["name"]:
            if brand in row:
                return brand
        
def identify_itemtype(row):
    for itemtype in itemtype_df["name"]:
        if itemtype in row:
            return itemtype
        
def identify_watchcount(row):
    try:
        count = re.search(r"\b\d{1,2}\b", row)
        return count[0]
    except:
        for watchcount in watchcount_df["name"]:
            if watchcount in row:
                return watchcount

def identify_storage(row):
    for store in storage_df["name"]:
        if store in row:
            return store

def extract_sku(row):
    sku = re.search("\w+\-?\w+$", row)
    if bool(re.search(r'\d',sku[0])):
        return sku[0]
    else:
        return None
print(f"Functions Loaded")

# WatchWindersUSA Store Scraping
print("Starting USAWINDER Scraping")
options = webdriver.ChromeOptions()
# options.add_argument("--headless=new")
driver = webdriver.Chrome(options=options)
# Navigate to website
driver.get("https://watchwinderusa.com/shop/")
print("Website loaded")
# identify an element on the webpage in order to send instructions
page = driver.find_element(By.TAG_NAME, "body")
# Scroll to end of the page
# Extract raw code from page with all items
html = driver.page_source
# Gather information from page after all items have been leaded
soup = BeautifulSoup(html)
# IDENTIFY EACH PRODUCT CARD
winders = soup.find_all("div", attrs = {"class":"product-wrapper"})
# SCRAPE FROM EACH PRODUCT CARD
usawinders = {}
item = 0
for winder in winders:
    print(f"Identifying Item {item}")
    if len(winder.find_all("bdi")) == 1:
        wprice = winder.find_all("bdi")[0].get_text()
        wpromoprice = wprice
        wpromotion = False
    else:
        wprice = winder.find_all("bdi")[1].get_text()
        wpromoprice = winder.find_all("bdi")[0].get_text()
        wpromotion = True
    wname = winder.find_all("h3", attrs ={"class":"wd-entities-title"})[0].get_text()
    usawinders[item] = {"name" : wname,
                        "Price (USD)" : wprice,
                        "Promotion" : wpromotion,
                        "Original Price (USD)" : wpromoprice}
    item+= 1
usawinder_df= pd.DataFrame(usawinders).T
usawinder_df= usawinder_df.drop_duplicates()

print(f"USAWINDERS store scraped")
usawinder_df.to_csv(r"C:\winderresults\test.csv")


usawinder_df["SKU"] = usawinder_df["name"].apply(extract_sku)



usawinder_df.reset_index(drop=True, inplace=True)
print(f"Cleaning")

# Wolf Store Scraping
print(f"Wolf Start")
result = None
while result is None:
    try:
        wolfwinder_df = usawinder_df[usawinder_df["brand"] == "WOLF"]
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless=new")
        driver = webdriver.Chrome(options=options)
        # Navigate to website
        driver.get("https://www.wolf1834.com/")
        print("Website loaded")
        time.sleep(2)
        # wait = WebDriverWait(driver, 1)
        # element = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id=\"html-body\"]/div[4]/div[2]/div/div[2]/div[2]/div[2]/div[2]/button")))
        button = driver.find_element(By.XPATH, "//*[@id=\"html-body\"]/div[3]/div[2]/div/div[2]/div[2]/div[2]/div[2]/button/span")
        print("Popup Found")
        button.click()
        print("Popup bypassed")
        element_to_hover_over = driver.find_element(By.XPATH, "//*[@id=\"switcher-store-trigger\"]")
        hover = ActionChains(driver).move_to_element(element_to_hover_over)
        hover.perform()
        button2 = driver.find_element(By.XPATH, "//*[@id=\"switcher-store\"]/div/ul/li[1]/a/strong/span")
        button2.click()
        result = 1
    except:
        pass

item = 0
scraped = {}
for sku in wolfwinder_df["SKU"]:
    try:
        searchbar = driver.find_element(By.XPATH, "//*[@id=\"search\"]")
        searchbar.clear()
        searchbar.send_keys(f"{sku}")
        sendsearch = driver.find_element(By.XPATH, "//*[@id=\"search_mini_form\"]/div[2]/button")
        sendsearch.click()
        searchresult = driver.find_element(By.XPATH, "//*[@id=\"list-ee2741f898fb958d170ce6d625648025\"]/ol/li/div")
        searchresult.click()
        time.sleep(1)
        page = driver.find_element(By.TAG_NAME, "body")
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        # IDENTIFY EACH PRODUCT CARD
        if len(soup.find_all("span", attrs = {"class":"price"})) == 7:
            itemprice = soup.find_all("span", attrs = {"class":"price"})[0].get_text()
            itempromoprice = itemprice
            itempromotion = False
        else:
            itemprice = soup.find_all("span", attrs = {"class":"price"})[1].get_text()
            itempromoprice = soup.find_all("span", attrs = {"class":"price"})[0].get_text()
            itempromotion = True
        itemprice = soup.find_all("span", attrs = {"class":"price"})[0].get_text()
        itemname = soup.find_all("span", attrs = {"class":"base"})[0].get_text()
        itemcolor = soup.find_all("span", attrs = {"class":"swatch-attribute-selected-option"})[0].get_text()
        stock = soup.find_all("span", attrs = {"class":"swatch-attribute-outofstock"})[0].get("style")
        itemsku = sku
        # CHECK IF OUT OF STOCK
        if stock == "":
            instock = False
        else:
            instock = True

        scraped[item] = ({"Supplier Name" : itemname,
                        "Supplier Price (USD)" : itemprice,
                        "Supplier Promotion" : itempromotion,
                        "Supplier Original Price (USD)" : itempromoprice,
                        "Color": itemcolor,
                        "SKU" : itemsku,
                        "In Stock": instock})
        item+= 1
        print(f"Scraping item {sku}")
    except:
        itemprice = "0"
        itempromotion = False
        itempromoprice = "0"
        itemname = "N/A"
        itemcolor = "N/A"
        itemsku = sku
        instock = "N/A"
        scraped[item] = ({"Supplier Name" : itemname,
                        "Supplier Price (USD)" : itemprice,
                        "Supplier Promotion" : itempromotion,
                        "Supplier Original Price (USD)" : itempromoprice,
                        "Color": itemcolor,
                        "SKU" : itemsku,
                        "In Stock": instock})
        item+= 1
        print(f"Scraping item {sku}")
wolfscrape = pd.DataFrame(scraped).T

wolfscrape["Supplier Original Price (USD)"] = wolfscrape["Supplier Original Price (USD)"].apply(lambda x : x.replace("$", ""))
wolfscrape["Supplier Original Price (USD)"]= wolfscrape["Supplier Original Price (USD)"].apply(lambda x : x.replace(",", ""))
wolfscrape["Supplier Original Price (USD)"]= wolfscrape["Supplier Original Price (USD)"].astype(float)
wolfscrape["Supplier Price (USD)"] = wolfscrape["Supplier Price (USD)"].apply(lambda x : x.replace("$", ""))
wolfscrape["Supplier Price (USD)"]= wolfscrape["Supplier Price (USD)"].apply(lambda x : x.replace(",", ""))
wolfscrape["Supplier Price (USD)"]= wolfscrape["Supplier Price (USD)"].astype(float)

wolfscrape["Supplier Discount"]= wolfscrape.apply(lambda x: abs(round((x["Supplier Price (USD)"]/ x["Supplier Original Price (USD)"])-1, 2)) if x["Supplier Promotion"] == True else 0, axis=1)



fullwinder_df = usawinder_df.merge(wolfscrape, how="outer", on= ["SKU"])
fullwinder_df.to_csv("C:\winderresults\watchwinders.csv")
print(f"File Saved")


fullwinder_df_history = fullwinder_df.copy()
fullwinder_df_history["date"] = datetime.today().strftime("%Y_%m_%d_%H_%M_%S")
if os.path.exists("C:\winderresults\watchwindershistory.csv"):
    history_df = pd.read_csv("C:\winderresults\watchwindershistory.csv")
    end_fullwinder_df_history = pd.concat([history_df, fullwinder_df_history])
    end_fullwinder_df_history = end_fullwinder_df_history.reset_index(drop=True)
    end_fullwinder_df_history.to_csv("C:\winderresults\watchwindershistory.csv")
else:
    fullwinder_df_history.to_csv("C:\winderresults\watchwindershistory.csv")
print(f"Historic File Saved")


# USE GOOGLE API TO CREATE SHEETS FILE

import os
from googleapiclient.http import MediaFileUpload
from Google import Create_Service

print(f"Uploading to GoogleSheets")
client_secret_file = r"C:\Users\carlo\Documents\Ironhack\Mini Project\own projects\WinderCrawler\client_secret_file.json"
api_name = "drive"
api_version = "v3"
scopes = ["https://www.googleapis.com/auth/drive"]
service = Create_Service(client_secret_file, api_name, api_version, scopes)

folder_id = "1kUjdUIyKKxL0uFnNxVAO2KvuaOyLfmBt"

file_names = ["C:\winderresults\watchwinders.csv", "C:\winderresults\watchwindershistory.csv"]
mime_types = ["text/csv", "text/csv"]

for file_name, mime_type in zip(file_names, mime_types):
    file_metadata = {
        "name" : os.path.basename(file_name).replace(".csv", "_"f"{datetime.today().strftime('%Y_%m_%d_%H_%M_%S')}"),
        "mimeType": "application/vnd.google-apps.spreadsheet",
        "parents" : [folder_id]
    }

    media = MediaFileUpload(f"{file_name}", mimetype = mime_type )

    service.files().create(
        body= file_metadata,
        media_body=media,
        fields="id"
    ).execute()
print(f"Upload Successful")
