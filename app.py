# app.py
from flask import Flask, render_template
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import seaborn as sns
import pandas as pd
from datetime import datetime
from pandas.plotting import register_matplotlib_converters
import os
from config import CONFIG, USER_TIMEFRAMES
import mpld3

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
app = Flask(__name__, template_folder=template_dir)

# Configuration
activate_filter_date = CONFIG['activate_filter_date']
activate_href_filter = CONFIG['activate_href_filter']
resample_var = CONFIG['resample_var']
general_start_date = CONFIG['general_start_date']
general_end_date = CONFIG['general_end_date']
usernames = CONFIG['usernames']
bar_size = CONFIG["bar_size"]

# Define general_timeframe
general_timeframe = (general_start_date, general_end_date)

# Set seaborn style
sns.set_theme(style="whitegrid", font_scale=1.2)

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
    df_resampled['RelativeRatio'] = ((((df_resampled['Ratio'] / december_ratio))) * 100 ) * -1
    return df_resampled

def plot_ratio_bars(df_resampled, color, username):
    plt.bar(df_resampled.index[1:], df_resampled['RelativeRatio'][1:], color=color, label=username, alpha=1, width=25)

def customize_plot_appearance(date_range):
    plt.xticks(date_range, [month.strftime('%B') for month in date_range], rotation=45, ha='right')



def plot_comments_likes_ratio(username, color, resample_type, user_timeframes, activate_filter_date, general_timeframe, activate_href_filter, vertical_lines=None, size_line=1):
    df = load_and_preprocess_data(username)
    df = apply_general_datetime_filter(df, general_timeframe)
    df = apply_user_datetime_filter(df, activate_filter_date, user_timeframes, username)
    df = apply_href_filter(df, activate_href_filter)

    df_resampled = resample_and_fill_missing(df, resample_type)
    df_resampled = calculate_ratio(df_resampled)

    color = '#db2777'

    # Set the background of the entire plot to be transparent
    plt.figure(figsize=(10, 5), facecolor='none')  # Adjust the figsize to make the chart smaller
    plt.axes().set_facecolor('none')

    # Plot the bars with transparency and blue color
    bars = plt.bar(df_resampled.index[1:], df_resampled['RelativeRatio'][1:], color=color, alpha=1, width=bar_size, edgecolor=color)

    # Customize plot appearance
    date_range = pd.date_range(start=df_resampled.index[1].replace(tzinfo=None), 
                               end=datetime(2025, 7, 14).replace(tzinfo=None), freq='M')
    customize_plot_appearance(date_range)


    # Delete vertical grid lines
    plt.gca().xaxis.grid(False)
    # Delete horizontal grid lines
    plt.gca().yaxis.grid(False)


   
    return df_resampled


# Set seaborn style
# Create an empty DataFrame to store the mixed data
mixed_df = pd.DataFrame()

# Plot for each user and update the mixed DataFrame
for username, color in zip(usernames, sns.color_palette("tab10", n_colors=len(usernames))):
    user_data = plot_comments_likes_ratio(username, color, resample_var, USER_TIMEFRAMES,
                                          activate_filter_date,
                                          general_timeframe,
                                          activate_href_filter)
    mixed_df = pd.concat([mixed_df, user_data], axis=1)

# Customize x-axis ticks with month names
plt.xticks(rotation=90)

# Calculate the average line
mixed_df['Average'] = mixed_df.filter(like='ratio2').mean(axis=1)

# Convert the plot to an HTML string using mpld3
html_plot = mpld3.fig_to_html(plt.gcf(), template_type='simple')

# Render the HTML template with the embedded plot
@app.route('/')
def index():
    return render_template('index.html', html_plot=html_plot)

if __name__ == '__main__':
    app.run(debug=True)
