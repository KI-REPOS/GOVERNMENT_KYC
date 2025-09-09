# backend/kyc_app/views.py
import json
import numpy as np
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.middleware.csrf import get_token
from django.utils import timezone
from .models import User, APIToken
from .mongo_utils import create_user_in_mongo, get_user_from_mongo, update_user_wallet

# Get CSRF token
@csrf_exempt
def get_csrf_token(request):
    return JsonResponse({'csrfToken': get_token(request)})

# Calculate cosine similarity between two vectors
def cosine_similarity(vec1, vec2):
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    return dot_product / (norm_vec1 * norm_vec2)

@csrf_exempt
@require_http_methods(["POST"])
def register_user(request):
    try:
        data = json.loads(request.body)
        gov_id = data.get('gov_id')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')
        password = data.get('password')
        photo_data = data.get('photo')
        embedding = data.get('embedding')
        
        if User.objects.filter(gov_id=gov_id).exists():
            return JsonResponse({'error': 'User with this Gov ID already exists'}, status=400)
            
        if User.objects.filter(email=email).exists():
            return JsonResponse({'error': 'User with this email already exists'}, status=400)
        
        # Create user in SQLite (for authentication)
        user = User.objects.create_user(
            username=gov_id,
            gov_id=gov_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password
        )
        
        # Store detailed user data in MongoDB
        mongo_id = create_user_in_mongo(gov_id, first_name, last_name, email, photo_data, embedding)
        user.mongo_id = mongo_id
        user.save()
        
        # Auto-login the user
        login(request, user)
        
        return JsonResponse({
            'message': 'User registered successfully', 
            'user_id': user.id,
            'gov_id': user.gov_id
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def generate_token(request):
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        
        user = get_object_or_404(User, id=user_id)
        
        # Create a new token that expires in 3 minutes
        expires_at = timezone.now() + timedelta(minutes=3)
        token = APIToken.objects.create(
            user=user,
            expires_at=expires_at
        )
        
        # Generate the API link
        api_link = f"{request.scheme}://{request.get_host()}/api/verify/?token={token.id}"
        
        return JsonResponse({
            'token': str(token.id),
            'api_link': api_link,
            'expires_at': expires_at.isoformat()
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def verify_kyc(request):
    try:
        data = json.loads(request.body)
        token_str = data.get('token')
        embedding = data.get('embedding')
        wallet_address = data.get('wallet')
        
        if not all([token_str, embedding, wallet_address]):
            return JsonResponse({
                'status': 'no', 
                'message': 'Missing required parameters: token, embedding, or wallet'
            }, status=400)
        
        # Get the token
        try:
            token = APIToken.objects.get(id=token_str)
        except APIToken.DoesNotExist:
            return JsonResponse({
                'status': 'no', 
                'message': 'Invalid token'
            })
        
        # Check if token is valid
        if not token.is_valid():
            return JsonResponse({
                'status': 'no', 
                'message': 'Token expired or already used'
            })
        
        # Get user data from MongoDB
        user_data = get_user_from_mongo(gov_id=token.user.gov_id)
        
        if not user_data or 'embedding' not in user_data:
            return JsonResponse({
                'status': 'no', 
                'message': 'No face data found for user'
            })
        
        # Convert stored embedding to numpy array
        stored_embedding = np.array(user_data['embedding'], dtype=np.float32)
        
        # Convert received embedding to numpy array
        received_embedding = np.array(embedding, dtype=np.float32)
        
        # Compare embeddings using cosine similarity
        similarity = cosine_similarity(stored_embedding, received_embedding)
        
        # Threshold for face matching (adjust as needed)
        if similarity < 0.6:
            return JsonResponse({
                'status': 'no', 
                'message': 'Face verification failed'
            })
        
        # Mark token as used
        token.used = True
        token.save()
        
        # Update user's wallet address in MongoDB
        update_user_wallet(token.user.gov_id, wallet_address)
        
        return JsonResponse({
            'status': 'yes', 
            'message': 'KYC verified successfully',
            'wallet_address': wallet_address
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'no', 
            'message': f'Error during verification: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_user(request, user_id):
    try:
        user = get_object_or_404(User, id=user_id)
        user_data = get_user_from_mongo(gov_id=user.gov_id)
        
        if not user_data:
            return JsonResponse({'error': 'User data not found in MongoDB'}, status=404)
        
        return JsonResponse({
            'gov_id': user.gov_id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'wallet_address': user_data.get('wallet_address'),
            'photo': user_data.get('photo')
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def profile_view(request):
    return render(request, 'profile.html', {'user': request.user})

from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def register_page(request):
    """Serve the HTML registration form."""
    return render(request, "index.html")


def test_view(request):
    return HttpResponse("Django is working! If you see this, the server is running correctly.")