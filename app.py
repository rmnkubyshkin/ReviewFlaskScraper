import pandas as pd
from flask import Flask, render_template, request
from flask_cors import cross_origin
import requests
import mongo_db
from bs4 import BeautifulSoup
from urllib.request import urlopen as url_request

app = Flask(__name__)


def get_search_substring():
    return str(request.form['content'].replace(" ", ""))


def create_full_searching_string(site_address):
    site_address_prepared_for_search = site_address + "/search?q="
    full_searching_string = site_address_prepared_for_search + get_search_substring()
    return full_searching_string


def read_page(url):
    client = url_request(url)
    page = client.read()
    client.close()
    return page


def prepare_link_for_parsing(link):
    product_request = requests.get(link)
    product_request.encoding = 'utf-8'
    return BeautifulSoup(product_request.text, "html.parser")


def save_to_csv(summary_product_data):
    filename = get_search_substring() + ".csv"
    headers = "Product, Customer Name, Rating, Heading, Comment \n"
    data_file = pd.DataFrame(summary_product_data)
    data_file.to_csv(filename, index=False, header=headers)


@app.route('/', methods=['GET'])
@cross_origin()
def home_page():
    return render_template("index.html")


@app.route('/review', methods=['POST', 'GET'])
@cross_origin()
def index():
    summary_product_data = []
    site_address = "https://www.flipkart.com"

    full_searching_string = create_full_searching_string(site_address)
    prepared_page_for_parsing = BeautifulSoup(read_page(full_searching_string), "html.parser")
    main_cards_from_page = prepared_page_for_parsing.findAll("div", {"class": "_1AtVbE col-12-12"})
    del main_cards_from_page[0:3]
    selected_card_product = main_cards_from_page[0]
    product_link = site_address + selected_card_product.div.div.div.a['href']

    if request.method == 'POST':
        try:
            database = mongo_db.auth_to_mongo_db()
            collection = mongo_db.create_collection(database)

            comments_from_card = prepare_link_for_parsing(product_link).find_all('div', {'class': "_16PBlm"})
            for single_comment in comments_from_card:
                try:
                    name = single_comment.div.div.find_all('p', {'class': '_2sc7ZR _2V5EHH'})[0].text
                except Exception as e:
                    name = 'No Name'
                    print('Caught this error: ' + repr(e))

                try:
                    rating = single_comment.div.div.div.div.text
                except Exception as e:
                    rating = 'No Rating'
                    print('Caught this error: ' + repr(e))

                try:
                    header = single_comment.div.div.div.p.text
                except Exception as e:
                    header = 'No Comment Heading'
                    print('Caught this error: ' + repr(e))

                try:
                    text = (single_comment.div.div.find_all('div', {'class': ''}))
                    text = text[0].div.text
                except Exception as e:
                    text = "No text"
                    print("Exception while creating dictionary: ", e)

                product_data = {"Product": get_search_substring(),
                                "Name": name,
                                "Rating": rating,
                                "CommentHead": header,
                                "Comment": text
                                }
                mongo_db.insert_into_collection(collection, product_data)
                summary_product_data.append(product_data)

            save_to_csv(summary_product_data)
            return render_template('results.html', reviews=summary_product_data[0:(len(summary_product_data)-1)])

        except Exception as e:
            print('The Exception message is: ', e)
            return 'something is wrong'

    else:
        return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)
