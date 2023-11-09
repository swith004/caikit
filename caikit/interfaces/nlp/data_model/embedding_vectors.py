# Copyright The Caikit Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Data structures for embedding vector representations
"""
# Standard
from dataclasses import dataclass

# First Party
from caikit.core import DataObjectBase, dataobject
from caikit.core.exceptions import error_handler
import alog

# Local
from ...common.data_model import Vector1D

log = alog.use_channel("DATAM")
error = error_handler.get(log)


@dataobject(package="caikit_data_model.caikit_nlp")
@dataclass
class EmbeddingResult(DataObjectBase):
    """Result from text embedding task"""

    result: Vector1D
