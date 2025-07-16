import re
from typing import Dict, List, Optional
from openai import OpenAI
from app.database import supabase
from app.config import settings

class ExpenseCategorizer:
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        self.category_keywords = {
            "Food": [
                "food", "meal", "lunch", "dinner", "breakfast", "snack", "restaurant", "cafe", "coffee",
                "pizza", "burger", "sandwich", "vegetables", "fruits", "milk", "bread",
                "rice", "dal", "curry", "biryani", "dosa", "idli", "samosa", "tea", "juice",
                "swiggy", "zomato", "uber eats", "foodpanda", "dominos", "kfc", "mcdonalds",
                "hotel", "dhaba", "canteen", "mess", "tiffin", "paratha", "roti", "chapati"
            ],
            "Grocery": [
                "grocery", "groceries", "supermarket", "market", "bazaar", "store", "shop",
                "reliance fresh", "big bazaar", "more", "dmart", "spencer", "nature basket",
                # Proteins & Meat
                "chicken", "mutton", "lamb", "beef", "pork", "fish", "seafood", "prawns", "crab",
                "egg", "eggs", "paneer", "tofu", "protein",
                # Fruits
                "apple", "banana", "orange", "mango", "grapes", "strawberry", "watermelon", "pineapple",
                "papaya", "guava", "kiwi", "pomegranate", "lemon", "lime", "coconut", "dates",
                # Vegetables
                "potato", "onion", "tomato", "carrot", "cabbage", "spinach", "broccoli", "cauliflower",
                "peas", "beans", "corn", "cucumber", "pepper", "chilli", "ginger", "garlic",
                # Grains & Staples
                "wheat", "flour", "oats", "quinoa", "barley", "pulses", "lentils", "chickpeas",
                # Dairy & Alternatives
                "yogurt", "curd", "cheese", "butter", "cream", "ghee", "almond milk", "soy milk",
                # Household items often bought at grocery stores
                "detergent", "soap", "shampoo", "toothpaste", "tissue", "toilet paper", "oil", "salt", "sugar", "spices"
            ],
            "Transport": [
                "transport", "uber", "ola", "taxi", "cab", "bus", "train", "metro", "auto",
                "rickshaw", "fuel", "petrol", "diesel", "gas", "parking", "toll", "flight",
                "airport", "railway", "ticket", "booking", "travel", "commute", "vehicle",
                "bike", "car", "scooter", "motorcycle", "rapido", "bounce", "yulu"
            ],
            "Entertainment": [
                "movie", "cinema", "theater", "concert", "show", "game", "gaming", "netflix",
                "prime", "hotstar", "spotify", "youtube", "subscription", "entertainment",
                "fun", "party", "club", "bar", "pub", "bowling", "sports", "gym", "fitness",
                "book", "magazine", "newspaper", "music", "album", "ticket", "event"
            ],
            "Shopping": [
                "shopping", "clothes", "shirt", "pants", "dress", "shoes", "bag", "accessories",
                "amazon", "flipkart", "myntra", "ajio", "nykaa", "electronics", "mobile",
                "laptop", "computer", "headphones", "charger", "cable", "gadget", "appliance",
                "furniture", "home", "decoration", "gift", "present", "online", "store", "mall"
            ],
            "Healthcare": [
                "doctor", "hospital", "clinic", "medicine", "pharmacy", "medical", "health",
                "checkup", "consultation", "treatment", "surgery", "dental", "dentist",
                "eye", "optician", "glasses", "test", "lab", "blood", "xray", "scan",
                "physiotherapy", "therapy", "massage", "wellness", "vitamins", "supplements"
            ],
            "Utilities": [
                "electricity", "water", "gas", "internet", "wifi", "phone", "mobile", "postpaid",
                "prepaid", "recharge", "bill", "utility", "maintenance", "repair", "service",
                "cleaning", "laundry", "rent", "emi", "loan", "insurance", "bank", "charges",
                "fee", "subscription", "premium", "payment", "transfer"
            ],
            "Education": [
                "education", "school", "college", "university", "course", "class", "tuition",
                "coaching", "training", "workshop", "seminar", "conference", "book", "notebook",
                "pen", "pencil", "stationery", "fees", "admission", "exam", "test", "study",
                "online course", "udemy", "coursera", "skill", "learning", "certificate"
            ]
        }
    
    def categorize_expense(self, note: str, user_id: str) -> Optional[str]:
        """
        Categorize expense using Claude AI with fallback to keyword matching
        Returns category_id if found, None otherwise
        """
        try:
            # Get user's categories
            categories_result = supabase.table('categories').select('*').eq('user_id', user_id).execute()
            if not categories_result.data:
                return None
            
            user_categories = {cat['name']: cat['id'] for cat in categories_result.data}
            category_names = list(user_categories.keys())
            
            # Try OpenAI categorization first
            print(f"🤖 Attempting OpenAI categorization for: '{note}'")
            print(f"📋 Available categories: {category_names}")
            openai_category = self._categorize_with_openai(note, category_names)
            print(f"🎯 OpenAI returned category: '{openai_category}'")
            
            if openai_category and openai_category in user_categories:
                category_id = user_categories[openai_category]
                print(f"✅ OpenAI categorization successful: '{openai_category}' -> ID: {category_id}")
                return category_id
            else:
                print(f"❌ OpenAI category '{openai_category}' not found in user categories: {list(user_categories.keys())}")
            
            # Fallback to keyword matching
            print(f"OpenAI failed, using keyword fallback for: '{note}'")
            fallback_category = self._categorize_with_keywords(note, user_categories)
            print(f"Keyword fallback result: {fallback_category}")
            return fallback_category
            
        except Exception as e:
            print(f"Error in categorization: {e}")
            print(f"Error details - Note: '{note}', User ID: {user_id}")
            # Final fallback to keyword matching
            try:
                categories_result = supabase.table('categories').select('*').eq('user_id', user_id).execute()
                if categories_result.data:
                    user_categories = {cat['name']: cat['id'] for cat in categories_result.data}
                    fallback_result = self._categorize_with_keywords(note, user_categories)
                    print(f"Fallback categorization result: {fallback_result}")
                    return fallback_result
            except Exception as fallback_error:
                print(f"Fallback categorization also failed: {fallback_error}")
            return None
    
    def _categorize_with_openai(self, note: str, available_categories: List[str]) -> Optional[str]:
        """
        Use OpenAI to categorize the expense
        """
        try:
            categories_str = ", ".join(available_categories)
            
            prompt = f"""You are an expense categorization expert for Indian users. 

            Expense note: "{note}"
            Available categories: {categories_str}

            Rules:
            1. Choose ONLY from the available categories
            2. Consider Indian context (swiggy=food, ola=transport, etc.)
            3. Consider: raw ingredients like chicken, fruits, vegetables = Grocery
            4. Consider: prepared meals, restaurant food = Food
            5. If unclear, prefer "Other" if available
            6. Respond with just the category name, nothing else

            Category:"""
            
            print(f"🔤 Sending to OpenAI with prompt: {prompt[:200]}...")
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.1
            )
            
            category = response.choices[0].message.content.strip()
            print(f"🤖 OpenAI raw response: '{category}'")
            print(f"🔍 Checking if '{category}' is in available categories: {available_categories}")
            
            # Validate the response is in available categories
            if category in available_categories:
                print(f"✅ Exact match found: '{category}'")
                return category
            
            # Try case-insensitive matching
            category_lower = category.lower()
            print(f"🔄 Trying case-insensitive matching for: '{category_lower}'")
            for cat in available_categories:
                if cat.lower() == category_lower:
                    print(f"✅ Case-insensitive match found: '{category}' -> '{cat}'")
                    return cat
            
            print(f"❌ No match found for '{category}' in available categories")
            return None
            
        except Exception as e:
            print(f"OpenAI categorization failed: {e}")
            # Log the specific error for debugging
            print(f"Error details - Note: '{note}', Available categories: {available_categories}")
            return None
    
    def _categorize_with_keywords(self, note: str, user_categories: Dict[str, str]) -> Optional[str]:
        """
        Fallback keyword-based categorization
        """
        clean_note = self._clean_text(note)
        category_scores = {}
        
        print(f"Keyword matching for: '{note}' -> cleaned: '{clean_note}'")
        
        for category_name, category_id in user_categories.items():
            score = self._calculate_category_score(clean_note, category_name)
            if score > 0:
                category_scores[category_id] = score
                print(f"  {category_name}: {score}")
        
        print(f"All scores: {category_scores}")
        
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])
            print(f"Best category ID: {best_category[0]} (score: {best_category[1]})")
            return best_category[0]
        
        # Default to "Other" category
        other_id = user_categories.get("Other")
        print(f"No matches found, defaulting to Other (ID: {other_id})")
        return other_id
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for better matching"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and extra spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _calculate_category_score(self, note: str, category_name: str) -> float:
        """Calculate similarity score between note and category"""
        if category_name not in self.category_keywords:
            return 0.0
        
        keywords = self.category_keywords[category_name]
        words_in_note = note.split()
        
        score = 0.0
        total_words = len(words_in_note)
        
        if total_words == 0:
            return 0.0
        
        for keyword in keywords:
            # Exact match
            if keyword in note:
                score += 1.0
            
            # Partial match (for compound words)
            for word in words_in_note:
                if keyword in word or word in keyword:
                    score += 0.5
                    break
        
        # Normalize score by note length
        return score / max(total_words, 1)
    
    def get_category_suggestions(self, note: str) -> List[Dict[str, str]]:
        """Get top 3 category suggestions for a note"""
        clean_note = self._clean_text(note)
        category_scores = {}
        
        for category_name, keywords in self.category_keywords.items():
            score = self._calculate_category_score(clean_note, category_name)
            if score > 0:
                category_scores[category_name] = score
        
        # Sort by score and return top 3
        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        return [{"name": cat, "confidence": round(score * 100, 1)} for cat, score in sorted_categories[:3]]
    
    def get_category_suggestions_with_openai(self, note: str) -> List[Dict[str, str]]:
        """Get AI-powered category suggestions with confidence scores using OpenAI"""
        try:
            prompt = f"""Analyze this expense note and suggest the top 3 most likely categories with confidence scores.

            Expense note: "{note}"
            
            Available categories: Food, Transport, Entertainment, Shopping, Healthcare, Utilities, Education, Other, Grocery
            
            Consider Indian context and category distinctions:
            - Swiggy, Zomato, restaurants = Food
            - Raw ingredients, fruits, vegetables, supermarket = Grocery  
            - Ola, Uber, BMTC = Transport  
            - Netflix, BookMyShow = Entertainment
            - Amazon, Flipkart = Shopping
            
            Respond in this exact format:
            Category1:Confidence1
            Category2:Confidence2  
            Category3:Confidence3
            
            Example:
            Grocery:85
            Food:10
            Other:5"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.2
            )
            
            suggestions = []
            lines = response.choices[0].message.content.strip().split('\n')
            
            for line in lines[:3]:  # Top 3 only
                if ':' in line:
                    parts = line.split(':')
                    if len(parts) == 2:
                        category = parts[0].strip()
                        try:
                            confidence = float(parts[1].strip())
                            suggestions.append({
                                "name": category,
                                "confidence": confidence
                            })
                        except ValueError:
                            continue
            
            return suggestions if suggestions else self.get_category_suggestions(note)
            
        except Exception as e:
            print(f"OpenAI suggestions failed: {e}")
            print(f"Suggestions error details - Note: '{note}'")
            # Fallback to keyword-based suggestions
            return self.get_category_suggestions(note)

# Global instance
categorizer = ExpenseCategorizer()