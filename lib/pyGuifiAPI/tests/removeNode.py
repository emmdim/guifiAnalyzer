#!/usr/bin/env python
import sys
sys.path.append('..')

from guifiConfig import *
from api import *

if len(sys.argv) != 2:
    print 'Remove an existing node'
    print 'Usage: %s <node_id>' % sys.argv[0]
    sys.exit(1)

g = GuifiAPI(USERNAME, PASSWORD, secure=SECURE)
g.auth()

try:
    g.removeNode(sys.argv[1])
except GuifiApiError, e:
    print e.reason
