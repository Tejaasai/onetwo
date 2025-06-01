import os
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from bs4 import BeautifulSoup
import requests
import time

# Define the scraping function
def scrape_flipkart(base_url, num_pages):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    }
    all_names = []
    all_prices = []
    all_discounts = []
    all_ratings = []

    for page in range(1, num_pages + 1):
        try:
            url = f"{base_url}&page={page}" if "?" in base_url else f"{base_url}?page={page}"
            source = requests.get(url, headers=headers)
            payload = {
                'api_key': os.getenv("SCRAPER_API_KEY"),
                'url': url
            }
            source = requests.get('http://api.scraperapi.com', params=payload, headers=headers)
            source.raise_for_status()
            soup = BeautifulSoup(source.text, 'html.parser')
            main_container = soup.find('div', class_=['DOjaWF gdgoEp'])

            if main_container:
                products = main_container.find_all('div', class_=['tUxRFH', 'slAVV4', '_1sdMkc LFEi7Z'])
                for p in products:
                    # Extract name
                    name_elem = p.find('div', class_=['KzDlHZ'])
                    name = name_elem.text if name_elem else (
                        p.find('a', class_=['wjcEIp', 'WKTcLC', 'WKTcLC BwBZTg']).text 
                        if p.find('a', class_=['wjcEIp', 'WKTcLC', 'WKTcLC BwBZTg']) 
                        else "Not Available"
                    )
                    # Extract price
                    price_elem = p.find('div', class_=['Nx9bqj _4b5DiR', 'Nx9bqj'])
                    price_text = price_elem.text.strip().replace('₹', '').replace(',', '') if price_elem else "Not Available"
                    try:
                        price = float(price_text)
                    except ValueError:
                        price = np.nan
                    # Extract discount
                    discount_elem = p.find('div', class_='UkUFwK')
                    discount = discount_elem.text.strip().replace('off', '') if discount_elem else "Not Available"
                    # Extract rating
                    rating_elem = p.find('div', class_='XQDdHH')
                    rating_text = rating_elem.text if rating_elem else "Not Available"
                    try:
                        rating = float(rating_text)
                    except ValueError:
                        rating = np.nan

                    all_names.append(name)
                    all_prices.append(price)
                    all_discounts.append(discount)
                    all_ratings.append(rating)
            time.sleep(1)  # Delay to avoid overwhelming the server
        except Exception as e:
            st.error(f"Error scraping page {page}: {e}")
            continue

    df = pd.DataFrame({
        'name': all_names,
        'price': all_prices,
        'discount': all_discounts,
        'rating': all_ratings
    })
    return df

# Streamlit App

st.sidebar.header("Scrape Settings")
url = st.sidebar.text_input("Flipkart URL", value="https://www.flipkart.com/search?q=t+shirts")
pages = st.sidebar.slider("Number of Pages", min_value=1, max_value=3, value=1)

# Display Metrics and Graphs
st.markdown(f"""
    <div style='background:#f9ff33;padding:20px;border-radius:10px;margin-bottom:20px'>
        <h1 style='color:#2874f0;text-align:center'>
            🛍️ Flipkart Smart Scraper
        </h1>
    </div>
    """, unsafe_allow_html=True)

if st.sidebar.button("Scrape Data"):
    with st.spinner("Scraping data..."):
        df = scrape_flipkart(url, pages)
    
    if not df.empty:
        st.success("Data scraped successfully!")
        
        

        # Metrics
        st.subheader("📈 Key Performance Indicators")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Products", len(df))
        col2.metric("Average Price", f"₹{df['price'].mean():.2f}" if not df['price'].dropna().empty else "N/A")
        avg_rating = df['rating'].mean()
        col3.metric("Average Rating", f"{avg_rating:.2f}/5" if not pd.isna(avg_rating) else "N/A")

        st.dataframe(df)

        # Analytics Dashboard
        st.header("📊 Advanced Analytics Dashboard")
        tab1, tab2, tab3, tab4 = st.tabs([
            "Price Intelligence", 
            "Rating Analysis", 
            "Product Insights",
            "Text Analytics"
        ])

        with tab1:
            st.subheader("💰 Price Distribution Analysis")
            col1, col2 = st.columns(2)
            with col1:
                fig = plt.figure()
                sns.histplot(df['price'].dropna(), bins=20, kde=True, color='skyblue')
                plt.xlabel("Price (₹)")
                st.pyplot(fig)
            with col2:
                fig = plt.figure()
                sns.boxplot(x=df['price'].dropna(), color='lightgreen')
                plt.xlabel("Price (₹)")
                st.pyplot(fig)

        with tab2:
            st.subheader("⭐ Rating Analysis")
            col1, col2 = st.columns(2)
            with col1:
                fig = plt.figure()
                sns.countplot(x=df['rating'].dropna().round(1), palette='viridis')
                plt.xticks(rotation=45)
                st.pyplot(fig)
            with col2:
                fig = plt.figure()
                sns.scatterplot(x=df['rating'], y=df['price'], alpha=0.6, color='orange')
                st.pyplot(fig)

        with tab3:
            st.subheader("🏆 Product Leaderboards")
            st.write("Top 10 expensive products")
            st.dataframe(df.nlargest(10, 'price')[['name', 'price']].style.format({'price': '₹{:.2f}'}), height=400)
            st.write("Top 10 rated products")
            st.dataframe(df.nlargest(10, 'rating')[['name', 'rating']], height=400)        

        with tab4:
            st.subheader("📝 Product Name Analytics")
            if not df['name'].dropna().empty:
                wordcloud = WordCloud(width=800, height=400, background_color='white').generate(' '.join(df['name'].dropna()))
                fig = plt.figure()
                plt.imshow(wordcloud, interpolation='bilinear')
                plt.axis('off')
                st.pyplot(fig)
            else:
                st.warning("No product names available for text analysis")
    else:
        st.warning("No data was scraped. Please check the URL and try again.")
else:
    st.info("Enter a Flipkart URL and select the number of pages, then click 'Scrape Data' to begin.")