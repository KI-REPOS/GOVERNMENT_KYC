#!/bin/bash
# Build script for Django application on Render

echo "=== Starting Build Process ==="

# Install Python dependencies
echo "1. Installing Python dependencies..."
pip install -r requirements.txt

# Create migrations for custom apps (especially kyc_app with custom User model)
echo "2. Creating migrations for custom apps..."
python manage.py makemigrations kyc_app --noinput

# Apply Django migrations
echo "3. Applying Django migrations..."
python manage.py migrate --noinput

# Show migration status for debugging
echo "4. Checking migration status..."
python manage.py showmigrations

# Collect static files
echo "5. Collecting static files..."
python manage.py collectstatic --noinput

# Test MongoDB connection
echo "6. Testing MongoDB connection..."
python <<EOF
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

try:
    mongo_uri = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/gov_kyc_db')
    print(f'Connecting to MongoDB...')
    
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
    print(f'⚠️ MongoDB connection failed: {e}')
except Exception as e:
    print(f'⚠️ MongoDB error: {e}')
EOF

# Verify the kyc_app_user table exists
echo "7. Verifying database tables..."
python <<EOF
import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gov_archive_project.settings')
django.setup()

try:
    with connection.cursor() as cursor:
        # Check if kyc_app_user table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='kyc_app_user';")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print('✓ kyc_app_user table exists!')
        else:
            print('✗ kyc_app_user table does NOT exist!')
            print('Available tables:')
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            for table in tables:
                print(f'  - {table[0]}')
            
except Exception as e:
    print(f'Error checking tables: {e}')
EOF

echo "8. Testing Django application..."
python manage.py check

echo "=== Build Completed ==="