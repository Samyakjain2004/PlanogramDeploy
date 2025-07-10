import streamlit as st
from app.analyze import analyze_video_for_query
import tempfile
import os
import base64
import cv2
import time
from PIL import Image
from app.mcp_server import invoke_tool
from app.tools.price_compare import compare_prices, advanced_product_search, get_quantity_suggestions

def format_timestamp(ms):
    total_seconds = ms / 1000
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)
    subseconds = int((total_seconds - int(total_seconds)) * 100)
    return f"{minutes:02}:{seconds:02}.{subseconds:02}"

def extract_frame_at_timestamp(video_path, timestamp_ms):
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        cap.set(cv2.CAP_PROP_POS_MSEC, int(timestamp_ms))
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return None
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    except Exception as e:
        st.error(f"🚨 Exception while extracting frame: {str(e)}")
        return None

# === Streamlit UI ===
st.set_page_config(page_title="Planogram Vision", layout="wide")
st.title("Planogram Vision")

# === Session State ===
for key in ["file_path", "file_type", "timestamps", "summary", "file_base64"]:
    if key not in st.session_state:
        st.session_state[key] = None if key in ["file_path", "file_type"] else ""

# # === File Upload ===
# st.markdown("### 📤 Upload File (Image or Video)")
# uploaded_file = st.file_uploader("Upload a video or image", type=["mp4", "mov", "avi", "mkv", "jpg", "jpeg", "png"])
#
# if uploaded_file:
#     file_ext = uploaded_file.name.split(".")[-1].lower()
#     is_video = file_ext in ["mp4", "mov", "avi", "mkv"]
#     is_image = file_ext in ["jpg", "jpeg", "png"]
#     st.session_state.file_type = "video" if is_video else "image" if is_image else None
#
#     if st.session_state.file_type:
#         file_bytes = uploaded_file.read()
#         st.session_state.file_base64 = base64.b64encode(file_bytes).decode("utf-8")
#
#         suffix = f".{file_ext}"
#         with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
#             temp_file.write(file_bytes)
#             temp_file.flush()
#             st.session_state.file_path = temp_file.name
# === File Upload + Previous Files Dropdown ===
UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# st.markdown("### 📤 Upload File (Image or Video)")
#
# # List previously uploaded files
# existing_files = sorted(
#     [f for f in os.listdir(UPLOAD_DIR) if f.lower().endswith((".mp4", ".mov", ".avi", ".mkv", ".jpg", ".jpeg", ".png"))]
# )
# selected_prev_file = st.selectbox("Or choose a previously uploaded file:", ["-- None --"] + existing_files)
#
# uploaded_file = st.file_uploader("Upload a new video or image", type=["mp4", "mov", "avi", "mkv", "jpg", "jpeg", "png"])
st.markdown("### 📤 Upload File (Image or Video)")

col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader("Upload a new video or image", type=["mp4", "mov", "avi", "mkv", "jpg", "jpeg", "png"])

with col2:
    existing_files = sorted(
        [f for f in os.listdir(UPLOAD_DIR) if f.lower().endswith((".mp4", "mov", "avi", "mkv", "jpg", "jpeg", "png"))]
    )
    selected_prev_file = st.selectbox("Or choose from existing files", ["-- None --"] + existing_files)

file_to_use = None
file_ext = None

if uploaded_file is not None:
    file_ext = uploaded_file.name.split(".")[-1].lower()
    file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)

    # Save uploaded file to disk (overwrites if changed)
    with open(file_path, "wb") as f:
        file_bytes = uploaded_file.read()
        f.write(file_bytes)

    file_to_use = file_path

elif selected_prev_file != "-- None --":
    file_ext = selected_prev_file.split(".")[-1].lower()
    file_to_use = os.path.join(UPLOAD_DIR, selected_prev_file)

# Load and prepare file if selected/uploaded
if file_to_use:
    try:
        is_video = file_ext in ["mp4", "mov", "avi", "mkv"]
        is_image = file_ext in ["jpg", "jpeg", "png"]
        st.session_state.file_type = "video" if is_video else "image" if is_image else None

        with open(file_to_use, "rb") as f:
            file_bytes = f.read()
            st.session_state.file_base64 = base64.b64encode(file_bytes).decode("utf-8")

        st.session_state.file_path = file_to_use
    except Exception as e:
        st.error(f"⚠️ Error reading file: {e}")


# === Ask Question ===
st.markdown("### 💬 Ask Your Question")
user_query = st.text_area("Enter your question", placeholder="e.g. Where is Tide powder located?")

