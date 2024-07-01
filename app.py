import streamlit as st
import pandas as pd
import time
from google_play_scraper import Sort, reviews as gp_reviews, app as gp_app

# Function to scrape reviews from Google Play with rating filter
def scrape_google_play(app_id, num_reviews=100, sort_order=Sort.NEWEST, min_rating=None, max_rating=None):
    all_reviews = []
    next_token = None
    while len(all_reviews) < num_reviews:
        current_reviews, token = gp_reviews(
            app_id,
            lang='en',
            country='us',
            sort=sort_order,
            count=min(num_reviews - len(all_reviews), 100),
            filter_score_with=None if min_rating is None and max_rating is None else list(range(min_rating, max_rating + 1)),
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
st.title('Google Play Store Review Scraper')

st.write("To find the app ID, go to the Google Play Store, search for the app, and copy the part of the URL after `id=` (e.g., for `https://play.google.com/store/apps/details?id=com.example.app`, the app ID is `com.example.app`).")
st.write("[Click here for a guide on how to find the Google Play Store app ID](https://www.sociablekit.com/how-to-find-google-play-app-id/)")

app_id = st.text_input('Enter the Google Play App ID:')
num_reviews = st.slider('Select number of reviews to scrape', min_value=100, max_value=5000, step=100, value=100)
sort_order = st.selectbox('Select the sort order of the reviews', ['Newest', 'Rating'])
sort_order_map = {'Newest': Sort.NEWEST, 'Rating': Sort.RATING}
sort_order_selected = sort_order_map[sort_order]

min_rating, max_rating = None, None
if sort_order_selected == Sort.RATING:
    min_rating, max_rating = st.slider('Select the rating range', min_value=1, max_value=5, value=(1, 5))

if st.button('Scrape Reviews'):
    reviews = scrape_google_play(app_id, num_reviews, sort_order_selected, min_rating, max_rating)
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
