from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List, Union, Tuple
from collections import OrderedDict, deque
import numpy as np
import time
from .backend import Backend, get_best_backend, is_backend_available


