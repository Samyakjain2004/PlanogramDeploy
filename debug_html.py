#!/usr/bin/env python3
"""
Debug HTML rendering in Streamlit
"""
import streamlit as st
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from tools.ui_components import ProductCard, PlatformBadge

def test_html_rendering():
    """Test HTML rendering step by step"""
    
    st.title("🐛 HTML Rendering Debug")
    
    # Test 1: Simple HTML
    st.subheader("Test 1: Simple HTML")
    simple_html = "<div style='background: red; color: white; padding: 10px;'>Simple Test</div>"
    st.markdown("Raw HTML:", simple_html)
    st.markdown("Rendered HTML:")
    st.markdown(simple_html, unsafe_allow_html=True)
    
    # Test 2: Platform Badge
    st.subheader("Test 2: Platform Badge")
    badge_html = PlatformBadge.generate_badge('amazon')
    st.markdown("Badge HTML:", badge_html)
    st.markdown("Rendered Badge:")
    st.markdown(badge_html, unsafe_allow_html=True)
    
    # Test 3: Product Card
    st.subheader("Test 3: Product Card")
    
    sample_product = {
        'title': 'Test Product Card',
        'price': '₹199',
        'rating': '4.2',
        'review_count': '1,234',
        'image': 'https://via.placeholder.com/150x150.png?text=Test+Image',
        'link': 'https://example.com',
        'platform': 'amazon',
        'delivery': '2-3 days',
        'savings': '₹50',
        'extracted_quantity': '250ml'
    }
    
    card_html = ProductCard.create_card(sample_product, 1)
    
    # Debug info
    st.write("**Debug Info:**")
    st.write(f"Card HTML Length: {len(card_html)}")
    st.write(f"Contains HTML comments: {'<!--' in card_html}")
    st.write(f"First 200 chars: {card_html[:200]}")
    
    # Show raw HTML in expandable section
    with st.expander("Show Raw HTML"):
        st.text(card_html)
    
    # Try to render the card
    st.subheader("Attempting to render card:")
    try:
        st.markdown(card_html, unsafe_allow_html=True)
        st.success("✅ Card rendered successfully!")
    except Exception as e:
        st.error(f"❌ Error rendering card: {str(e)}")
    
    # Test 4: Alternative rendering methods
    st.subheader("Test 4: Alternative Methods")
    
    # Method 1: Using st.write
    st.write("**Method 1: Using st.write**")
    try:
        st.write(card_html, unsafe_allow_html=True)
        st.success("✅ st.write worked!")
    except Exception as e:
        st.error(f"❌ st.write failed: {str(e)}")
    
    # Method 2: Using components.html
    st.write("**Method 2: Using components.html**")
    try:
        import streamlit.components.v1 as components
        components.html(card_html, height=400)
        st.success("✅ components.html worked!")
    except Exception as e:
        st.error(f"❌ components.html failed: {str(e)}")

if __name__ == "__main__":
    test_html_rendering()