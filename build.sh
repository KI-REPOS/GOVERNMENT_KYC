#!/bin/bash
# Build script for Django application on Render

echo "=== Starting Build Process ==="

# Install Python dependencies
echo "1. Installing Python dependencies..."
pip install -r requirements.txt

# Apply Django migrations
echo "2. Applying Django migrations..."
python manage.py migrate

# Collect static files
echo "3. Collecting static files..."
python manage.py collectstatic --noinput

# Optional: Create superuser if doesn't exist
# echo "4. Checking if superuser exists..."
# echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin','admin@example.com','adminpassword')" | python manage.py shell

# Test MongoDB connection
echo "5. Testing MongoDB connection..."
python <<EOF
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

try:
    mongo_uri = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/gov_kyc_db')
    print(f'Connecting to MongoDB: {mongo_uri}')
    
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print('✓ MongoDB connection successful!')

    # Check if database and collection exist
    db = client['gov_kyc_db']
    collections = db.list_collection_names()
    print(f'Available collections: {collections}')

    # Create users collection if it doesn't exist
    if 'users' not in collections:
        db.create_collection('users')
        print('✓ Created users collection')

    client.close()

except ConnectionFailure as e:
    print(f'✗ MongoDB connection failed: {e}')
    exit(1)
except Exception as e:
    print(f'✗ Error: {e}')
    exit(1)
EOF

echo "6. Testing Django application..."
python manage.py check

echo "=== Build Completed Successfully ==="
