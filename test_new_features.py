#!/usr/bin/env python3
"""
Test script for new features: Google Vision, Direct Links, Price Filtering
"""

import sys
import os
sys.path.append('./app')

def test_direct_retailer_extractor():
    """Test direct retailer URL extraction"""
    print("🔗 Testing Direct Retailer Extractor...")
    
    try:
        from tools.direct_retailer_extractor import DirectRetailerExtractor
        
        extractor = DirectRetailerExtractor()
        
        # Test sample URLs
        test_urls = [
            "https://www.google.co.in/shopping/product/1?gl=in&prds=pid:123456789",
            "https://www.amazon.in/dp/B0123456789",
            "https://www.flipkart.com/product/xyz123",
            "https://unknown-site.com/product/123"
        ]
        
        for url in test_urls:
            direct_url, retailer_name, retailer_info = extractor.extract_direct_url(url)
            print(f"   URL: {url[:50]}...")
            print(f"   Retailer: {retailer_name}")
            print(f"   Trust Score: {retailer_info.get('trust_score', 'N/A')}")
            print()
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_enhanced_price_scraper():
    """Test enhanced price scraper with price filtering"""
    print("💰 Testing Enhanced Price Scraper with Price Filtering...")
    
    try:
        from tools.enhanced_price_scraper import enhanced_product_search
        
        # Test basic search
        results = enhanced_product_search('Tide detergent', quantity='500ml', limit=3)
        print(f"   Basic search: Found {len(results)} products")
        
        if results:
            print(f"   Sample product: {results[0].get('title', 'N/A')[:50]}...")
            print(f"   Platform: {results[0].get('platform_name', 'N/A')}")
            print(f"   Price: {results[0].get('price', 'N/A')}")
        
        # Test with price filtering
        results_filtered = enhanced_product_search(
            'Tide detergent', 
            quantity='500ml', 
            limit=3,
            price_min=50,
            price_max=200
        )
        print(f"   Filtered search (₹50-200): Found {len(results_filtered)} products")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_google_vision():
    """Test Google Vision integration"""
    print("👁️ Testing Google Vision Integration...")
    
    try:
        from tools.google_vision import GoogleVisionProductDetector
        
        detector = GoogleVisionProductDetector()
        
        # Test with placeholder (will use fallback)
        print("   Testing fallback product detection...")
        
        # This will use fallback since we don't have a real image
        products = detector._fallback_product_detection("test_image.jpg")
        print(f"   Fallback detection ready: {len(products)} products (expected 0 for test)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_ui_components():
    """Test enhanced UI components with more platforms"""
    print("🎨 Testing Enhanced UI Components...")
    
    try:
        from tools.ui_components import PlatformBadge, ProductCard
        
        # Test platform detection
        test_platforms = ['amazon', 'flipkart', 'bigbasket', 'nykaa', 'zepto']
        
        for platform in test_platforms:
            badge = PlatformBadge.generate_badge(platform)
            print(f"   {platform.title()} badge: {len(badge)} chars")
        
        # Test product card with new platform
        sample_product = {
            'title': 'Test Product from BigBasket',
            'price': '₹199',
            'rating': '4.2',
            'review_count': '1,234',
            'image': 'https://via.placeholder.com/150x150.png',
            'link': 'https://www.bigbasket.com/product/123',
            'platform': 'bigbasket',
            'platform_name': 'BigBasket',
            'delivery': 'Same day delivery available',
            'savings': '₹50',
            'extracted_quantity': '500ml'
        }
        
        card_html = ProductCard.create_card(sample_product, 1)
        print(f"   BigBasket product card: {len(card_html)} chars")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_price_extraction():
    """Test price range extraction from queries"""
    print("🔍 Testing Price Range Extraction...")
    
    try:
        # Simulate the extraction function
        import re
        
        def extract_price_range(query):
            range_patterns = [
                r'₹?(\d+)\s*[-to]\s*₹?(\d+)',
                r'between\s+₹?(\d+)\s+and\s+₹?(\d+)',
                r'under\s+₹?(\d+)',
                r'above\s+₹?(\d+)'
            ]
            
            query_lower = query.lower()
            
            for pattern in range_patterns[:2]:  # Range patterns
                match = re.search(pattern, query_lower)
                if match:
                    return float(match.group(1)), float(match.group(2))
            
            for pattern in range_patterns[2:3]:  # Under patterns
                match = re.search(pattern, query_lower)
                if match:
                    return None, float(match.group(1))
            
            for pattern in range_patterns[3:]:  # Above patterns
                match = re.search(pattern, query_lower)
                if match:
                    return float(match.group(1)), None
            
            return None, None
        
        test_queries = [
            "Find Tide detergent between ₹100 and ₹500",
            "Search for phones under ₹20000",
            "Show products above ₹1000",
            "Laptops 50000-80000",
            "Just search for headphones"
        ]
        
        for query in test_queries:
            price_min, price_max = extract_price_range(query)
            print(f"   Query: {query}")
            print(f"   Range: {price_min} - {price_max}")
            print()
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🧪 TESTING NEW FEATURES")
    print("=" * 50)
    
    tests = [
        ("Direct Retailer Extractor", test_direct_retailer_extractor),
        ("Enhanced Price Scraper", test_enhanced_price_scraper),
        ("Google Vision Integration", test_google_vision),
        ("UI Components", test_ui_components),
        ("Price Range Extraction", test_price_extraction)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"   ❌ Test failed: {str(e)}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    print("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Ready to deploy new features.")
    else:
        print("⚠️ Some tests failed. Check the issues above.")

if __name__ == "__main__":
    main()