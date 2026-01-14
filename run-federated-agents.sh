#!/bin/bash

python -m mofa.agentic.run \
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
      --simulation-budget 0 \
      --md-timesteps 10000 \
      --md-snapshots 10 \
      --retain-lammps \
      --raspa-timesteps 1000000 \
      --dft-opt-steps 1 \
      --compute-config federated \
      --cpu-endpoint b2675547-e5cf-4f1f-9334-fba9b83e93cc \
      --polaris-endpoint bafaa425-816c-43f1-a4c7-d9ac7d07ee92 \
      --log-level INFO
      # --lammps-on-ramdisk \
