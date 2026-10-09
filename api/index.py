"""
Vercel Serverless Function entrypoint for Flask.
"""

from app import app

# Vercel looks for the WSGI application callable
app = app
