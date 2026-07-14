#!/usr/bin/env python3
"""Debug script for CI issues"""

import sys
import os
import subprocess

def check_environment():
    """Check the environment"""
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    
    # Check critical packages
    packages = ['pytest', 'pandas', 'fastapi', 'streamlit', 'sqlalchemy']
    for pkg in packages:
        try:
            __import__(pkg)
            print(f"✓ {pkg} installed")
        except ImportError:
            print(f"✗ {pkg} NOT installed")
            return False
    
    return True

def run_simple_test():
    """Run a simple test"""
    try:
        # Test basic imports
        import pandas as pd
        import fastapi
        import streamlit as st
        from sqlalchemy import create_engine
        
        # Test basic functionality
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        assert len(df) == 3
        
        # Test API
        from fastapi import FastAPI
        app = FastAPI()
        
        print("✓ Basic functionality test passed")
        return True
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

def run_minimal_pytest():
    """Run minimal pytest"""
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'tests/test_api.py::test_root_endpoint',
            '-v', '--tb=short', '--no-header'
        ], capture_output=True, text=True, timeout=30)
        
        print(f"Pytest exit code: {result.returncode}")
        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("✗ Pytest timed out")
        return False
    except Exception as e:
        print(f"✗ Pytest failed: {e}")
        return False

if __name__ == "__main__":
    print("=== CI Debug Script ===")
    
    # Set environment
    os.environ['API_KEY'] = 'test-ci-key'
    os.environ['DB_TYPE'] = 'sqlite'
    
    # Run checks
    if not check_environment():
        sys.exit(1)
    
    if not run_simple_test():
        sys.exit(1)
    
    if not run_minimal_pytest():
        sys.exit(1)
    
    print("✓ All checks passed")
