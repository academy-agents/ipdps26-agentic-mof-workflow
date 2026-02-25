#!/bin/bash -le
#PBS -l select=6
#PBS -l walltime=01:00:00
#PBS -l filesystems=home:grand:eagle
#PBS -q debug-scaling
#PBS -N mofa-test
#PBS -A APSDataAnalysis

hostname

# Change to working directory
cd ${PBS_O_WORKDIR}
pwd

# Activate the environment
module use /soft/modulefiles
module load conda; conda activate base
conda activate /eagle/Diaspora/alok/sc25-agentic-mof-workflow/env
which python

export OPENBLAS_NUM_THREADS=1
export TMPDIR=/tmp

# Launch MPS on each node
# NNODES=`wc -l < $PBS_NODEFILE`
# mpiexec -n ${NNODES} --ppn 1 ./bin/enable_mps_polaris.sh &
parallel --env _  --nonall --sshloginfile $PBS_NODEFILE "nohup /grand/SuperBERT/alok/sc25-agentic-mof-workflow/bin/enable_mps_polaris.sh &"

# Start Redis
redis-server --bind 0.0.0.0 --appendonly no --logfile redis.log --protected-mode no &
redis_pid=$!
echo launched redis on $redis_pid

# Run
python run_parallel_workflow.py \
      --node-path input-files/zn-paddle-pillar/node.json \
      --ligand-templates input-files/zn-paddle-pillar/template_*_prompt.yml \
      --generator-path models/geom-300k/geom_difflinker_epoch=997_new.ckpt \
      --generator-config-path models/geom-300k/config-tf32-a100.yaml \
      --maximum-train-size 2048 \
      --maximum-strain 0.25 \
      --retrain-freq 64 \
      --num-epochs 128 \
      --num-samples 1024 \
      --gen-batch-size 128 \
      --simulation-budget 20 \
      --md-timesteps 100000 \
      --md-snapshots 10 \
      --raspa-timesteps 50000 \
      --lammps-on-ramdisk \
      --dft-opt-steps 1 \
      --dft-fraction 0.4 \
      --ai-fraction 0.4 \
      --proxy-threshold 100000 \
      --compute-config polaris
echo Python done

# Shutdown services
kill $redis_pid
mpiexec -n ${NNODES} --ppn 1 ./bin/disable_mps_polaris.sh
