import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from google_play_scraper import Sort, reviews as gp_reviews, app as gp_app

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Function to scrape reviews from Trustpilot by organization name
def scrape_trustpilot_by_name(name):
    search_url = f"https://www.trustpilot.com/search?query={name}"
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    try:
        company_url = soup.find('a', class_='search-result-heading__title').get('href')
        full_url = f"https://www.trustpilot.com{company_url}"
        return scrape_trustpilot(full_url)
    except AttributeError as e:
        st.write(f"Error finding company URL: {e}")
        return None

def scrape_trustpilot(url):
    reviews = []
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        review_containers = soup.select('.styles_review__3HHTb')
        for review in review_containers:
            reviewer_name = review.select_one('.styles_consumerDetailsWrapper__nU4Xd .typography_typography__F2JzV.typography_bodysmall__2jSAv.typography_color--dark__5k6hX.typography_fontstyle--bold__j6yRo').text.strip()
            review_date = review.select_one('time').text.strip()
            review_title = review.select_one('h2').text.strip()
            review_text = review.select_one('p').text.strip()
            review_rating = review.select_one('.styles_reviewHeader__iU9Px img')['alt']
            reviews.append({
                'Reviewer Name': reviewer_name,
                'Review Date': review_date,
                'Review Title': review_title,
                'Review Text': review_text,
                'Review Rating': review_rating
            })
    except requests.exceptions.RequestException as e:
        st.write(f"An error occurred while making the request: {e}")
    except AttributeError as e:
        st.write(f"An error occurred while parsing the HTML: {e}")
    except Exception as e:
        st.write(f"An unexpected error occurred: {e}")
    return reviews

# Function to scrape reviews from PissedConsumer by organization name
def scrape_pissedconsumer_by_name(name):
    search_url = f"https://www.pissedconsumer.com/search.html?q={name}"
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    try:
        company_url = soup.find('a', class_='search-results-title').get('href')
        full_url = f"https://www.pissedconsumer.com{company_url}"
        return scrape_pissedconsumer(full_url)
    except AttributeError as e:
        st.write(f"Error finding company URL: {e}")
        return None

def scrape_pissedconsumer(url):
    reviews = []
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        review_containers = soup.select('.complaints__item')
        for review in review_containers:
            reviewer_name = review.select_one('.complaints__author a').text.strip()
            review_date = review.select_one('time').text.strip()
            review_title = review.select_one('h3 a').text.strip()
            review_text = review.select_one('.complaints__text').text.strip()
            review_rating = review.select_one('.rating img')['alt']
            reviews.append({
                'Reviewer Name': reviewer_name,
                'Review Date': review_date,
                'Review Title': review_title,
                'Review Text': review_text,
                'Review Rating': review_rating
            })
    except requests.exceptions.RequestException as e:
        st.write(f"An error occurred while making the request: {e}")
    except AttributeError as e:
        st.write(f"An error occurred while parsing the HTML: {e}")
    except Exception as e:
        st.write(f"An unexpected error occurred: {e}")
    return reviews

# Function to scrape reviews from Google Play
def scrape_google_play(app_id, num_reviews=100, sort_order=Sort.NEWEST):
    all_reviews = []
    next_token = None
    while len(all_reviews) < num_reviews:
        current_reviews, token = gp_reviews(
            app_id,
            lang='en',
            country='us',
            sort=sort_order,
            count=min(num_reviews - len(all_reviews), 100),
            filter_score_with=None,
            continuation_token=next_token
        )
        all_reviews.extend(current_reviews)
        next_token = token
        if not next_token:
            break
        time.sleep(2)  # Add delay to avoid rate limiting
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
            reviews_df = pd.DataFrame(reviews)
            st.dataframe(reviews_df)
            download_csv(reviews_df, 'trustpilot_reviews.csv')
        else:
            st.write("No reviews found or unable to scrape.")

elif option == 'PissedConsumer':
    org_name = st.text_input('Enter the name of the organization:')
    if st.button('Scrape Reviews'):
        reviews = scrape_pissedconsumer_by_name(org_name)
        if reviews:
            st.write(f"Scraped {len(reviews)} reviews for {org_name} from PissedConsumer")
            reviews_df = pd.DataFrame(reviews)
            st.dataframe(reviews_df)
            download_csv(reviews_df, 'pissedconsumer_reviews.csv')
        else:
            st.write("No reviews found or unable to scrape.")

elif option == 'Google Play':
    st.write("To find the app ID, go to the Google Play Store, search for the app, and copy the part of the URL after `id=` (e.g., for `https://play.google.com/store/apps/details?id=com.example.app`, the app ID is `com.example.app`).")
    app_id = st.text_input('Enter the Google Play App ID:')
    num_reviews = st.slider('Select number of reviews to scrape', min_value=50, max_value=500, step=50, value=10)
    sort_order = st.selectbox('Select the sort order of the reviews', ['Newest', 'Rating'])
    sort_order_map = {'Newest': Sort.NEWEST, 'Rating': Sort.RATING}
    sort_order_selected = sort_order_map[sort_order]

    if st.button('Scrape Reviews'):
        reviews = scrape_google_play(app_id, num_reviews, sort_order_selected)
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
        else:
            st.write("No reviews found or unable to scrape.")

st.write("Note: Scraping reviews from certain websites may violate their terms of service. Use responsibly and ensure compliance with the website's policies.")
