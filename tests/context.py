import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import converter as converter
from POAGraph import POAGraph
from Node import Node
# from POReader import POReader
from Sequence import Source
from Multialignment import Multialignment
import toolkit as toolkit
import maf_reader as maf_reader
# from POAGraphVisualizer import POAGraphVisualizer