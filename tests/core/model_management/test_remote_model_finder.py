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
"""
Tests for the RemoteModelFinder
"""

# Standard
from contextlib import contextmanager

# Third Party
import pytest

# First Party
from aconfig import Config

# Local
from caikit.core.model_management.remote_model_finder import RemoteModelFinder
from caikit.core.modules import RemoteModuleConfig
from caikit.runtime.model_management.model_manager import ModelManager
from tests.conftest import random_test_id
from tests.fixtures import Fixtures
from tests.runtime.conftest import (
    generate_tls_configs,
    multi_task_model_id,
    open_port,
    runtime_grpc_test_server,
    runtime_http_test_server,
    sample_task_model_id,
)

## Test Helpers #######################################################################


@pytest.fixture
def sample_module_id(good_model_path) -> str:
    """Loaded model ID using model manager load model implementation"""
    model_id = random_test_id()
    model_manager = ModelManager.get_instance()
    # model load test already tests with archive - just using a model path here
    local_model = model_manager.load_model(
        model_id,
        local_model_path=good_model_path,
        model_type=Fixtures.get_good_model_type(),  # eventually we'd like to be determining the type from the model itself...
    )
    yield local_model.model().MODULE_ID


@contextmanager
def temp_finder(
    multi_finder_name="remote",
    multi_finder_cfg=None,
    connection_cfg=None,
):
    # Provide defaults
    if not multi_finder_cfg:
        multi_finder_cfg = {"discover_models": True, "supported_models": {}}

    if connection_cfg:
        multi_finder_cfg["connection"] = connection_cfg

    if "connection" not in multi_finder_cfg:
        multi_finder_cfg["connection"] = {
            "hostname": "localhost",
            "protocol": "grpc",
        }

    yield RemoteModelFinder(Config(multi_finder_cfg), multi_finder_name)


## Tests #######################################################################


def test_remote_module_finder_static_model(sample_module_id):
    """Test to ensure static supported_models definition works as expected"""
    with temp_finder(
        multi_finder_cfg={
            "discover_models": False,
            "supported_models": {"sample": sample_module_id},
        }
    ) as finder:
        config = finder.find_model("sample")
        # Check RemoteModuleConfig has the right type, name, and task methods
        assert isinstance(config, RemoteModuleConfig)
        assert sample_module_id in config.module_id
        assert "sample" == config.model_path
        assert len(config.task_methods) == 1
        # Assert how many SampleTask methods there are
        assert len(config.task_methods[0][1]) == 3


def test_remote_module_finder_multi_task_model(multi_task_model_id, open_port):
    """Test to ensure model finder works for models with multiple tasks"""
    with runtime_http_test_server(open_port) as server:
        with temp_finder(
            connection_cfg={
                "hostname": "localhost",
                "port": server.port,
                "protocol": "http",
            }
        ) as finder:
            config = finder.find_model(multi_task_model_id)
            # Check RemoteModuleConfig has the right type, name, and task methods
            assert isinstance(config, RemoteModuleConfig)
            assert len(config.task_methods) == 2


def test_remote_module_finder_discover_http_models(sample_task_model_id, open_port):
    """Test to ensure discovering models works for http"""
    with runtime_http_test_server(open_port) as server:
        with temp_finder(
            connection_cfg={
                "hostname": "localhost",
                "port": server.port,
                "protocol": "http",
            }
        ) as finder:
            config = finder.find_model(sample_task_model_id)
            assert isinstance(config, RemoteModuleConfig)
            assert sample_task_model_id == config.model_path
            assert len(config.task_methods) == 1
            # Assert how many SampleTask methods there are
            assert len(config.task_methods[0][1]) == 3


