# Watch Winders Crawler

# IMPORT LIBRARIES
import requests
from bs4 import BeautifulSoup

import time
import re
import random
from datetime import datetime

import os
from os.path import exists

import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains

from googleapiclient.http import MediaFileUpload
from Google import Create_Service
print("imports completed successfully")

# Create directory for local storage
localdirectory = r"C:\winderresults"
if os.path.exists(localdirectory):
    print(f"local directory already exists at {localdirectory}")
    pass
else:
    os.mkdir(localdirectory)
    print(f"folder created at {localdirectory}")

# Setting Brands to be identified - To be automatized later on 
brand = {"name": ["Rapport",
        "Diplomat", 
        "Steinhausen", 
        "Volta", 
        "WOLF", 
        "Billstone"]}
brand_df = pd.DataFrame(data=brand)

# Setting Types to be identified 
itemtype = {"name": ["Watch Box",
            "Watch Winder Safe",
            "Watch WInder Safe",
            "Watch Winder",
            "Watch Zip Case",
            "Watch Roll"]}
itemtype_df = pd.DataFrame(data=itemtype)

# Setting watch count to be identified
watchcount = {"name": ["Single",
            "Double",
            "Triple",
            "Duo",
            "Three",
            "Twelve",
            "Twenty",
            "Module"]}
watchcount_df = pd.DataFrame(data=watchcount)

# Functions
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

def extract_sku(row):
    sku = re.search("\w+\-?\w+$", row)
    if bool(re.search(r'\d',sku[0])):
        return sku[0]
    else:
        return None
print(f"functions loaded")

# watchwindersusa store scraping
print("starting watchwinderusa scraping")
options = webdriver.ChromeOptions()
# options.add_argument("--headless=new")
driver = webdriver.Chrome(options=options)

# Navigate to website
driver.get("https://watchwinderusa.com/shop/")
print("website loaded")

# Scroll to end of the page
# identify an element on the webpage in order to send instructions
page = driver.find_element(By.TAG_NAME, "body")
winders = []
print("scrolling down to load entire page")
while len(winders) < 211: # amount of products to be found
    page.send_keys(Keys.PAGE_DOWN)
    # Extract raw code from page with all items
    html = driver.page_source
    soup = BeautifulSoup(html, features ="lxml")
    # IDENTIFY EACH PRODUCT CARD
    winders = soup.find_all("div", attrs = {"class":"product-wrapper"})
# SCRAPE FROM EACH PRODUCT CARD
time.sleep(2)
usawinders = {}
item = 0
winders = soup.find_all("div", attrs = {"class":"product-wrapper"})
for winder in winders:
    print(f"{item} items scraped")
    if len(winder.find_all("bdi")) == 1: # If only 1 price instance detected found no promotion is recorded
        wprice      = winder.find_all("bdi")[0].get_text()
        wpromoprice = wprice
        wpromotion  = False
        wname       = winder.find_all("h3", attrs ={"class":"wd-entities-title"})[0].get_text()
    else:                                  # If more than one price instance detected found promotion is recorded
        wprice      = winder.find_all("bdi")[1].get_text()
        wpromoprice = winder.find_all("bdi")[0].get_text()
        wpromotion  = True
        wname       = winder.find_all("h3", attrs ={"class":"wd-entities-title"})[0].get_text()
    # Create dictionary to fill dataframe
    usawinders[item] = {"name" : wname,
                        "Price (USD)" : wprice,
                        "Promotion" : wpromotion,
                        "Original Price (USD)" : wpromoprice}
    item+= 1

usawinder_df= pd.DataFrame(usawinders).T
usawinder_df= usawinder_df.drop_duplicates() # From the way the site is loaded, some duplicates may appear.

print(f"watchwindersusa store scraped")

# data cleaning and manipulation
# transform prices into number types to be manipulated
usawinder_df["Original Price (USD)"] = usawinder_df["Original Price (USD)"].apply(lambda x : x.replace("$", ""))
usawinder_df["Original Price (USD)"] = usawinder_df["Original Price (USD)"].apply(lambda x : x.replace(",", ""))
usawinder_df["Original Price (USD)"] = usawinder_df["Original Price (USD)"].astype(float)
# transform prices into number types to be manipulated
usawinder_df["Price (USD)"] = usawinder_df["Price (USD)"].apply(lambda x : x.replace("$", ""))
usawinder_df["Price (USD)"] = usawinder_df["Price (USD)"].apply(lambda x : x.replace(",", ""))
usawinder_df["Price (USD)"] = usawinder_df["Price (USD)"].astype(float)
# calculate discount percentage
usawinder_df["Discount"]= usawinder_df.apply(lambda x : abs(round((x["Price (USD)"]/ x["Original Price (USD)"])-1, 2)) if x["Promotion"] == True else 0, axis=1)

