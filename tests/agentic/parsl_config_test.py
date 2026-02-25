import parsl

from mofa.agentic.parsl_config import get_aurora_config
from mofa.agentic.task import test_generator_executor
from mofa.agentic.task import test_validator_executor

def test_aurora_config(tmpdir):
    config = get_aurora_config("parsl_runs")
    parsl.load(config)
    # future = test_generator_executor()
    # assert future.result() == "Hello World"

    future = test_validator_executor()
    assert future.result() == "Hello World"
