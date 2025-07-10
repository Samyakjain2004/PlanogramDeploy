#!/usr/bin/env python3
"""
Google Vision API Integration for Product Detection
Enhanced visual product matching with Google's AI
"""

import os
import requests
import base64
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json

@dataclass
class ProductDetection:
    """Product detection result from Google Vision"""
    name: str
    brand: str
    category: str
    confidence: float
    description: str
    attributes: Dict[str, str]
    bounding_box: Optional[Dict] = None

class GoogleVisionProductDetector:
    """Google Vision API integration for product detection"""
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_CLOUD_API_KEY")
        self.vision_endpoint = "https://vision.googleapis.com/v1/images:annotate"
        
    def detect_products_in_image(self, image_path: str) -> List[ProductDetection]:
        """
        Detect products in image using Google Vision API
        
        Args:
            image_path: Path to the image file
            
        Returns:
            List of detected products with details
        """
        try:
            # Encode image to base64
            image_base64 = self._encode_image(image_path)
            
            # Prepare the request
            request_data = {
                "requests": [
                    {
                        "image": {
                            "content": image_base64
                        },
                        "features": [
                            {
                                "type": "PRODUCT_SEARCH",
                                "maxResults": 10
                            },
                            {
                                "type": "OBJECT_LOCALIZATION",
                                "maxResults": 10
                            },
                            {
                                "type": "TEXT_DETECTION",
                                "maxResults": 10
                            },
                            {
                                "type": "LOGO_DETECTION",
                                "maxResults": 10
                            }
                        ]
                    }
                ]
            }
            
            # Make API request
            response = requests.post(
                f"{self.vision_endpoint}?key={self.api_key}",
                headers={"Content-Type": "application/json"},
                json=request_data,
                timeout=30
            )
            
            if response.status_code == 200:
                return self._parse_vision_response(response.json())
            else:
                print(f"❌ Google Vision API error: {response.status_code}")
                return self._fallback_product_detection(image_path)
                
        except Exception as e:
            print(f"❌ Google Vision error: {str(e)}")
            return self._fallback_product_detection(image_path)
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image file to base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _parse_vision_response(self, response: Dict) -> List[ProductDetection]:
        """Parse Google Vision API response into ProductDetection objects"""
        products = []
        
        if "responses" not in response:
            return products
        
        vision_response = response["responses"][0]
        
        # Extract product search results
        if "productSearchResults" in vision_response:
            product_results = vision_response["productSearchResults"]
            for result in product_results.get("results", []):
                product = self._create_product_from_search_result(result)
                if product:
                    products.append(product)
        
        # Extract from object localization
        if "localizedObjectAnnotations" in vision_response:
            objects = vision_response["localizedObjectAnnotations"]
            for obj in objects:
                product = self._create_product_from_object(obj)
                if product:
                    products.append(product)
        
        # Extract from text and logos
        text_products = self._extract_products_from_text(vision_response)
        products.extend(text_products)
        
        return products
    
    def _create_product_from_search_result(self, result: Dict) -> Optional[ProductDetection]:
        """Create ProductDetection from product search result"""
        try:
            product_info = result.get("product", {})
            
            return ProductDetection(
                name=product_info.get("displayName", "Unknown Product"),
                brand=self._extract_brand(product_info),
                category=product_info.get("productCategory", "General"),
                confidence=result.get("score", 0.0),
                description=product_info.get("description", ""),
                attributes=self._extract_attributes(product_info)
            )
        except Exception:
            return None
    
    def _create_product_from_object(self, obj: Dict) -> Optional[ProductDetection]:
        """Create ProductDetection from object localization"""
        try:
            name = obj.get("name", "")
            
            # Filter for product-related objects
            product_keywords = [
                "bottle", "box", "package", "container", "food", "drink",
                "cosmetic", "detergent", "soap", "shampoo", "medicine"
            ]
            
            if any(keyword in name.lower() for keyword in product_keywords):
                return ProductDetection(
                    name=name.title(),
                    brand="Unknown",
                    category="Product",
                    confidence=obj.get("score", 0.0),
                    description=f"Detected {name}",
                    attributes={},
                    bounding_box=obj.get("boundingPoly", {})
                )
        except Exception:
            return None
    
    def _extract_products_from_text(self, vision_response: Dict) -> List[ProductDetection]:
        """Extract product information from detected text"""
        products = []
        
        # Get all detected text
        text_annotations = vision_response.get("textAnnotations", [])
        if not text_annotations:
            return products
        
        full_text = text_annotations[0].get("description", "").lower()
        
        # Common product brands and categories
        brand_patterns = {
            "tide": "Detergent",
            "surf": "Detergent", 
            "ariel": "Detergent",
            "vim": "Dishwash",
            "dettol": "Antiseptic",
            "lux": "Soap",
            "dove": "Soap",
            "pantene": "Shampoo",
            "head & shoulders": "Shampoo",
            "colgate": "Toothpaste",
            "oral-b": "Toothpaste",
            "maggi": "Food",
            "nestle": "Food",
            "coca-cola": "Beverage",
            "pepsi": "Beverage"
        }
        
        for brand, category in brand_patterns.items():
            if brand in full_text:
                products.append(ProductDetection(
                    name=f"{brand.title()} Product",
                    brand=brand.title(),
                    category=category,
                    confidence=0.8,
                    description=f"Detected {brand} brand product",
                    attributes={"source": "text_detection"}
                ))
        
        return products
    
    def _extract_brand(self, product_info: Dict) -> str:
        """Extract brand information from product data"""
        # Try different fields that might contain brand info
        brand_fields = ["brand", "manufacturer", "displayName"]
        
        for field in brand_fields:
            if field in product_info:
                return product_info[field]
        
        return "Unknown"
    
    def _extract_attributes(self, product_info: Dict) -> Dict[str, str]:
        """Extract product attributes"""
        attributes = {}
        
        # Common attribute fields
        attr_fields = ["color", "size", "material", "weight", "volume"]
        
        for field in attr_fields:
            if field in product_info:
                attributes[field] = product_info[field]
        
        return attributes
    
    def _fallback_product_detection(self, image_path: str) -> List[ProductDetection]:
        """Fallback product detection using local analysis"""
        # Use existing Azure OpenAI analysis as fallback
        try:
            from app.analyze import extract_products_from_image
            
            result = extract_products_from_image(
                image_path, 
                "What products do you see in this image? List the brand names and product types."
            )
            
            if result and result.get("summary"):
                # Parse the summary to create product detections
                summary = result["summary"]
                return self._parse_text_to_products(summary)
            
        except Exception as e:
            print(f"❌ Fallback detection error: {str(e)}")
        
        return []
    
    def _parse_text_to_products(self, text: str) -> List[ProductDetection]:
        """Parse text analysis into ProductDetection objects"""
        products = []
        
        # Simple parsing logic - can be enhanced
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 5:  # Minimum length
                # Try to identify brand and product type
                words = line.split()
                if len(words) >= 2:
                    products.append(ProductDetection(
                        name=line,
                        brand=words[0] if words else "Unknown",
                        category="Product",
                        confidence=0.6,
                        description=line,
                        attributes={"source": "text_analysis"}
                    ))
        
        return products[:5]  # Limit to top 5
    
    def find_similar_products(self, detected_products: List[ProductDetection], search_query: str) -> List[ProductDetection]:
        """Find products similar to detected ones that match search query"""
        similar_products = []
        
        search_lower = search_query.lower()
        
        for product in detected_products:
            # Calculate similarity score
            similarity_score = 0.0
            
            # Check brand match
            if product.brand.lower() in search_lower:
                similarity_score += 0.4
            
            # Check category match
            if product.category.lower() in search_lower:
                similarity_score += 0.3
            
            # Check name match
            name_words = product.name.lower().split()
            search_words = search_lower.split()
            
            common_words = set(name_words) & set(search_words)
            if common_words:
                similarity_score += 0.3 * (len(common_words) / len(search_words))
            
            if similarity_score > 0.5:  # Threshold for similarity
                product.confidence = similarity_score
                similar_products.append(product)
        
        # Sort by similarity score
        similar_products.sort(key=lambda x: x.confidence, reverse=True)
        
        return similar_products

# === Integration Function ===
def enhanced_product_detection(image_path: str, query: str = "") -> Tuple[List[ProductDetection], str]:
    """
    Enhanced product detection combining Google Vision and local analysis
    
    Args:
        image_path: Path to the image file
        query: Optional query to filter/match products
        
    Returns:
        Tuple of (detected_products, analysis_summary)
    """
    detector = GoogleVisionProductDetector()
    
    # Detect products
    products = detector.detect_products_in_image(image_path)
    
    # Filter based on query if provided
    if query and products:
        similar_products = detector.find_similar_products(products, query)
        if similar_products:
            products = similar_products
    
    # Generate summary
    if products:
        summary = f"🔍 **Detected {len(products)} products:**\n\n"
        for i, product in enumerate(products[:3], 1):
            summary += f"{i}. **{product.name}** ({product.brand})\n"
            summary += f"   Category: {product.category} | Confidence: {product.confidence:.1%}\n\n"
        
        if len(products) > 3:
            summary += f"...and {len(products) - 3} more products detected.\n\n"
        
        summary += "💡 **Ask me to search for prices** of any of these products!"
    else:
        summary = "❌ No products clearly detected in this image. Try uploading a clearer image or ask a specific question."
    
    return products, summary