#! /bin/bash

# Make a virtual environment from the frameworks
module load frameworks/2025
python3 -m venv ./venv --system-site-packages
source ./venv/bin/activate

# Install the MOFA stuff
pip install -e .
# for aurora, take out the pypi install
pip uninstall pytorch-lightning -y
# put in the one with xpu support
export PACKAGE_NAME=pytorch
pip install git+https://github.com/azton/lightning.git

# Install llamps (OpenCL GPU no MPI)
mkdir libs
cd libs
git clone git@github.com:lammps/lammps.git
git checkout stable_22Jul2025
cd lammps
mkdir build; cd build
cmake -C ../cmake/presets/oneapi.cmake -DPKG_MOLECULE=on -DPKG_EXTRA-MOLECULE=on -DPKG_EXTRA-FIX=on -DPKG_KSPACE=on -DPKG_MANYBODY=on -DPKG_GRANULAR=on -DPKG_MOFFF=on -DPKG_QEQ=on -DPKG_REAXFF=on  -DPKG_RIGID=on -DPKG_KSPACE=on -DPKG_ML-SNAP=on -DFFT=MKL -DFFT_SINGLE=on -DPKG_GPU=on -DGPU_API=opencl ../cmake
cmake --build .
cd ../../..

# Install conda stuff and symlink it to venv
# This avoids needing 2 environments, or copyign the frameworks env
deactivate
conda env create --file envs/aurora/environment.yml -p ./conda-env
cd venv/bin/
ln -s ../../conda-env/bin/simulate simulate
ln -s ../../conda-env/bin/parallel parallel
cd ../..
