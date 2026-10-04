import functions_framework
import requests
import json
import os
import re

# ✅ الـ API الصحيح
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
API_KEY = os.environ.get('GEMINI_API_KEY')

@functions_framework.http
def gemini_absa_enricher(request):
    try:
        if request.method == 'OPTIONS':
            return ('', 204, {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Content-Type',
            })

        request_json = request.get_json(silent=True)
        
        if not request_json or 'normalized_text' not in request_json:
            return json.dumps({"error": "Missing normalized_text"}), 400

        normalized_text = request_json['normalized_text']
        
        review_length = len(normalized_text)
        print(f"📏 Review length: {review_length} characters")
        
        # Generic ABSA prompt for any business type
        PROMPT_TEMPLATE = (
            "ROLE: You are a highly specialized AI Data Analyst expert in Aspect-Based Sentiment Analysis (ABSA), "
            "focusing on Arabic language reviews for businesses and services.\n\n"
            
            "OBJECTIVE: Analyze customer reviews to identify specific operational aspects and their sentiment. "
            "This analysis helps businesses understand customer feedback and improve their services.\n\n"
            
            "CONTEXT: Users provide feedback in various Arabic dialects (Saudi, Egyptian, Levantine, etc.) often using local slang or "
            "sarcastic expressions. We need to convert this into a clean, machine-readable dataset.\n\n"
            
            "TASK: Your mission is to decompose the 'USER REVIEW' into its core components. For every record:\n"
            "1. Identify the 'Aspects' mentioned (e.g., cleanliness, service, price, quality).\n"
            "2. Assign a 'Polarity' (إيجابي, سلبي, محايد) for EACH identified aspect.\n"
            "3. CRITICAL: Detect sarcasm and double-meanings to ensure negative experiences are not misclassified as positive.\n\n"
            
            "POSSIBLE ASPECTS (11 aspects ONLY - extract ONLY these):\n"
            "1. النظافة - Cleanliness of facilities, premises, restrooms\n"
            "2. الجودة - Quality of products, services, or equipment\n"
            "3. الموظفين - Staff competence, professionalism, interaction\n"
            "4. خدمة العملاء - Customer service, reception, management, treatment\n"
            "5. الزحام - Crowding, waiting time, availability\n"
            "6. السعر - Price, cost, value for money, offers\n"
            "7. الموقع - Location, accessibility, area, transportation\n"
            "8. الصيانة - Maintenance, repairs, facility upkeep\n"
            "9. المرافق - Amenities, parking, facilities, conveniences\n"
            "10. التنوع - Variety, options, selection, diversity\n"
            "11. ساعات العمل - Operating hours, opening times, flexibility\n\n"
            
            "CRITICAL RULES:\n"
            "1. Extract ONLY aspects explicitly mentioned in the review\n"
            "2. Do NOT extract generic aspects - map them to specific aspects above\n"
            "3. If review mentions variety/options/selection → use 'التنوع'\n"
            "4. If review mentions working hours/opening times → use 'ساعات العمل'\n"
            "5. Extract ONLY from the 11 aspects listed above - no other aspects allowed\n\n"
            
            "CONSTRAINTS:\n"
            "1. Output ONLY a raw JSON array of objects. No introductory or concluding text.\n"
            "2. Each object must have keys: 'aspect' and 'polarity'.\n"
            "3. Use exact Arabic terminology from the 11 aspects above.\n"
            "4. Only include aspects that are explicitly or implicitly mentioned in the review.\n"
            "5. NEVER use aspects not in the list.\n\n"
            
            "EXAMPLES:\n\n"
            "Example 1:\n"
            "Review: 'المكان نظيف جداً بس الموظفين تعاملهم سيء والسعر مبالغ فيه.'\n"
            'Output: [{{"aspect": "النظافة", "polarity": "إيجابي"}}, {{"aspect": "الموظفين", "polarity": "سلبي"}}, {{"aspect": "السعر", "polarity": "سلبي"}}]\n\n'
            
            "Example 2:\n"
            "Review: 'الجودة ممتازة والموظفين يشرحون زين، بس ساعات العمل قصيرة ويسكرون بدري'\n"
            'Output: [{{"aspect": "الجودة", "polarity": "إيجابي"}}, {{"aspect": "الموظفين", "polarity": "إيجابي"}}, {{"aspect": "ساعات العمل", "polarity": "سلبي"}}]\n\n'
            
            "Example 3:\n"
            "Review: 'المكان عموماً حلو والخدمة منظمة'\n"
            'Output: [{{"aspect": "خدمة العملاء", "polarity": "إيجابي"}}]\n\n'
            
            "---\n"
            "USER REVIEW: {}\n\n"
            "Output (JSON array only, no other text):"
        )
        
        final_prompt = PROMPT_TEMPLATE.format(normalized_text)

        payload = {
            "contents": [{"parts": [{"text": final_prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.8,
                "topK": 40,
                "maxOutputTokens": 2048
            }
        }

        url = f"{API_URL}?key={API_KEY}"
        headers = {'Content-Type': 'application/json'}
        
        response = requests.post(url, headers=headers, json=payload, timeout=180)
        
        print(f"✅ Gemini API Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Gemini Error: {response.text[:500]}")
            return json.dumps([{
                "aspect": "System",
                "polarity": f"HTTP_{response.status_code}"
            }]), 200
        
        result = response.json()
        
        if 'candidates' not in result or not result['candidates']:
            return json.dumps([{"aspect": "System", "polarity": "NO_CANDIDATES"}]), 200
        
        if 'content' not in result['candidates'][0]:
            return json.dumps([{"aspect": "System", "polarity": "NO_CONTENT"}]), 200
        
        output_text = result['candidates'][0]['content']['parts'][0]['text']
        
        # تنظيف
        output_text = output_text.strip()
        output_text = re.sub(r'^```json\s*', '', output_text, flags=re.MULTILINE | re.IGNORECASE)
        output_text = re.sub(r'^```\s*', '', output_text, flags=re.MULTILINE)
        output_text = re.sub(r'\s*```\s*$', '', output_text, flags=re.MULTILINE)
        
        if output_text.startswith('"') and output_text.endswith('"'):
            output_text = output_text[1:-1]
        
        output_text = output_text.replace('\\"', '"')
        output_text = output_text.replace('\\n', '\n')
        output_text = output_text.replace('\\\\', '\\')
        
        match = re.search(r'(\[.*\])', output_text, re.DOTALL)
        if match:
            output_text = match.group(1)
        
        output_text = output_text.strip()
        
        try:
            parsed = json.loads(output_text)
            
            if not isinstance(parsed, list):
                return json.dumps([{"aspect": "System", "polarity": "NOT_ARRAY"}]), 200
            
            valid_aspects = []
            for item in parsed:
                if isinstance(item, dict) and 'aspect' in item and 'polarity' in item:
                    valid_aspects.append(item)
            
            if not valid_aspects:
                return json.dumps([{"aspect": "System", "polarity": "NO_VALID_ASPECTS"}]), 200
            
            print(f"✅ SUCCESS: {len(valid_aspects)} aspects")
            
            return json.dumps(valid_aspects, ensure_ascii=False), 200, {
                'Content-Type': 'application/json; charset=utf-8'
            }
            
        except json.JSONDecodeError as je:
            print(f"❌ JSON ERROR: {je}")
            return json.dumps([{"aspect": "System", "polarity": "JSON_ERROR"}]), 200

    except Exception as e:
        print(f"❌ EXCEPTION: {type(e).__name__}: {e}")
        return json.dumps([{"aspect": "System", "polarity": "INTERNAL_ERROR"}]), 200
