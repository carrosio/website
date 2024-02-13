from flask import Flask, render_template
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import seaborn as sns
import pandas as pd
from datetime import datetime
from pandas.plotting import register_matplotlib_converters
import os

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
app = Flask(__name__, template_folder=template_dir)

# Configuration
activate_filter_date = False
activate_href_filter = False
resample_var = 'm'
general_start_date = '2023-11'
general_end_date = '2028'

usernames = ['javiermilei']

# Function to plot daily comments/likes ratio
def load_and_preprocess_data(username):
    df = pd.read_csv(f"data/{username}.csv")
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    return df

def apply_general_datetime_filter(df, general_timeframe):
    if general_timeframe:
        start_date, end_date = general_timeframe
        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]
    return df

def apply_user_datetime_filter(df, activate_filter_date, timeframe, username):
    if activate_filter_date and timeframe:
        start_date, end_date = timeframe.get(username, (None, None))
        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]
    return df

def apply_href_filter(df, activate_href_filter):
    if activate_href_filter:
        df = df[~df['Href'].str.contains("/reel/")]
    return df

def resample_and_fill_missing(df, resample_type):
    df_resampled = df.resample(resample_type).last().ffill()
    return df_resampled

def calculate_ratio(df_resampled):
    df_resampled['Ratio'] = ((df_resampled['Comments'] / (df_resampled['Likes'] + df_resampled['Comments']) * 100) * -1)
    december_ratio = df_resampled.loc[df_resampled.index.month == 12, 'Ratio'].values[0]
    df_resampled['RelativeRatio'] = ((df_resampled['Ratio'] / december_ratio) * 100 )
    return df_resampled

def plot_ratio_bars(df_resampled, color, username):
    plt.bar(df_resampled.index[1:], df_resampled['RelativeRatio'][1:], color=color, label=username, alpha=1, width=25)

def customize_plot_appearance(date_range):
    plt.xticks(date_range, [month.strftime('%B %Y') for month in date_range], rotation=90)

def plot_comments_likes_ratio(username, color, resample_type, timeframe=None, activate_filter_date=False,
                               general_timeframe=None, activate_href_filter=False, vertical_lines=None, size_line=1):
    df = load_and_preprocess_data(username)
    df = apply_general_datetime_filter(df, general_timeframe)
    df = apply_user_datetime_filter(df, activate_filter_date, timeframe, username)
    df = apply_href_filter(df, activate_href_filter)

    df_resampled = resample_and_fill_missing(df, resample_type)
    df_resampled = calculate_ratio(df_resampled)

    plt.figure(figsize=(16, 10))
    plot_ratio_bars(df_resampled, color, username)

    date_range = pd.date_range(start=df_resampled.index[1].replace(tzinfo=None), 
                           end=datetime(2025, 7, 14).replace(tzinfo=None), freq='M')
    customize_plot_appearance(date_range)

    return df_resampled

# Set seaborn style
sns.set_style("whitegrid")

# Set a larger figure size
plt.figure(figsize=(16, 10))

# Usernames and their respective timeframes
user_timeframes = {'javiermilei': ('2023-12-10', '2028'), 'alferdezok': ('2019-12-10', '2023-12-10')}
general_timeframe = (general_start_date, general_end_date)

# Create an empty DataFrame to store the mixed data
mixed_df = pd.DataFrame()

# Plot for each user and update the mixed DataFrame
for username, color in zip(usernames, sns.color_palette("tab10", n_colors=len(usernames))):
    user_data = plot_comments_likes_ratio(username, color, resample_var, timeframe=user_timeframes,
                                           activate_filter_date=activate_filter_date,
                                           general_timeframe=general_timeframe,
                                           activate_href_filter=activate_href_filter)
    mixed_df = pd.concat([mixed_df, user_data], axis=1)

# Customize x-axis ticks with month names
plt.xticks(rotation=90)

# Calculate the average line
mixed_df['Average'] = mixed_df.filter(like='ratio2').mean(axis=1)

# Save the plot as bytes
img_bytes = BytesIO()
plt.savefig(img_bytes, format='png')
img_bytes.seek(0)

# Convert the bytes to base64 for embedding in HTML
img_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')

# Render the HTML template with the embedded chart
@app.route('/')
def index():
    return render_template('index.html', img_base64=img_base64)

if __name__ == '__main__':
    app.run(debug=True)
