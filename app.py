from flask import Flask, render_template
import pandas as pd
import json

app = Flask(__name__)
username = 'javiermilei'


@app.route('/line')

def line():
    df = pd.read_csv(f'/home/pepe/Documents/ig_scrape_definitive/{username}_mixed_data_line.csv')
    labels = df['Date'].tolist()
    values = df['ratio2'].tolist()

    labels_json = json.dumps(labels)
    values_json = json.dumps(values)

    return render_template('line.html', labels_json=labels_json, values_json=values_json)


@app.route('/bar')
def index():
    # Read the CSV file into a DataFrame
    df = pd.read_csv(f'/home/pepe/Documents/ig_scrape_definitive/{username}_mixed_data_bar.csv')  # Replace 'your_data.csv' with your actual CSV file name
    #print(df)
    # Prepare data for Chart.js
    
    labels = df['Date'].tolist()
    values = df['RelativeRatio'].tolist()

    # Convert lists to JSON
    labels_json = json.dumps(labels)
    values_json = json.dumps(values)

    print(values_json)
    return render_template('bar.html', labels_json=labels_json, values_json=values_json)

@app.route('/')
def main():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5002)