if st.button("🚀 Analyze"):
    if st.session_state.file_path and user_query and st.session_state.file_type:
        with st.spinner("Analyzing, please wait..."):
            try:
                result = analyze_video_for_query(st.session_state.file_path, user_query)
                st.session_state.result = result
                st.session_state.summary = result.get("final_summary", "")
                st.session_state.timestamps = result.get("timestamps", []) if st.session_state.file_type == "video" else []
                st.success("✅ Analysis complete!")
            except Exception as e:
                st.error(f"❌ Error during processing: {str(e)}")

# === Show Preview (only for image) ===
if st.session_state.file_type == "image" and st.session_state.file_base64:
    st.markdown("### 🖼 Image Preview")
    st.image(f"data:image/jpeg;base64,{st.session_state.file_base64}", width=300)

# === Show Summary ===
if st.session_state.summary:
    st.markdown("### 📝 Analysis Summary")
    
    # Clean the summary to remove technical artifacts
    clean_summary = st.session_state.summary
    
    # Remove product_name = ... lines
    import re
    clean_summary = re.sub(r'\n\s*product_name\s*=\s*[^\n]*', '', clean_summary)
    clean_summary = re.sub(r'product_name\s*=\s*[^\n]*', '', clean_summary)
    
    # Clean up extra whitespace and newlines
    clean_summary = re.sub(r'\n\s*\n', '\n', clean_summary).strip()
    
    st.write(clean_summary)

# === Advanced Price Comparison with Recommendations ===
product_name = ""
if "result" in st.session_state:
    product_name = st.session_state.result.get("product_name", "")
    print(f"[🧪 Triggering SerpAPI with product: {product_name}]")

