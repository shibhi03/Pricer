import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

# Ensure the root project directory is in the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

st.set_page_config(page_title="Pricer - E-commerce Scraper", layout="wide")

from src.core.config_loader import load_config
from src.services.scrapper_service import ScraperService
from src.models.database import get_session_local, init_db
from src.models.product import Product, PriceHistory

# Load Config and Initialize Service
@st.cache_resource
def get_scraper_service():
    config = load_config()
    return ScraperService(config)

service = get_scraper_service()

st.title("🛒 Pricer - Smart E-commerce Comparison")
st.markdown("Search across multiple platforms (Amazon, Flipkart, Meesho, etc.) to find the best prices.")

query = st.text_input("Enter product name to search:")

if st.button("Search", type="primary"):
    if not query:
        st.warning("Please enter a search query.")
    else:
        with st.spinner("Scraping across platforms. This may take a moment..."):
            results = service.search(query)
            
            if not results:
                st.error("No results found or all scrapers were blocked.")
            else:
                st.success(f"Found {len(results)} items!")
                
                # Convert to DataFrame
                df = pd.DataFrame(results)
                
                # Remove zero prices for charting and calculation
                valid_prices_df = df[df["price"] > 0]
                
                # Show key metrics
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Items Found", len(results))
                if not valid_prices_df.empty:
                    lowest_price = valid_prices_df["price"].min()
                    best_platform = valid_prices_df.loc[valid_prices_df["price"].idxmin(), "platform"]
                    col2.metric("Lowest Price", f"₹{lowest_price}", delta=best_platform.capitalize(), delta_color="off")
                    col3.metric("Average Price", f"₹{valid_prices_df['price'].mean():.2f}")

                st.subheader("Price Comparison by Platform")
                if not valid_prices_df.empty:
                    # Group by platform to show average price
                    avg_prices = valid_prices_df.groupby("platform")["price"].mean().reset_index()
                    fig = px.bar(
                        avg_prices, 
                        x="platform", 
                        y="price", 
                        title="Average Price per Platform",
                        color="platform",
                        text_auto='.2s'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                st.subheader("Detailed Results")
                
                # Display results with image links
                display_df = df.copy()
                # Make URLs clickable if using st.dataframe with column config, 
                # but st.data_editor is better for links in recent streamlit versions.
                st.dataframe(
                    display_df,
                    column_config={
                        "url": st.column_config.LinkColumn("Product Link"),
                        "image_url": st.column_config.ImageColumn("Image")
                    },
                    hide_index=True,
                    use_container_width=True
                )

st.divider()

st.subheader("📈 Price History")
st.markdown("View historical prices for a saved product.")

# Fetch unique search queries from DB
try:
    db = service.SessionLocal()
    saved_queries = [row[0] for row in db.query(Product.search_query).distinct().all()]
    if saved_queries:
        selected_query = st.selectbox("Select a previously searched item:", saved_queries)
        
        if selected_query:
            # Get products for this query
            products = db.query(Product).filter(Product.search_query == selected_query).all()
            
            if products:
                history_data = []
                for p in products:
                    for h in p.prices:
                        history_data.append({
                            "platform": p.platform,
                            "title": p.title[:50] + "...",
                            "price": h.price,
                            "timestamp": h.timestamp
                        })
                
                if history_data:
                    history_df = pd.DataFrame(history_data)
                    fig_hist = px.line(
                        history_df, 
                        x="timestamp", 
                        y="price", 
                        color="platform",
                        line_group="title",
                        hover_name="title",
                        title=f"Price History for '{selected_query}'"
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)
                else:
                    st.info("No price history data available for these products.")
    else:
         st.info("No saved searches yet.")
except Exception as e:
    st.error(f"Error connecting to database: {e}")
finally:
    if 'db' in locals():
        db.close()
