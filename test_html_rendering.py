#!/usr/bin/env python3
"""
Test HTML rendering in Streamlit with logging
"""
import streamlit as st
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from tools.ui_components import ProductCard, PlatformBadge

def main():
    st.title("🧪 HTML Rendering Test")
    
    # Create sample product data
    sample_product = {
        'title': 'Dettol Handwash Original - 250ml',
        'price': '₹125',
        'rating': '4.3',
        'review_count': '2,156',
        'image': 'https://m.media-amazon.com/images/I/61-2Bq1V1lL._SL1500_.jpg',
        'link': 'https://www.amazon.in/Dettol-Handwash-Original-250ml/dp/B00FRDOQ0C',
        'platform': 'amazon',
        'delivery': 'FREE delivery by tomorrow',
        'savings': '₹25',
        'extracted_quantity': '250ml'
    }
    
    # Test 1: Direct HTML rendering
    st.subheader("Test 1: Direct HTML Rendering")
    
    # Generate the card HTML
    card_html = ProductCard.create_card(sample_product, 1)
    
    # Log details
    st.write(f"**Generated HTML Length:** {len(card_html)}")
    st.write(f"**Contains newlines:** {chr(10) in card_html}")
    st.write(f"**Contains tabs:** {chr(9) in card_html}")
    st.write(f"**Contains HTML comments:** {'<!--' in card_html}")
    
    # Show first few characters
    st.write(f"**First 200 chars:** {card_html[:200]}")
    
    # Test rendering
    st.subheader("Attempting to render card...")
    
    try:
        # Try to render the card
        st.markdown(card_html, unsafe_allow_html=True)
        st.success("✅ HTML Card rendered successfully!")
    except Exception as e:
        st.error(f"❌ Error rendering card: {str(e)}")
        st.write("**Raw HTML output:**")
        st.text(card_html)
    
    # Test 2: Alternative rendering with components
    st.subheader("Test 2: Alternative Rendering")
    
    try:
        import streamlit.components.v1 as components
        st.write("Using streamlit.components.v1.html:")
        components.html(card_html, height=400, scrolling=True)
        st.success("✅ Components rendering worked!")
    except Exception as e:
        st.error(f"❌ Components rendering failed: {str(e)}")
    
    # Test 3: Simple HTML test
    st.subheader("Test 3: Simple HTML Test")
    
    simple_html = '<div style="background: #4CAF50; color: white; padding: 20px; border-radius: 10px; text-align: center;"><h3>This is a simple HTML test</h3><p>If you can see this properly styled, HTML rendering is working!</p></div>'
    
    st.write("Simple HTML test:")
    st.markdown(simple_html, unsafe_allow_html=True)
    
    # Test 4: Platform badge test
    st.subheader("Test 4: Platform Badge Test")
    
    badge_html = PlatformBadge.generate_badge('amazon')
    st.write("Platform badge:")
    st.markdown(badge_html, unsafe_allow_html=True)
    
    # Test 5: Image test
    st.subheader("Test 5: Image Test")
    
    image_html = f'<div style="text-align: center; padding: 20px;"><img src="{sample_product["image"]}" style="width: 200px; height: 200px; object-fit: cover; border-radius: 10px; border: 2px solid #ddd;" alt="Product Image"></div>'
    
    st.write("Image test:")
    st.markdown(image_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()