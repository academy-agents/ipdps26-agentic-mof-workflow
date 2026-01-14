from __future__ import annotations

import dataclasses


class ComputeConfig:
    num_generator_workers: int
    num_assembly_workers: int
    num_validator_workers: int
    num_optimizer_workers: int
    num_estimator_workers: int
    torch_device: str
    cp2k_cmd: str
    lammps_cmd: tuple[str, ...]
    lammps_env: dict[str, str]


@dataclasses.dataclass(kw_only=True)
class PolarisSingleNode(ComputeConfig):
    # retrain tasks get 1 GPU and 8 CPUs
    num_retrain_workers = 1
    # generate-ligands tasks get 1 GPU and 4 CPUs
    num_generator_workers = 2
    # assemble-ligands tasks get 1 CPU
    num_assembly_workers = 8
    # validate-structures get 0.5 GPUs and 2 CPUs
    num_validator_workers = 1
    # optimize-cells get 1 GPU and 8 CPUs
    num_optimizer_workers = 0
    num_estimator_workers = 2
    torch_device = "cuda"
    cp2k_cmd = (
        "module restore ; "
        # "mpiexec -n 1 --ppn 1 --env OMP_NUM_THREADS=8 --hosts $HOSTNAME "
        # "--cpu-bind depth --depth 8 "
        # "/lus/eagle/projects/ExaMol/cp2k-2024.1/set_affinity_gpu_polaris.sh "
        "/lus/eagle/projects/ExaMol/cp2k-2024.1/exe/local_cuda/cp2k_shell.psmp "
    )
    lammps_cmd = (
        "/eagle/MOFA/jgpaul/lammps/build-gpu-nompi-mixed/lmp",
        "-sf",
        "gpu",
        "-pk",
        "gpu",
        "1",
    )
    lammps_env: dict[str, str] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(kw_only=True)
class FederatedConfig(ComputeConfig):
    # Generator, retrain share a single debug aurora node with 12 GPU tiles
    num_retrain_workers = 1
    num_generator_workers = 5

    # Validator share two dubug-scaling with 12 whole GPUs
    num_validator_workers = 24

    # Assembly and optimizer share the chameleon node
    num_assembly_workers = 4
    num_estimator_workers = 8

    # Optimizer workers have a single polaris debug job with four GPUs
    num_optimizer_workers = 8

    torch_device = "xpu"

    # @property
    # def cp2k_cmd(self) -> str:
    #     worker_id = str(os.environ("PARSL_WORKER_RANK"))
    #     cpu_map = {
    #         "0": "list:24-31",
    #         "1": "list:16-23",
    #         "2": "list:8-15",
    #         "3": "list:0-7",
    #     }
    #     cpu_ids = cpu_map[worker_id]
    # 
    
    # Runs on Polaris
    # TODO: Implement CPU binding for performance
    cp2k_cmd = (
        "mpiexec -n 2 --ppn 2 --env OMP_NUM_THREADS=4 "
        "--hosts $HOSTNAME"
        "/grand/SuperBERT/alok/cp2k/build/bin/cp2k_shell.psmp"
    )

    lammps_cmd = (
        # "/flare/proxystore/jgpaul/lammps/build-cpu/lmp",
        # "/flare/proxystore/jgpaul/lammps/build-nompi-cpu/lmp",
        "/flare/Diaspora/alok/agents/lammps/build/lmp",
        "-sf",
        "hybrid",
        "gpu",
        "omp",
        "-pk",
        "gpu",
        "1",
        "neigh",
        "no",
        "-pk",
        "omp",
        "16",
    )
    lammps_env: dict[str, str] = dataclasses.field(default_factory=dict)


COMPUTE_CONFIGS = {
    "federated": FederatedConfig(),
    "polaris-single": PolarisSingleNode(),
}
