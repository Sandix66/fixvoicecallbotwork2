import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent

# Initialize Firebase Admin SDK
cred = credentials.Certificate(ROOT_DIR / 'config' / 'firebase_config.json')
firebase_app = firebase_admin.initialize_app(cred)

# Get Firestore client
db = firestore.client()

def get_firestore_db():
    """Get Firestore database instance"""
    return db

def get_firebase_auth():
    """Get Firebase Auth instance"""
    return auth