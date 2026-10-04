import functions_framework
import googlemaps
import json
import csv
from io import StringIO
from google.cloud import storage
from datetime import datetime
import os

API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'absa-reviews')

# Define your branches/locations to collect reviews from
# Add your own locations here following this format:
BRANCHES = [
    {"id": 1, "name": "Example Branch 1", "query": "Your business name Location 1 City"},
    {"id": 2, "name": "Example Branch 2", "query": "Your business name Location 2 City"},
    # Add more branches as needed
]

# Example format:
# {"id": 1, "name": "Coffee Shop - Downtown", "query": "My Coffee Shop Downtown Riyadh"}
# {"id": 2, "name": "Restaurant - Mall", "query": "My Restaurant King Abdullah Mall Riyadh"}

def clean_text(text):
    """إزالة newlines"""
    if not text or not isinstance(text, str):
        return text
    return ' '.join(text.split())

@functions_framework.http
def gmaps_multi_collector(request):
    """Collector - searches by branch name"""
    try:
        if request.method == 'OPTIONS':
            return ('', 204, {'Access-Control-Allow-Origin': '*'})

        gmaps = googlemaps.Client(key=API_KEY)
        
        all_reviews = []
        successful_branches = 0
        failed_branches = []
        
        print(f"🚀 Collecting from {len(BRANCHES)} branches...")
        
        for branch in BRANCHES:
            branch_id = branch['id']
            branch_name = branch['name']
            query = branch['query']
            
            print(f"\n📍 {branch_name}")
            
            try:
                # ✅ البحث بالاسم بدل place_id
                search_result = gmaps.places(
                    query=query,
                    language='ar',
                    region='sa'
                )
                
                if not search_result.get('results'):
                    print(f"   ❌ Not found")
                    failed_branches.append(branch_name)
                    continue
                
                place = search_result['results'][0]
                place_id = place['place_id']
                
                print(f"   🔍 Found: {place.get('name', '')}")
                
                # جلب التفاصيل والمراجعات
                place_details = gmaps.place(
                    place_id=place_id,
                    fields=['name', 'formatted_address', 'formatted_phone_number', 
                           'rating', 'user_ratings_total', 'reviews'],
                    language='ar'
                )
                
                if 'result' not in place_details:
                    failed_branches.append(branch_name)
                    continue
                
                details = place_details['result']
                reviews = details.get('reviews', [])
                
                if not reviews:
                    print(f"   ⚠️  No reviews")
                    continue
                
                # جمع المراجعات
                for review in reviews[:5]:
                    review_data = {
                        'data_source': 'gmaps',
                        'branch_id': branch_id,
                        'branch_name': branch_name,
                        'place_name': details.get('name', branch_name),
                        'place_id': place_id,
                        'address': clean_text(details.get('formatted_address', '')),
                        'phone': clean_text(details.get('formatted_phone_number', '')),
                        'overall_rating': details.get('rating', 0),
                        'total_user_ratings': details.get('user_ratings_total', 0),
                        'author_name': clean_text(review.get('author_name', '')),
                        'author_url': review.get('author_url', ''),
                        'rating': review.get('rating', 0),
                        'raw_review': clean_text(review.get('text', '')),
                        'time': review.get('time', ''),
                        'relative_time': clean_text(review.get('relative_time_description', '')),
                        'language': review.get('language', 'ar'),
                        'collected_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    }
                    
                    all_reviews.append(review_data)
                
                successful_branches += 1
                print(f"   ✅ {len(reviews[:5])} reviews")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                failed_branches.append(branch_name)
        
        if not all_reviews:
            return json.dumps({
                'status': 'success',
                'reviews_collected': 0,
                'message': 'No reviews found'
            }), 200
        
        # حفظ CSV
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=all_reviews[0].keys(), quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(all_reviews)
        
        # رفع لـ GCS
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gmaps/reviews_all_branches_{timestamp}.csv"
        
        blob = bucket.blob(filename)
        blob.upload_from_string(output.getvalue(), content_type='text/csv')
        
        print(f"\n✅ Saved: {filename}")
        print(f"📝 Total: {len(all_reviews)} reviews")
        
        return json.dumps({
            'status': 'success',
            'reviews_collected': len(all_reviews),
            'branches_successful': successful_branches,
            'branches_total': len(BRANCHES),
            'branches_failed': len(failed_branches),
            'failed_branches': failed_branches,
            'file': filename
        }), 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(traceback.format_exc())
        return json.dumps({'status': 'error', 'error': str(e)}), 500