if product_name and product_name.lower() != "unknown":
    st.markdown("### 🛒 Smart Price Agent")
    
    # Get quantity suggestions
    from app.tools.quantity_matcher import get_product_category
    
    # Define quantity suggestions based on product type
    category = get_product_category(product_name)
    if category == 'detergent':
        quantity_suggestions = ['250ml', '500ml', '1L', '2L', '500g', '1kg']
    elif category == 'soap':
        quantity_suggestions = ['75g', '100g', '125g', '150g', '1 piece', '3 pieces']
    else:
        quantity_suggestions = ['250ml', '500ml', '1L', '500g', '1kg', '1 piece']
    
    # Create columns for better layout
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # Quantity specification
        st.markdown("**📦 Specify Quantity**")
        quantity_option = st.selectbox(
            "What quantity are you looking for?",
            ["Any quantity"] + quantity_suggestions,
            help="Select the specific quantity you want to purchase"
        )
        
        # Custom quantity input
        custom_quantity = st.text_input(
            "Or enter custom quantity:",
            placeholder="e.g., 750ml, 2kg, 5 pieces",
            help="Enter your desired quantity in format: number + unit"
        )
    
    with col2:
        # Sorting options
        st.markdown("**🔄 Sort by**")
        sort_options = {
            "🎯 Best Match": "recommendation",
            "💰 Price: Low to High": "price_low", 
            "💰 Price: High to Low": "price_high",
            "⭐ Rating": "rating",
            "📝 Reviews": "reviews",
            "🚚 Delivery": "delivery"
        }
        
        sort_choice = st.selectbox(
            "Choose sorting criteria:",
            list(sort_options.keys()),
            help="How would you like to sort the results?"
        )
    
    with col3:
        # Number of results
        st.markdown("**📊 Results**")
        result_count = st.slider(
            "Number of products:",
            min_value=3,
            max_value=10,
            value=5,
            help="How many products to show"
        )
    
    # Price range filter (optional)
    st.markdown("**💸 Price Range (Optional)**")
    price_filter = st.checkbox("Filter by price range")
    min_price, max_price = 0, 50000
    
    if price_filter:
        price_range = st.slider(
            "Select price range (₹):",
            min_value=0,
            max_value=50000,
            value=(500, 5000),
            step=100,
            help="Set your budget range"
        )
        min_price, max_price = price_range
    
    # Search button
    if st.button("🔍 Find Best Deals", type="primary"):
        # Determine final quantity
        final_quantity = custom_quantity if custom_quantity else (
            quantity_option if quantity_option != "Any quantity" else None
        )
        
        # Determine sort criteria
        sort_by = sort_options[sort_choice]
        
        with st.spinner("🤖 AI analyzing best deals across the internet..."):
            # Check if API key is available
            if not os.getenv("SERPAPI_API_KEY"):
                st.error("❌ SerpAPI key is missing. Please check your .env file.")
            else:
                try:
                    # Use enhanced search system
                    from app.tools.enhanced_price_scraper import enhanced_product_search
                    
                    prices = enhanced_product_search(
                        product_name=product_name, 
                        quantity=final_quantity, 
                        sort_by=sort_by, 
                        limit=result_count
                    )
                    
                    # Check if there was an error
                    if len(prices) == 1 and "Error" in prices:
                        st.error(f"❌ {prices['Error']}")
                        st.warning("Try again later or check your internet connection.")
                    else:
                        # Import new components
                        from app.tools.ui_components import ComparisonTable, ProductCard, FilteringInfo
                        
                        # Display comparison header
                        header_html = ComparisonTable.create_comparison_header(
                            product_name, final_quantity, len(prices) - 1 if '🏆' in str(prices) else len(prices)
                        )
                        st.markdown(header_html, unsafe_allow_html=True)
                        
                        # Show filtering information
                        filter_info = FilteringInfo.create_filter_summary(
                            total_found=len(prices),
                            filtered_count=len(prices) - 1 if '🏆' in str(prices) else len(prices),
                            target_quantity=final_quantity,
                            sort_by=sort_choice
                        )
                        st.markdown(filter_info, unsafe_allow_html=True)
                        
                except Exception as e:
                    st.error(f"❌ Error fetching prices: {str(e)}")
                    st.warning("SerpAPI request failed. Please try again later.")
            # for site_title, markdown_text in prices.items():
            #     st.markdown(f"""
            # **{site_title}**
            # {markdown_text}
            # """, unsafe_allow_html=True)
            #st.markdown("### 🛒 Price Comparison")

            # cols = st.columns(3)
            #
            # for i, (site_title, markdown_text) in enumerate(prices.items()):
            #     with cols[i % 3]:
            #         # Extract image URL and link from markdown text
            #         import re
            #
            #         img_match = re.search(r'<img src="(.*?)"', markdown_text)
            #         link_match = re.search(r"\[Buy Now\]\((.*?)\)", markdown_text)
            #         price_match = re.search(r"₹[\d,.]+", markdown_text)
            #
            #         image_url = img_match.group(1) if img_match else ""
            #         product_url = link_match.group(1) if link_match else "#"
            #         price = price_match.group(0) if price_match else "₹N/A"
            #
            #         st.markdown(f"""
            #         <div style="
            #             border: 1px solid #e0e0e0;
            #             border-radius: 12px;
            #             box-shadow: 0 4px 8px rgba(0,0,0,0.05);
            #             padding: 16px;
            #             background-color: #ffffff;
            #             margin-bottom: 16px;
            #             text-align: center;
            #         ">
            #             <img src="{image_url}" style="width:100px; height:auto; margin-bottom:12px;" alt="Product">
            #             <div style="font-weight:600; font-size:16px; margin-bottom:6px;">{site_title}</div>
            #             <div style="font-size:15px; margin-bottom:8px; color:#444;">{price}</div>
            #             <a href="{product_url}" target="_blank" style="
            #                 display: inline-block;
            #                 padding: 6px 14px;
            #                 background-color: #ff7f50;
            #                 color: white;
            #                 text-decoration: none;
            #                 border-radius: 6px;
            #                 font-size: 14px;
            #                 font-weight: 500;
            #             ">Buy Now</a>
            #         </div>
            #         """, unsafe_allow_html=True)
                        
                # Use enhanced price scraper for better results
                from app.tools.enhanced_price_scraper import enhanced_product_search
                
                # Get enhanced results
                try:
                    enhanced_results = enhanced_product_search(
                        product_name=product_name,
                        quantity=final_quantity,
                        sort_by=sort_by,
                        limit=result_count
                    )
                    
                    if "Error" in enhanced_results:
                        st.error(f"❌ {enhanced_results['Error']}")
                        # Fall back to original results
                        enhanced_results = prices
                except:
                    # Fall back to original results if enhanced scraper fails
                    enhanced_results = prices
                
                # Display products using new system
                product_cards = []
                best_deal_data = None
                
                # Handle list return from enhanced_product_search
                if isinstance(enhanced_results, list):
                    # New format - direct list of products
                    product_cards = enhanced_results
                    # Get best deal (first product after sorting)
                    if product_cards:
                        best_deal_data = product_cards[0]
                elif isinstance(enhanced_results, dict):
                    # Legacy format - dictionary with keys
                    for key, value in enhanced_results.items():
                        if key.startswith("🏆"):
                            if isinstance(value, dict):
                                best_deal_data = value
                            continue
                        
                        # Handle both old and new format
                        if isinstance(value, dict):
                            # New enhanced format
                            product_cards.append(value)
                        else:
                            # Old format - convert
                            import re
                            img_match = re.search(r'<img src="(.*?)"', str(value))
                            link_match = re.search(r"\[Buy Now\]\((.*?)\)", str(value))
                            price_match = re.search(r"₹[\d,.]+", str(value))
                            rating_match = re.search(r"Rating.*?: ([\d.]+)", str(value))
                            
                            product_cards.append({
                                'title': key.split(" - ", 1)[1] if " - " in key else key,
                                'price': price_match.group(0) if price_match else "₹N/A",
                                'rating': float(rating_match.group(1)) if rating_match else 4.0,
                                'review_count': 100,
                                'image': img_match.group(1) if img_match else "https://via.placeholder.com/150x150.png?text=No+Image",
                                'link': link_match.group(1) if link_match else "#",
                                'platform': 'default',
                                'platform_name': 'Online Store',
                                'delivery': 'Standard delivery',
                                'savings': '',
                                'extracted_quantity': '',
                                'rank': len(product_cards) + 1
                            })
                
                if product_cards:
                    # Show best deal banner
                    if best_deal_data:
                        banner_html = ComparisonTable.create_best_deal_banner(best_deal_data)
                        st.markdown(banner_html, unsafe_allow_html=True)
                    elif product_cards:
                        banner_html = ComparisonTable.create_best_deal_banner(product_cards[0])
                        st.markdown(banner_html, unsafe_allow_html=True)
                    
                    # Display product cards in grid
                    cols = st.columns(2)
                    
                    for i, product_data in enumerate(product_cards):
                        with cols[i % 2]:
                            card_html = ProductCard.create_card(product_data, i + 1)
                            st.markdown(card_html, unsafe_allow_html=True)
                    
                    # Add spacing
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                else:
                    st.warning("No products found matching your criteria. Try adjusting your search terms or quantity.")

