from flask import Flask, render_template, request, redirect
from imagekitio import ImageKit
import time
import os
import csv
import pandas as pd
import datetime
from datetime import date
from collections import Counter


app = Flask(__name__)
app.secret_key = "receiptapp"

imagekit = ImageKit(
    private_key='private_h/b5MVHmiK8XHzmyAMqoPdNU9nQ=',
    public_key='public_+q9uqgq/uRYFBCHFay6XUzwoPqc=',
    url_endpoint = 'https://ik.imagekit.io/ydm0adt60h'
)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/categories", methods=['GET', 'POST'])
def categories():

    if request.method == 'POST':
        catname = request.form['catname']
        with open("static/catnames.txt", "a+") as file_object:
            file_object.seek(0)
            data = file_object.read(100)
            if len(data) > 0 :
                file_object.write("\n")
            file_object.write(catname)        
        print(catname)
        return redirect('/categories')
    cats = []
    hrefs = []
    with open('static/catnames.txt') as my_file:
        for line in my_file:
            cats.append(line)
    for i in cats:
        hrefs.append("/handler?cat="+i)
    return render_template('categories.html', length=len(cats), cats=cats, href=hrefs)

@app.route('/handler', methods=['GET'])
def handler():
    title = request.args.get("cat")
    add = "/add?cat={0}".format(title)
    view = "/view?cat={0}".format(title)
    stats = "/stats?cat={0}".format(title)
    return render_template("handler.html", title=title, add=add, view=view, stats=stats)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        cost = request.form['cost']
        name = request.form['name']
        date = request.form['date']
        uploaded_file = request.files['file']
        if uploaded_file.filename != '':
            filename = str(int(time.time()*1000))+"_"+uploaded_file.filename
            uploaded_file.save("upfiles/"+filename)
        
        files = os.listdir('upfiles')

        if filename in files:
            imagekit.upload_file(
                file= open("upfiles/"+filename, "rb"), # required
                file_name= filename, # required
                options= {
                    "use_unique_file_name": False
                }
            )
            os.remove('upfiles/'+filename)
            imagekit_url = imagekit.url({
                        "path": filename,
                        "url_endpoint": "https://ik.imagekit.io/ydm0adt60h/",
                    }
            )
            field_names = ['Name', 'Cost', 'Date', 'URL']
            dictionary= {"Name": name, "Cost": cost, "Date": date, "URL": imagekit_url}
            if "{0}.csv".format(request.args.get("cat")) in os.listdir("static"):
                with open('static/{0}.csv'.format(request.args.get("cat")), 'a') as csv_file:
                    dict_object = csv.DictWriter(csv_file, fieldnames=field_names) 
                    dict_object.writerow(dictionary)
            else:
                with open('static/{0}.csv'.format(request.args.get('cat')), 'w', encoding='UTF8') as f:
                    writer = csv.DictWriter(f, fieldnames=field_names)
                    writer.writeheader()
                    writer.writerow(dictionary)      

            print(imagekit_url)
        return redirect('/handler?cat={0}'.format(request.args.get("cat")))
    cat = request.args.get("cat")
    return render_template('add.html', title=cat)

@app.route('/view', methods=['GET', 'POST'])
def view():
    cat = request.args.get("cat")
    data = pd.read_csv("static/{0}.csv".format(cat))
    names = data['Name'].tolist()
    costs = data['Cost'].tolist()
    dates = data['Date'].tolist()
    urls = data['URL'].tolist()
    return render_template('viewer.html', length=len(names), title=cat, names=names, costs=costs, dates=dates, urls=urls)

@app.route('/stats')
def stats():
    cat = request.args.get('cat')
    data = pd.read_csv("static/{0}.csv".format(cat))
    names = data['Name'].tolist()
    names = list(set([item for items, c in Counter(names).most_common()
                                      for item in [items] * c]))
    costs = data['Cost'].tolist()
    dates = data['Date'].tolist()
    month = date.today().month
    datetime_object = datetime.datetime.strptime(str(month), "%m")
    full_month_name = datetime_object.strftime("%B")
    year = date.today().year
    monthcost = 0
    totalcost = 0
    i_count = 0
    for i in dates:
        if i[-4:] == str(year):
            if int(i[0:2]) == int(month):
                monthcost += costs[i_count]
                totalcost += costs[i_count]
            else:
                totalcost += costs[i_count]
        i_count += 1

    freq = names
    length = len(freq)

    return render_template('stats.html', title=cat, month=full_month_name, monthcost=monthcost, totalcost=totalcost, length=length, freq=freq)

