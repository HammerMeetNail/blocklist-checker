import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
from web.checker import app


def test_min():
    assert 1 == 1
