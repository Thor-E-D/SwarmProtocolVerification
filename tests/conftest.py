# tests/conftest.py
import sys
import os

# Add the src directory to the system path so it can be imported in all tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