def test_remote_module_finder_discover_https_insecure_models(
    sample_task_model_id, open_port
):
    """Test to ensure discovering models works for https without checking certs"""
    with generate_tls_configs(open_port, tls=True, mtls=False) as config_overrides:
        with runtime_http_test_server(
            open_port,
            tls_config_override=config_overrides,
        ) as server_with_tls:
            with temp_finder(
                connection_cfg={
                    "hostname": "localhost",
                    "port": server_with_tls.port,
                    "protocol": "http",
                    "tls": {"enabled": True, "insecure_verify": True},
                }
            ) as finder:
                config = finder.find_model(sample_task_model_id)
                assert isinstance(config, RemoteModuleConfig)
                assert sample_task_model_id == config.model_path
                assert len(config.task_methods) == 1
                # Assert how many SampleTask methods there are
                assert len(config.task_methods[0][1]) == 3


def test_remote_module_finder_discover_https_mtls_models(
    sample_task_model_id, open_port
):
    """Test to ensure discovering models works for https with MTLS and secure CA"""
    with generate_tls_configs(open_port, tls=True, mtls=True) as config_overrides:
        with runtime_http_test_server(
            open_port,
            tls_config_override=config_overrides,
        ) as server_with_tls:
            with temp_finder(
                connection_cfg={
                    "hostname": "localhost",
                    "port": server_with_tls.port,
                    "protocol": "http",
                    "tls": {
                        "enabled": True,
                        "ca_file": config_overrides["use_in_test"]["ca_cert"],
                        "cert_file": config_overrides["use_in_test"]["client_cert"],
                        "key_file": config_overrides["use_in_test"]["client_key"],
                    },
                }
            ) as finder:
                config = finder.find_model(sample_task_model_id)
                assert isinstance(config, RemoteModuleConfig)
                assert sample_task_model_id == config.model_path
                assert len(config.task_methods) == 1
                # Assert how many SampleTask methods there are
                assert len(config.task_methods[0][1]) == 3


def test_remote_module_finder_discover_grpc_models(sample_task_model_id, open_port):
    """Test to ensure discovering models works for grpc"""
    with runtime_grpc_test_server(open_port) as server:
        with temp_finder(
            connection_cfg={
                "hostname": "localhost",
                "port": server.port,
                "protocol": "grpc",
            }
        ) as finder:
            config = finder.find_model(sample_task_model_id)
            assert isinstance(config, RemoteModuleConfig)
            assert sample_task_model_id == config.model_path
            assert len(config.task_methods) == 1
            # Assert how many SampleTask methods there are
            assert len(config.task_methods[0][1]) == 3


def test_remote_module_finder_discover_grpc_insecure_models():
    """Test to ensure discovering models raises an error when using insecure grpc"""
    with pytest.raises(ValueError):
        RemoteModelFinder(
            Config(
                {
                    "connection": {
                        "hostname": "localhost",
                        "port": 80,
                        "protocol": "grpc",
                        "tls": {"enabled": True, "insecure_verify": True},
                    }
                }
            ),
            "remote_finder",
        )


def test_remote_module_finder_discover_grpc_mtls_models(
    sample_task_model_id, open_port
):
    """Test to ensure discovering models raises an error when using insecure grpc"""
    with generate_tls_configs(open_port, tls=True, mtls=True) as config_overrides:
        with runtime_grpc_test_server(
            open_port,
        ) as server_with_tls:
            with temp_finder(
                connection_cfg={
                    "hostname": "localhost",
                    "port": server_with_tls.port,
                    "protocol": "grpc",
                    "tls": {
                        "enabled": True,
                        "ca_file": config_overrides["use_in_test"]["ca_cert"],
                        "cert_file": config_overrides["use_in_test"]["client_cert"],
                        "key_file": config_overrides["use_in_test"]["client_key"],
                    },
                }
            ) as finder:
                config = finder.find_model(sample_task_model_id)
                assert isinstance(config, RemoteModuleConfig)
                assert sample_task_model_id == config.model_path
                assert len(config.task_methods) == 1
                # Assert how many SampleTask methods there are
                assert len(config.task_methods[0][1]) == 3


def test_remote_module_finder_not_found():
    """Test to ensure error is raised when no model is found"""
    with temp_finder(
        multi_finder_cfg={"discover_models": False, "supported_models": {"wrong": "id"}}
    ) as finder:
        with pytest.raises(KeyError):
            finder.find_model("sample")
