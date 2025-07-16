import re
from typing import Dict, List, Optional
from anthropic import Anthropic
from app.database import supabase
from app.config import settings

class ExpenseCategorizer:
    def __init__(self):
        self.anthropic_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        
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
            
            # Try Claude AI categorization first
            claude_category = self._categorize_with_claude(note, category_names)
            if claude_category and claude_category in user_categories:
                return user_categories[claude_category]
            
            # Fallback to keyword matching
            fallback_category = self._categorize_with_keywords(note, user_categories)
            return fallback_category
            
        except Exception as e:
            print(f"Error in categorization: {e}")
            # Final fallback to keyword matching
            try:
                categories_result = supabase.table('categories').select('*').eq('user_id', user_id).execute()
                if categories_result.data:
                    user_categories = {cat['name']: cat['id'] for cat in categories_result.data}
                    return self._categorize_with_keywords(note, user_categories)
            except:
                pass
            return None
    
    def _categorize_with_claude(self, note: str, available_categories: List[str]) -> Optional[str]:
        """
        Use Claude Sonnet to categorize the expense
        """
        try:
            categories_str = ", ".join(available_categories)
            
            prompt = f"""You are an expense categorization expert for Indian users. 

            Expense note: "{note}"
            Available categories: {categories_str}

            Rules:
            1. Choose ONLY from the available categories
            2. Consider Indian context (swiggy=food, ola=transport, etc.)
            3. If unclear, prefer "Other" if available
            4. Respond with just the category name, nothing else

            Category:"""
            
            response = self.anthropic_client.completions.create(
                model="claude-2",
                max_tokens_to_sample=10,
                temperature=0.1,
                prompt=f"\n\nHuman: {prompt}\n\nAssistant:"
            )
            
            category = response.completion.strip()
            
            # Validate the response is in available categories
            if category in available_categories:
                return category
            
            # Try case-insensitive matching
            category_lower = category.lower()
            for cat in available_categories:
                if cat.lower() == category_lower:
                    return cat
            
            return None
            
        except Exception as e:
            print(f"Claude categorization failed: {e}")
            return None
    
    def _categorize_with_keywords(self, note: str, user_categories: Dict[str, str]) -> Optional[str]:
        """
        Fallback keyword-based categorization
        """
        clean_note = self._clean_text(note)
        category_scores = {}
        
        for category_name, category_id in user_categories.items():
            score = self._calculate_category_score(clean_note, category_name)
            if score > 0:
                category_scores[category_id] = score
        
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])
            return best_category[0]
        
        # Default to "Other" category
        return user_categories.get("Other")
    
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
    
    def get_category_suggestions_with_claude(self, note: str) -> List[Dict[str, str]]:
        """Get AI-powered category suggestions with confidence scores using Claude"""
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
            
            response = self.anthropic_client.completions.create(
                model="claude-2",
                max_tokens_to_sample=50,
                temperature=0.2,
                prompt=f"\n\nHuman: {prompt}\n\nAssistant:"
            )
            
            suggestions = []
            lines = response.completion.strip().split('\n')
            
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
            print(f"Claude suggestions failed: {e}")
            # Fallback to keyword-based suggestions
            return self.get_category_suggestions(note)

# Global instance
categorizer = ExpenseCategorizer()