# apply cleaning and categorizing functions
usawinder_df["brand"] = usawinder_df["name"].apply(identify_brand)
usawinder_df["brand"] = usawinder_df["brand"].replace(["Wolf"] , "WOLF") # Some names are not standardized, hardcoding required

usawinder_df["itemtype"] = usawinder_df["name"].apply(identify_itemtype)
usawinder_df["itemtype"] = usawinder_df["itemtype"].replace(["Watch WInder Safe"] , "Watch Winder Safe") # Some names are not standardized, hardcoding required

# transform watch count into number types for better manipulation
usawinder_df["watch_count"] = usawinder_df["name"].apply(identify_watchcount)
usawinder_df["watch_count"] = usawinder_df["watch_count"].replace(["Single", "Module"] , 1)
usawinder_df["watch_count"] = usawinder_df["watch_count"].replace(["Double", "Duo"] , 2)
usawinder_df["watch_count"] = usawinder_df["watch_count"].replace(["Three", "Triple"] , 3)
usawinder_df["watch_count"] = usawinder_df["watch_count"].replace(["Twelve"] , 12)
usawinder_df["watch_count"] = usawinder_df["watch_count"].replace(["Twenty"] , 20)

# extract sku code from items
usawinder_df["SKU"] = usawinder_df["name"].apply(extract_sku)
usawinder_df.reset_index(drop=True, inplace=True)
print(f"data cleaning and transformation complete")

# Wolf Store Scraping
print(f"wolf1834 store scraping")
result = None
while result is None:
    try:
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless=new")
        driver = webdriver.Chrome(options=options)
        # Navigate to website
        driver.get("https://www.wolf1834.com/")
        print("website loaded")
        try:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id=\"html-body\"]/div[3]/div[2]/div/div[2]/div[2]/div[2]/div[2]/button"))).click()
        except:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id=\"html-body\"]/div[4]/div[2]/div/div[2]/div[2]/div[2]/div[2]/button"))).click()
        print("popup bypassed")
        # previous waiting strategies to deal with popup
        # time.sleep(10)
        # wait = WebDriverWait(driver, 15)
        # wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id=\"html-body\"]/div[4]/div[2]/div/div[2]/div[2]/div[2]/div[2]/button").click()))
        # button = driver.find_element(By.XPATH, "//*[@id=\"html-body\"]/div[3]/div[2]/div/div[2]/div[2]/div[2]/div[2]/button/span")
        # button.click()
        # selecting USD currency
        element_to_hover_over = driver.find_element(By.XPATH, "//*[@id=\"switcher-store-trigger\"]")
        hover = ActionChains(driver).move_to_element(element_to_hover_over)
        hover.perform()
        button2 = driver.find_element(By.XPATH, "//*[@id=\"switcher-store\"]/div/ul/li[1]/a/strong/span")
        button2.click()
        print("USD currency selected")
        result = 1
    except:
        print("unable to bypass popup, retrying...")
        pass

# scraping each item page, using SKU codes to search
print("beginning individual item search")
item = 0
scraped = {}
wolfwinder_df = usawinder_df[usawinder_df["brand"] == "WOLF"]
for sku in wolfwinder_df["SKU"]:
        try:
            searchbar = driver.find_element(By.XPATH, "//*[@id=\"search\"]")
            searchbar.clear()
            searchbar.send_keys(f"{sku}")
            sendsearch = driver.find_element(By.XPATH, "//*[@id=\"search_mini_form\"]/div[2]/button")
            sendsearch.click()
            time.sleep(1)
            searchresult = driver.find_element(By.XPATH, "//*[@id=\"list-ee2741f898fb958d170ce6d625648025\"]/ol/li/div")
            searchresult.click()
            time.sleep(1)
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            # IDENTIFY EACH PRODUCT CARD
            price_box = soup.find_all("div", attrs = {"class":"product-info-price"}) # locate price container for item
            # If only 1 price instance detected found no promotion is recorded
            if len(price_box[0].find_all("span", attrs = {"class":"price"})) == 1:    
                itemprice = soup.find_all("span", attrs = {"class":"price"})[0].get_text()
                itempromoprice = itemprice
                itempromotion = False
            # If more than one price instance detected found promotion is recorded
            else:                                                                    
                itemprice = soup.find_all("span", attrs = {"class":"price"})[1].get_text()
                itempromoprice = soup.find_all("span", attrs = {"class":"price"})[0].get_text()
                itempromotion = True

            itemprice   = soup.find_all("span", attrs = {"class":"price"})[0].get_text()
            itemname    = soup.find_all("span", attrs = {"class":"base"})[0].get_text()
            itemcolor   = soup.find_all("span", attrs = {"class":"swatch-attribute-selected-option"})[0].get_text()
            stock       = soup.find_all("span", attrs = {"class":"swatch-attribute-outofstock"})[0].get("style")
            itemsku     = sku

            # CHECK IF OUT OF STOCK
            if stock == "":
                instock = False
            else:
                instock = True

            scraped[item] = ({"Supplier Name"               : itemname,
                            "Supplier Price (USD)"          : itemprice,
                            "Supplier Promotion"            : itempromotion,
                            "Supplier Original Price (USD)" : itempromoprice,
                            "Color"                         : itemcolor,
                            "SKU"                           : itemsku,
                            "In Stock"                      : instock})       
            item+= 1
            print(f"scraping item {sku}")
        # if no item found to be clickable, sku is recorded with blank stats
        except:
            print(f"{sku} code not found in supplier store")
            itemprice =         "0"
            itempromotion =     False
            itempromoprice =    "0"
            itemname =          "N/A"
            itemcolor =         "N/A"
            itemsku =           sku
            instock =           "N/A"
            scraped[item] = ({"Supplier Name"               : itemname,
                            "Supplier Price (USD)"          : itemprice,
                            "Supplier Promotion"            : itempromotion,
                            "Supplier Original Price (USD)" : itempromoprice,
                            "Color"                         : itemcolor,
                            "SKU"                           : itemsku,
                            "In Stock"                      : instock})
            item+= 1
            
