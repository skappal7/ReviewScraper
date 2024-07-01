import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io
import time
from google_play_scraper import Sort, reviews as gp_reviews, app as gp_app

# Function to scrape reviews from Trustpilot by organization name
def scrape_trustpilot_by_name(name):
    search_url = f"https://www.trustpilot.com/search?query={name}"
    response = requests.get(search_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    try:
        company_url = soup.find('a', class_='search-result-heading__title').get('href')
        full_url = f"https://www.trustpilot.com{company_url}"
        return scrape_trustpilot(full_url)
    except AttributeError:
        return None

def scrape_trustpilot(url):
    reviews = []
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    for review in soup.find_all('p', class_='review-content__text'):
        reviews.append(review.text.strip())
    return reviews

# Function to scrape reviews from PissedConsumer by organization name
def scrape_pissedconsumer_by_name(name):
    search_url = f"https://www.pissedconsumer.com/search.html?q={name}"
    response = requests.get(search_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    try:
        company_url = soup.find('a', class_='search-results-title').get('href')
        full_url = f"https://www.pissedconsumer.com{company_url}"
        return scrape_pissedconsumer(full_url)
    except AttributeError:
        return None

def scrape_pissedconsumer(url):
    reviews = []
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    for review in soup.find_all('p', class_='review-text'):
        reviews.append(review.text.strip())
    return reviews

# Function to scrape reviews from Google Play
def scrape_google_play(app_id, reviews_per_request=100, total_reviews_to_fetch=200):
    all_reviews = []
    next_token = None
    while len(all_reviews) < total_reviews_to_fetch:
        current_reviews, token = gp_reviews(
            app_id,
            lang='en',
            country='us',
            sort=Sort.NEWEST,
            count=reviews_per_request,
            filter_score_with=None,
            continuation_token=next_token
        )
        all_reviews.extend(current_reviews)
        next_token = token
        if not next_token:
            break
        time.sleep(5)
    reviews_text = [review['content'] for review in all_reviews]
    return reviews_text

# Function to fetch Google Play app details
def fetch_google_play_app_details(app_id):
    app_details = gp_app(app_id)
    return {
        'title': app_details['title'],
        'installs': app_details['installs'],
        'score': app_details['score'],
        'ratings': app_details['ratings'],
        'reviews': app_details['reviews'],
        'description': app_details['description']
    }

# Function to download data as CSV
def download_csv(data, filename):
    csv = data.to_csv(index=False)
    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name=filename,
        mime='text/csv',
    )

# Function to download data as Excel
def download_excel(data, filename):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    data.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.save()
    processed_data = output.getvalue()
    st.download_button(
        label="Download data as Excel",
        data=processed_data,
        file_name=filename,
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )

# Streamlit app
st.title('Review Scraper')

option = st.selectbox(
    'Choose a platform to scrape reviews from:',
    ('Trustpilot', 'PissedConsumer', 'Google Play')
)

if option == 'Trustpilot':
    org_name = st.text_input('Enter the name of the organization:')
    if st.button('Scrape Reviews'):
        reviews = scrape_trustpilot_by_name(org_name)
        if reviews:
            st.write(f"Scraped {len(reviews)} reviews for {org_name} from Trustpilot")
            reviews_df = pd.DataFrame(reviews, columns=['Review'])
            st.dataframe(reviews_df)
            download_csv(reviews_df, 'trustpilot_reviews.csv')
            download_excel(reviews_df, 'trustpilot_reviews.xlsx')
        else:
            st.write("No reviews found or unable to scrape.")

elif option == 'PissedConsumer':
    org_name = st.text_input('Enter the name of the organization:')
    if st.button('Scrape Reviews'):
        reviews = scrape_pissedconsumer_by_name(org_name)
        if reviews:
            st.write(f"Scraped {len(reviews)} reviews for {org_name} from PissedConsumer")
            reviews_df = pd.DataFrame(reviews, columns=['Review'])
            st.dataframe(reviews_df)
            download_csv(reviews_df, 'pissedconsumer_reviews.csv')
            download_excel(reviews_df, 'pissedconsumer_reviews.xlsx')
        else:
            st.write("No reviews found or unable to scrape.")

elif option == 'Google Play':
    st.write("To find the app ID, go to the Google Play Store, search for the app, and copy the part of the URL after `id=` (e.g., for `https://play.google.com/store/apps/details?id=com.example.app`, the app ID is `com.example.app`).")
    app_id = st.text_input('Enter the Google Play App ID:')
    if st.button('Scrape Reviews'):
        reviews = scrape_google_play(app_id)
        if reviews:
            app_details = fetch_google_play_app_details(app_id)
            st.write(f"App Title: {app_details['title']}")
            st.write(f"Installs: {app_details['installs']}")
            st.write(f"Average Rating: {app_details['score']}")
            st.write(f"Total Ratings: {app_details['ratings']}")
            st.write(f"Total Reviews: {app_details['reviews']}")
            st.write(f"Description: {app_details['description']}")
            st.write(f"Scraped {len(reviews)} reviews for App ID {app_id}")
            reviews_df = pd.DataFrame(reviews, columns=['Review'])
            st.dataframe(reviews_df)
            download_csv(reviews_df, 'google_play_reviews.csv')
            download_excel(reviews_df, 'google_play_reviews.xlsx')
        else:
            st.write("No reviews found or unable to scrape.")

st.write("Note: Scraping reviews from certain websites may violate their terms of service. Use responsibly and ensure compliance with the website's policies.")
