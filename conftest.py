from __future__ import annotations
import os
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
import pytest
from click.testing import CliRunner
from frametree.core.set import Dataset
from frametree.core.row import DataRow
from frametree.testing.data.blueprint import SIMPLE_DATASET
from frametree.core.store import LocalStore
from frametree.flywheel.data import Flywheel

try:
    from pydra import set_input_validator
except ImportError:
    pass
else:
    set_input_validator(True)

# Set DEBUG logging for unittests if required
log_level = logging.WARNING

logger = logging.getLogger("arcana")
logger.setLevel(log_level)

sch = logging.StreamHandler()
sch.setLevel(log_level)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
sch.setFormatter(formatter)
logger.addHandler(sch)

############
# CHANGEME #
############


print(sorted(list(os.environ.keys())))

# TEST_STORE_URI =  os.environ["ARCANA_FLYWHEEL_TEST_STORE_URI"]
# TEST_STORE_USER = os.environ["ARCANA_FLYWHEEL_TEST_STORE_USER"]
TEST_STORE_PASSWORD = "fw.epilepsyproject.org.au:0JT8tiJh9CMCDQCbCM"


def install_and_launch_app(
    name: str,
    command_config: dict,
    row: DataRow,
    inputs: dict[str, str],
    timeout: int = 1000,  # seconds
    poll_interval: int = 10,  # seconds
) -> tuple[int, str, str]:
    """Installs a new command to be run in the integrated workflow engine of the "flywheel"
    data store, then launches it on the specified row with the provided inputs.

    Parameters
    ----------
    name : str
        The name to install the command as
    command_config : dict[str, Any]
        JSON that defines the XNAT command in the container service (see `generate_xnat_command`)
    row : DataRow
        the row of the dataset to run the app on
    inputs : dict[str, str]
        Inputs passed to the pipeline at launch (i.e. typically through text fields in the CS launch UI)
    timeout : int
        the time to wait for the pipeline to complete (seconds)
    poll_interval : int
        the time interval between status polls (seconds)

    Returns
    -------
    workflow_id : int
        the auto-generated ID for the launched workflow
    status : str
        the status of the completed workflow
    out_str : str
        stdout and stderr from the workflow run
    """
    raise NotImplementedError


############
# FIXTURES #
############


@pytest.fixture
def data_store(work_dir: Path, arcana_home, request):
    cache_dir = work_dir / "remote-cache"
    cache_dir.mkdir()
    if TEST_STORE_PASSWORD is None:
        raise NotImplementedError(
            "Need to set values of 'TEST_STORE_URI', 'TEST_STORE_USER' and "
            f"'TEST_STORE_PASSWORD' in {__file__} to point to a valid account on "
            "an instance of the remote store that can be used for testing, i.e. "
            "allow the creation of dummy test data.\n\n"
            "IT SHOULD NOT BE A PRODUCTION SERVER!!"
        )
    store = Flywheel(
        server="dummy",
        cache_dir=cache_dir,
        password=TEST_STORE_PASSWORD,
    )
    store.save("test_mock_store")
    yield store


@pytest.fixture
def simple_dataset(data_store, work_dir, run_prefix) -> Dataset:
    blueprint = SIMPLE_DATASET.translate_to(data_store)
    dataset_id = make_dataset_id(data_store, "simple", work_dir, run_prefix)
    return blueprint.make_dataset(data_store, dataset_id, name="")


@pytest.fixture(scope="session")
def run_prefix():
    "A datetime string used to avoid stale data left over from previous tests"
    return datetime.strftime(datetime.now(), "%Y%m%d%H%M%S")


@pytest.fixture
def cli_runner(catch_cli_exceptions):
    def invoke(*args, catch_exceptions=catch_cli_exceptions, **kwargs):
        runner = CliRunner()
        result = runner.invoke(*args, catch_exceptions=catch_exceptions, **kwargs)
        return result

    return invoke


@pytest.fixture
def work_dir() -> Path:
    work_dir = tempfile.mkdtemp()
    return Path(work_dir)


@pytest.fixture
def arcana_home(work_dir):
    """Sets the ARCANA_HOME environment variable to be inside the work directory, so
    "user-level" configurations can be set without affecting the host environment"""
    arcana_home = work_dir / "arcana-home"
    with patch.dict(os.environ, {"ARCANA_HOME": str(arcana_home)}):
        yield arcana_home


def make_dataset_id(data_store, name, work_dir, run_prefix):
    return work_dir / name if isinstance(data_store, LocalStore) else name + run_prefix


# For debugging in IDE's don't catch raised exceptions and let the IDE
# break at it
if os.getenv("_PYTEST_RAISE", "0") != "0":

    @pytest.hookimpl(tryfirst=True)
    def pytest_exception_interact(call):
        raise call.excinfo.value

    @pytest.hookimpl(tryfirst=True)
    def pytest_internalerror(excinfo):
        raise excinfo.value

    CATCH_CLI_EXCEPTIONS = False
else:
    CATCH_CLI_EXCEPTIONS = True


@pytest.fixture
def catch_cli_exceptions():
    return CATCH_CLI_EXCEPTIONS
