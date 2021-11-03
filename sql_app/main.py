from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm import Session
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import time
from datetime import datetime
import re
from .models import Products, Base, Price
from .database import SessionLocal, engine

Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


''' extracting data with selenuim'''


def extracting():
    options = Options()
    options.page_load_strategy = 'eager'

    # id of categories in url of website. it could change by adding new category.
    category_id = [10, 11, 90, 91, 129]

    result = dict()

    def dkprice_to_numbers(dkprice):
        '''gets something like ۱۱۷،۰۰۰ تومان and returns 117000'''
        convert_dict = {u'۱': '1', u'۲': '2', u'۳': '3', u'۴': '4', u'۵': '5',
                        u'۶': '6', u'۷': '7', u'۸': '8', u'۹': '9', u'۰': '0', }
        price = u'۰' + dkprice
        for k in convert_dict.keys():
            price = re.sub(k, convert_dict[k], price)

        price = re.sub('[^0-9]', '', price)
        return int(price)

    '''extracting data for each page'''

    def extracting_data(id):
        driver = webdriver.Firefox(options=options)
        try:
            driver.get(f'https://liateam.ir/category/id= {id}')
        except:
            raise HTTPException(status_code=500)
        time.sleep(2)           # rest to load pagees

        try:
            total_pages = len(                                          # find the number of pages for each category
                driver.find_element(By.CLASS_NAME, 'paginationWrapper').
                find_elements(By.TAG_NAME, "li")) - 2
        except:
            total_pages = 1
        print(f'total page {id}:', total_pages)

        for page in range(1, total_pages + 1):
            print(f' page {id}:', page)
            if total_pages != 1:
                driver.find_element(By.CLASS_NAME, 'paginationWrapper').find_element(
                    By.LINK_TEXT, str(page)).click()
            time.sleep(2)       
            elem = driver.find_elements(
                By.XPATH, "//div[@class='col-6 col-xl-12 col-md-12 col-lg-12 infoHolder']")

            for product in elem:
                try:
                    product_price = product.find_element(
                        By.CLASS_NAME, 'price').text
                    product_price = product_price[0:-5]
                    product_price = dkprice_to_numbers(product_price)
                    product_id = product.find_element(
                        By.TAG_NAME, 'i').get_attribute('id')
                except:
                    continue
                result[f'{product_id}'] = product_price

        driver.close()
        return len(result)

    for id in category_id:
        extracting_data(id)
        print(len(result))
    return result


''' route for averaging extracting data. '''


@app.get("/average/")
def read_users():
    result = extracting()
    sum = 0
    for value in result.values():
        sum += float(value) 
    average = sum / len(result)
    average = "{:.2f}".format(average)
    return {'number of products': len(result), 'average': average}


''' route for record all extracting data in database. '''


@app.get("/record/")
def record(db: Session = Depends(get_db)):
    result = extracting()
    # adding a new product id to the database. 
    for product_id in result.keys():
        database_products = db.query(Products).all()
        check = False
        for products in database_products:
            if product_id == str(products.id_product):
                check = True
                break
        if check is False:
            new_record = Products(id_product=product_id)
            db.add(new_record)
            db.commit()
    # adding all od data to the database
    for product_id, product_price in result.items():
        new_price = Price(price=product_price,
                          date=datetime.now(), id_product=product_id)
        db.add(new_price)
        db.commit()
    return {f'{len(result.items())} data add to the databaes in {datetime.now()}'}
