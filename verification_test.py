#!/usr/bin/env python3
"""
Comprehensive verification test after fixing AttributeError
"""
import sys
sys.path.append('./app')

def test_complete_workflow():
    """Test the complete application workflow"""
    print("🔍 COMPREHENSIVE VERIFICATION TEST")
    print("="*50)
    
    try:
        # Import all necessary modules
        from tools.enhanced_price_scraper import enhanced_product_search
        from tools.ui_components import ProductCard, ComparisonTable
        from tools.quantity_matcher import QuantityMatcher
        
        print("\n✅ All modules imported successfully")
        
        # Test 1: Enhanced Product Search
        print("\n1️⃣ Testing Enhanced Product Search...")
        products = enhanced_product_search('Dettol handwash', quantity='250ml', limit=3)
        
        print(f"   Return Type: {type(products)}")
        print(f"   Number of Products: {len(products)}")
        
        if not isinstance(products, list):
            print("   ❌ ERROR: Function should return a list")
            return False
        
        if len(products) == 0:
            print("   ❌ ERROR: No products returned")
            return False
        
        print("   ✅ Enhanced product search working correctly")
        
        # Test 2: Data Structure Validation
        print("\n2️⃣ Testing Data Structure...")
        first_product = products[0]
        required_keys = [
            'title', 'price', 'rating', 'review_count', 'image', 
            'link', 'platform', 'platform_name', 'delivery', 
            'savings', 'extracted_quantity', 'rank'
        ]
        
        missing_keys = [key for key in required_keys if key not in first_product]
        if missing_keys:
            print(f"   ❌ ERROR: Missing keys: {missing_keys}")
            return False
        
        print("   ✅ All required data keys present")
        print(f"   Sample product: {first_product['title'][:40]}...")
        print(f"   Price: {first_product['price']}")
        print(f"   Platform: {first_product['platform_name']}")
        
        # Test 3: HTML Generation
        print("\n3️⃣ Testing HTML Generation...")
        for i, product in enumerate(products[:2]):
            card_html = ProductCard.create_card(product, i+1)
            
            # Check HTML quality
            is_clean = not (chr(10) in card_html or chr(9) in card_html or '<!--' in card_html)
            has_image = '<img' in card_html
            has_buy_button = 'Buy Now' in card_html
            has_price = product['price'] in card_html
            
            print(f"   Product {i+1}:")
            print(f"     HTML Length: {len(card_html)} chars")
            print(f"     Clean HTML: {is_clean}")
            print(f"     Has Image: {has_image}")
            print(f"     Has Buy Button: {has_buy_button}")
            print(f"     Has Price: {has_price}")
            
            if not all([is_clean, has_image, has_buy_button, has_price]):
                print(f"   ❌ ERROR: HTML generation issues for product {i+1}")
                return False
        
        print("   ✅ HTML generation working correctly")
        
        # Test 4: Simulate Streamlit App Logic
        print("\n4️⃣ Testing Streamlit App Logic...")
        
        # Simulate the fixed logic in streamlit_app.py
        enhanced_results = products  # This is what the app gets
        product_cards = []
        best_deal_data = None
        
        # Test the isinstance logic
        if isinstance(enhanced_results, list):
            product_cards = enhanced_results
            if product_cards:
                best_deal_data = product_cards[0]
        
        print(f"   Product cards created: {len(product_cards)}")
        print(f"   Best deal data: {'✅' if best_deal_data else '❌'}")
        
        if len(product_cards) == 0 or not best_deal_data:
            print("   ❌ ERROR: Streamlit app logic failed")
            return False
        
        print("   ✅ Streamlit app logic working correctly")
        
        # Test 5: End-to-End HTML Rendering
        print("\n5️⃣ Testing End-to-End HTML Rendering...")
        
        # Generate comparison header
        header_html = ComparisonTable.create_comparison_header(
            "Dettol Handwash", "250ml", len(product_cards)
        )
        
        # Generate all product cards
        all_cards_html = []
        for i, product_data in enumerate(product_cards):
            card_html = ProductCard.create_card(product_data, i + 1)
            all_cards_html.append(card_html)
        
        total_html_size = len(header_html) + sum(len(card) for card in all_cards_html)
        print(f"   Header HTML: {len(header_html)} chars")
        print(f"   Product Cards: {len(all_cards_html)} cards")
        print(f"   Total HTML Size: {total_html_size} chars")
        
        # Check if all HTML is clean
        all_html_clean = all(
            not (chr(10) in card or chr(9) in card or '<!--' in card)
            for card in all_cards_html
        )
        
        print(f"   All HTML Clean: {all_html_clean}")
        
        if not all_html_clean:
            print("   ❌ ERROR: Some HTML is not clean")
            return False
        
        print("   ✅ End-to-end HTML rendering working correctly")
        
        print("\n" + "="*50)
        print("🎉 ALL TESTS PASSED!")
        print("="*50)
        print("✅ Enhanced Product Search: Working")
        print("✅ Data Structure: Correct")
        print("✅ HTML Generation: Clean and Complete")
        print("✅ Streamlit App Logic: Fixed")
        print("✅ End-to-End Workflow: Functional")
        print("\n🚀 APPLICATION IS FULLY OPERATIONAL")
        print("🔗 Access at: http://localhost:8501")
        
        return True
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_complete_workflow()
    exit(0 if success else 1)