# === Video Timeline and Frame View ===
if st.session_state.file_type == "video" and st.session_state.file_path and st.session_state.file_base64:
    st.markdown("### 📊 Product Detection Timeline")

    cap = cv2.VideoCapture(st.session_state.file_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration_ms = (frame_count / fps) * 1000.0 if fps > 0 else 1
    cap.release()

    markers = ""
    for ts in st.session_state.timestamps:
        left_px = (ts / duration_ms) * 576.0
        markers += f'<div class="marker" style="left:{left_px:.2f}px;" title="{format_timestamp(ts)}"></div>'

    debug_ts = 3850
    debug_left_pct = min((debug_ts / duration_ms) * 100.0, 100)
    debug_marker = f'<div class="debug-line" style="left:{debug_left_pct:.6f}%;" title="03:03.85"></div>'

    st.markdown(
        f"""
        <div style="position:relative; width:640px; margin-bottom:8px;">
            <video id="videoPlayer" width="640" height="360" controls>
                <source src="data:video/mp4;base64,{st.session_state.file_base64}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
            <div class="timeline-overlay">
                <div class="timeline-inner">
                    {markers}{debug_marker}
                </div>
            </div>
        </div>

        <style>
        .timeline-overlay {{
            position: absolute;
            bottom: 42px;
            width: 640px;
            height: 0;
            display: flex;
            justify-content: center;
            pointer-events: none;
        }}
        .timeline-inner {{
            width: 576px;
            height: 12px;
            position: relative;
        }}
        .marker {{
            position: absolute;
            width: 4px;
            height: 6px;
            background-color: yellow;
            box-shadow: 0 0 4px rgba(255, 255, 0, 0.9);
        }}
        .marker:hover::after {{
            content: attr(title);
            position: absolute;
            top: -28px;
            left: -10px;
            background: black;
            color: white;
            padding: 2px 5px;
            font-size: 10px;
            border-radius: 4px;
            white-space: nowrap;
        }}
        .debug-line {{
            position: absolute;
            width: 1px;
            height: 12px;
            background-color: red;
            opacity: 0.9;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

    # === Timestamp Frame Viewer ===
    if st.session_state.timestamps:
        st.markdown("### ⏱️ View Frame by Timestamp")
        formatted_map = {format_timestamp(ts): ts for ts in st.session_state.timestamps}
        formatted_list = list(formatted_map.keys())

        selected_display = st.selectbox("Select timestamp", formatted_list)

        if st.button("🔍 Show Frame at Timestamp"):
            timestamp_ms = formatted_map[selected_display]
            frame = extract_frame_at_timestamp(st.session_state.file_path, timestamp_ms)
            if frame is not None:
                st.image(frame, caption=f"🖼 Frame at {selected_display}", width=320)
            else:
                st.warning(f"❌ No frame available at {selected_display}")

# === Clear Session ===
if st.session_state.file_path:
    if st.button("🧹 Clear Session & Delete File"):
        try:
            os.remove(st.session_state.file_path)
            st.success(f"🗑 File deleted: {st.session_state.file_path}")
        except Exception as e:
            st.warning(f"Could not delete file: {e}")
        for key in ["file_path", "file_type", "timestamps", "summary", "file_base64"]:
            st.session_state[key] = None if key in ["file_path", "file_type"] else ""