wolfscrape = pd.DataFrame(scraped).T

# data cleaning and manipulation
# transform prices into number types to be manipulated
wolfscrape["Supplier Original Price (USD)"] = wolfscrape["Supplier Original Price (USD)"].apply(lambda x : x.replace("$", ""))
wolfscrape["Supplier Original Price (USD)"]= wolfscrape["Supplier Original Price (USD)"].apply(lambda x : x.replace(",", ""))
wolfscrape["Supplier Original Price (USD)"]= wolfscrape["Supplier Original Price (USD)"].astype(float)
# transform prices into number types to be manipulated
wolfscrape["Supplier Price (USD)"] = wolfscrape["Supplier Price (USD)"].apply(lambda x : x.replace("$", ""))
wolfscrape["Supplier Price (USD)"]= wolfscrape["Supplier Price (USD)"].apply(lambda x : x.replace(",", ""))
wolfscrape["Supplier Price (USD)"]= wolfscrape["Supplier Price (USD)"].astype(float)
# calculate discount percentage
wolfscrape["Supplier Discount"]= wolfscrape.apply(lambda x: abs(round((x["Supplier Price (USD)"]/ x["Supplier Original Price (USD)"])-1, 2)) if x["Supplier Promotion"] == True else 0, axis=1)


# save merged table into local directory
fullwinder_df = usawinder_df.merge(wolfscrape, how="outer", on= ["SKU"])
fullwinder_df.to_csv("C:\winderresults\watchwinders.csv")
print(f"file saved in local directory: {localdirectory}")

# creating historic data
fullwinder_df_history = fullwinder_df.copy()
fullwinder_df_history["date"] = datetime.today().strftime("%Y_%m_%d_%H_%M_%S")
if os.path.exists("C:\winderresults\watchwindershistory.csv"):
    history_df = pd.read_csv("C:\winderresults\watchwindershistory.csv", index_col=None)
    end_fullwinder_df_history = pd.concat([history_df, fullwinder_df_history])
    end_fullwinder_df_history = end_fullwinder_df_history.reset_index(drop=True)
    end_fullwinder_df_history.to_csv("C:\winderresults\watchwindershistory.csv")
else:
    fullwinder_df_history.to_csv("C:\winderresults\watchwindershistory.csv")
print(f"historic file saved in local directory: {localdirectory}")


# USE GOOGLE API TO CREATE SHEETS FILE
print(f"uploading file to goole sheets directory")
client_secret_file = r"C:\Users\carlo\Documents\Ironhack\Mini Project\own projects\WinderCrawler\client_secret_file.json"
api_name = "drive"
api_version = "v3"
scopes = ["https://www.googleapis.com/auth/drive"]
service = Create_Service(client_secret_file, api_name, api_version, scopes)

folder_id =     "1kUjdUIyKKxL0uFnNxVAO2KvuaOyLfmBt"

file_names =    ["C:\winderresults\watchwinders.csv", "C:\winderresults\watchwindershistory.csv"]
mime_types =    ["text/csv", "text/csv"]

for file_name, mime_type in zip(file_names, mime_types):
    file_metadata = {"name"         : os.path.basename(file_name).replace(".csv", "_"f"{datetime.today().strftime('%Y_%m_%d_%H_%M_%S')}"),
                    "mimeType"      : "application/vnd.google-apps.spreadsheet",
                    "parents"       : [folder_id]}
    media = MediaFileUpload(f"{file_name}", mimetype = mime_type )
    service.files().create(
        body= file_metadata,
        media_body=media,
        fields="id"
    ).execute()
print(f"files successfully uploaded to google drive")
