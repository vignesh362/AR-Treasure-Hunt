#!/usr/bin/env python3
"""
Simple Riddle Generator based on GPS coordinates
Uses Gemini API to identify location and generate riddles
"""

import os
import json
import requests
from typing import Dict, List, Tuple

class LocationRiddleGenerator:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
    
    def identify_place(self, latitude: float, longitude: float) -> Dict:
        """Identify place from coordinates"""
        # First, get general location info using reverse geocoding
        try:
            location_info = self._get_location_info(latitude, longitude)
            print(f"📍 General location: {location_info}")
        except:
            location_info = "Unknown location"
        
        prompt = f"""You are a precise location identification expert. Given the EXACT coordinates {latitude}, {longitude}, identify the SPECIFIC building, structure, or landmark at this precise location.

GENERAL LOCATION CONTEXT: {location_info}

IMPORTANT: 
- Be as specific as possible - identify the exact building name, not just the general area
- If it's a university building, include the specific building name and department
- If it's a landmark, include the specific monument or structure name
- Focus on what is physically located at these exact coordinates
- Use the general location context to help identify the specific building

Return ONLY valid JSON in this exact format:
{{
    "name": "Exact specific name of the building/structure",
    "type": "Type of place (building, landmark, etc.)",
    "institution": "Institution name if applicable",
    "city": "City name",
    "state": "State/Province",
    "country": "Country",
    "facts": ["specific fact 1", "specific fact 2", "specific fact 3"],
    "description": "Brief description of this specific building/structure"
}}"""
        
        response = self._call_gemini(prompt)
        
        # Clean the response to extract JSON
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:]
        if response.endswith('```'):
            response = response[:-3]
        if response.startswith('```'):
            response = response[3:]
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parsing failed, using fallback data")
            # Fallback data for Cornell coordinates (42.449268, -76.4837724)
            return {
                "name": "Cornell University Physical Sciences Building",
                "type": "University Building",
                "institution": "Cornell University",
                "city": "Ithaca",
                "state": "New York",
                "country": "United States",
                "facts": [
                    "Built in 1961, it houses the Physics and Chemistry departments",
                    "Features state-of-the-art research laboratories",
                    "Named after the famous physicist who worked here"
                ],
                "description": "A prominent academic building at Cornell University"
            }
        except Exception as e:
            print(f"⚠️ API call failed: {e}, using fallback data")
            # Fallback data for Cornell coordinates
            return {
                "name": "Cornell University Physical Sciences Building",
                "type": "University Building",
                "institution": "Cornell University",
                "city": "Ithaca",
                "state": "New York",
                "country": "United States",
                "facts": [
                    "Built in 1961, it houses the Physics and Chemistry departments",
                    "Features state-of-the-art research laboratories",
                    "Named after the famous physicist who worked here"
                ],
                "description": "A prominent academic building at Cornell University"
            }
    
    def generate_riddle(self, place_info: Dict) -> str:
        """Generate riddle based on place information"""
        prompt = f"""Create a creative riddle about this place: {place_info['name']}
        
        Place Details:
        - Type: {place_info['type']}
        - Institution: {place_info.get('institution', 'N/A')}
        - Location: {place_info['city']}, {place_info['state']}, {place_info['country']}
        - Facts: {', '.join(place_info['facts'])}
        
        Create a 2-4 line riddle that:
        1. Is challenging but solvable
        2. References specific facts about the place
        3. Rhymes if possible
        4. Hints at the place without being too obvious"""
        
        return self._call_gemini(prompt).strip()
    
    def generate_location_riddle(self, latitude: float, longitude: float) -> Dict:
        """Generate complete riddle for given coordinates"""
        print(f"🔍 Identifying place at {latitude}, {longitude}...")
        
        # Identify the place
        place_info = self.identify_place(latitude, longitude)
        print(f"✅ Found: {place_info['name']}")
        
        # Generate riddle
        print("🧩 Generating riddle...")
        riddle = self.generate_riddle(place_info)
        print(f"✅ Riddle generated!")
        
        return {
            "coordinates": {"latitude": latitude, "longitude": longitude},
            "place": place_info,
            "riddle": riddle
        }
    
    def generate_riddle_for_known_place(self, place_name: str, latitude: float, longitude: float) -> Dict:
        """Generate riddle for a known place name"""
        print(f"🧩 Generating riddle for: {place_name}")
        
        # Create place info with the known name
        place_type = "University Building" if "Building" in place_name else "Landmark"
        place_info = {
            "name": place_name,
            "type": place_type,
            "institution": "Cornell University",
            "city": "Ithaca",
            "state": "New York", 
            "country": "United States",
            "facts": self._get_place_facts(place_name),
            "description": f"A {place_type.lower()} at Cornell University"
        }
        
        # Generate riddle
        print("🧩 Generating riddle...")
        riddle = self.generate_riddle(place_info)
        print(f"✅ Riddle generated!")
        
        return {
            "coordinates": {"latitude": latitude, "longitude": longitude},
            "place": place_info,
            "riddle": riddle
        }
    
    def _get_place_facts(self, place_name: str) -> List[str]:
        """Get specific facts for known places"""
        facts_map = {
            "Physical Science Building": [
                "Built in 1961, it houses the Physics and Chemistry departments",
                "Features state-of-the-art research laboratories", 
                "Named after the famous physicist who worked here"
            ],
            "Albert R. Mann Library": [
                "Named after Cornell's first president",
                "Houses extensive collections of agricultural and life sciences materials",
                "Features modern study spaces and research facilities"
            ],
            "Animal Health Diagnostic Center": [
                "Provides veterinary diagnostic services",
                "Supports animal health research and education",
                "Features advanced laboratory facilities"
            ],
            "Herbert F. Johnson Museum of Art": [
                "Designed by I.M. Pei, features a distinctive concrete and glass design",
                "Houses over 35,000 works of art from around the world",
                "Offers stunning views of Cayuga Lake from its upper floors"
            ],
            "Baker Flagpole": [
                "A prominent landmark in the center of campus",
                "Surrounded by the Arts Quad, one of Cornell's most iconic spaces",
                "Often used as a meeting point for students and visitors"
            ]
        }
        return facts_map.get(place_name, [
            f"An important location at Cornell University",
            f"Part of the historic Cornell campus",
            f"A significant {place_name.lower()}"
        ])
    
    def _get_location_info(self, latitude: float, longitude: float) -> str:
        """Get general location info using reverse geocoding"""
        try:
            # Use a free reverse geocoding service
            url = f"https://api.bigdatacloud.net/data/reverse-geocode-client?latitude={latitude}&longitude={longitude}&localityLanguage=en"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return f"{data.get('locality', 'Unknown')}, {data.get('principalSubdivision', 'Unknown')}, {data.get('countryName', 'Unknown')}"
            else:
                return "Unknown location"
        except:
            return "Unknown location"
    
    def _call_gemini(self, prompt: str) -> str:
        """Make API call to Gemini"""
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 1024,
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}?key={self.api_key}",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"⚠️ API Error: {response.status_code}")
                print(f"Response: {response.text}")
                raise Exception(f"API Error: {response.status_code} - {response.text}")
            
            result = response.json()
            
            if 'candidates' not in result or not result['candidates']:
                raise Exception("No candidates in response")
            
            if 'content' not in result['candidates'][0]:
                raise Exception("No content in response")
            
            if 'parts' not in result['candidates'][0]['content']:
                raise Exception("No parts in content")
            
            return result['candidates'][0]['content']['parts'][0]['text']
            
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Network error: {e}")
            raise Exception(f"Network error: {e}")
        except Exception as e:
            print(f"⚠️ API call failed: {e}")
            raise Exception(f"API call failed: {e}")


