from concurrent.futures import as_completed
from pathlib import Path
from platform import node
import argparse
import json

from tqdm import tqdm
from ase import Atoms
import parsl
from parsl.config import Config
from parsl.app.python import PythonApp
from parsl.executors import HighThroughputExecutor
from parsl.providers import PBSProProvider
from parsl.launchers import MpiExecLauncher


def test_function(path: Path, timesteps: int) -> tuple[float, list[Atoms]]:
    """Run a gRASPA simulation, report runtime and resultant capacities

    Args:
        path: Path to a directory containing DDEC output
        invocation: Command to invoke gRASPA
        timesteps: Number of GCMC time steps
    Returns:
        - Runtime (s)
        - Gas capacities
    """
    from mofa.simulation.raspa import RASPARunner
    from mofa.simulation.cp2k import load_atoms_with_charges
    from time import perf_counter
    from pathlib import Path

    run_dir = Path(f'run-{timesteps}')
    run_dir.mkdir(exist_ok=True, parents=True)

    # Run
    name = path.name[:12]
    runner = RASPARunner()
    atoms = load_atoms_with_charges(path)
    start_time = perf_counter()
    output = runner.run_GCMC_single(atoms, name, timesteps=timesteps)
    run_time = perf_counter() - start_time

    return run_time, output


if __name__ == "__main__":
    # Get the length of the runs, etc
    parser = argparse.ArgumentParser()
    parser.add_argument('--timesteps', help='Number of timesteps to run', default=100000, type=int)
    parser.add_argument('--config', help='Which compute configuration to use', default='local')
    args = parser.parse_args()

    # Select the correct configuraion
    if args.config == "local":
        config = Config(executors=[HighThroughputExecutor(max_workers=128)])
        
    elif args.config == "polaris":
        config = Config(executors=[
            HighThroughputExecutor(
                max_workers_per_node=4,
                cpu_affinity='block-reverse',
                available_accelerators=4,
                provider=PBSProProvider(
                    launcher=MpiExecLauncher(bind_cmd="--cpu-bind", overrides="--depth=32 --ppn 1"),
                    account='APSDataAnalysis',
                    queue='debug',
                    select_options="ngpus=4",
                    scheduler_options="#PBS -l filesystems=home:eagle:grand",
                    worker_init="""
module use /soft/modulefiles; module load conda
conda activate /eagle/Diaspora/alok/sc25-agentic-mof-workflow/env
cd /grand/SuperBERT/alok/sc25-agentic-mof-workflow/
export TMPDIR=/tmp

pwd
which python
hostname
                    """,
                    nodes_per_block=1,
                    init_blocks=1,
                    min_blocks=0,
                    max_blocks=1,
                    cpus_per_node=32,
                    walltime="1:00:00",
                )
            )
        ])
    else:
        raise ValueError(f'Configuration not defined: {args.config}')

    # Prepare parsl
    with parsl.load(config):
        test_app = PythonApp(test_function)

        # Submit each MOF in cp2k-runs
        futures = []
        for path in Path('cp2k-runs').rglob('DDEC6_even_tempered_net_atomic_charges.xyz'):
            future = test_app(path.parent, args.timesteps)
            future.path = path
            futures.append(future)

        # Store results
        for future in tqdm(as_completed(futures), total=len(futures)):
            if future.exception() is not None:
                print(f'{future.mof.name} failed: {future.exception}')
                continue
            runtime, output = future.result()

            # Store the result
            with open('runtimes.json', 'a') as fp:
                print(json.dumps({
                    'host': node(),
                    'path': str(path.parent),
                    'timesteps': args.timesteps,
                    'runtime': runtime,
                    'output': output,
                    'config': args.config,
                }), file=fp)