def main():
    """Main function to generate riddle for given coordinates"""
    # Get API key from environment or prompt user
    api_key = "API KEY"
    if not api_key:
        api_key = input("Enter your Gemini API key: ").strip()
        if not api_key:
            print("❌ No API key provided. Exiting.")
            return

    places = {
        (42.4483579, -76.4800221): "Physical Science Building",
        (42.4483176, -76.4765426): "Albert R. Mann Library", 
        (42.4485359, -76.4667365): "Animal Health Diagnostic Center",
        (42.4498775, -76.4881075): "Herbert F. Johnson Museum of Art",
        (42.4495615, -76.4865407): "Baker Flagpole"
    }

    # Find the closest match to the input coordinates
    def find_closest_place(target_lat, target_lng, places_dict):
        min_distance = float('inf')
        closest_place = None
        
        for (lat, lng), place_name in places_dict.items():
            # Simple distance calculation
            distance = ((target_lat - lat) ** 2 + (target_lng - lng) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                closest_place = place_name
        
        return closest_place

    # Get coordinates from user or use default
    # latitude = float(input("Enter latitude (or press Enter for 42.4483579): ") or "42.4483579")
    # longitude = float(input("Enter longitude (or press Enter for -76.4800221): ") or "-76.4800221")

    # Find the mapped location name
    location_name = find_closest_place(latitude, longitude, places)
    print(f"📍 Mapped location: {location_name}")

    try:
        generator = LocationRiddleGenerator(api_key)
        result = generator.generate_riddle_for_known_place(location_name, latitude, longitude)   
        print("\n" + "="*50)
        print("🎯 LOCATION RIDDLE GENERATED")
        print("="*50)
        print(f"📍 Location: {result['place']['name']}")
        print(f"🏢 Type: {result['place']['type']}")
        print(f"🏛️ Institution: {result['place'].get('institution', 'N/A')}")
        print(f"🌍 Location: {result['place']['city']}, {result['place']['state']}, {result['place']['country']}")
        print(f"\n🧩 RIDDLE:")
        print(f'"{result["riddle"]}"')
        print(f"\n💡 Facts about this place:")
        for i, fact in enumerate(result['place']['facts'], 1):
            print(f"   {i}. {fact}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
