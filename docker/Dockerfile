ARG PYTORCH="1.9.0"
ARG CUDA="11.1"
ARG CUDNN="8"
# Version dependencies https://mmcv.readthedocs.io/en/latest/get_started/installation.html
ARG MMCV="1.5.3"
ARG MMDET="2.25.0"
ARG MMSEG="0.26.0"
FROM pytorch/pytorch:${PYTORCH}-cuda${CUDA}-cudnn${CUDNN}-devel

ENV TORCH_CUDA_ARCH_LIST="6.0 6.1 7.0+PTX"
ENV TORCH_NVCC_FLAGS="-Xfatbin -compress-all"
ENV CMAKE_PREFIX_PATH="$(dirname $(which conda))/../"

# To fix GPG key error when running apt-get update
RUN apt-key adv \
    --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/3bf863cc.pub
RUN apt-key adv \
    --fetch-keys https://developer.download.nvidia.com/compute/machine-learning/repos/ubuntu1804/x86_64/7fa2af80.pub

RUN apt-get update && \
    apt-get install \
        --yes \
        --no-install-recommends \
            build-essential \
            cmake \
            ffmpeg \
            libsm6 \
            libxext6 \
            git \
            ninja-build \
            libglib2.0-0 \
            libsm6 \
            libxrender-dev \
            libxext6 \
            python3-dev \
            libopenblas-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Minkowski Engine
RUN pip install ninja
ENV MAX_JOBS=4
RUN pip install \
    --upgrade git+https://github.com/NVIDIA/MinkowskiEngine \
    --install-option="--blas=openblas" \
    --install-option="--force_cuda" \
    --verbose \
    --no-deps

# Install MMCV, MMDetection and MMSegmentation
ARG PYTORCH
ARG CUDA
ARG MMCV
ARG MMDET
ARG MMSEG
RUN ["/bin/bash", "-c", "pip install --no-cache-dir mmcv-full==${MMCV} -f https://download.openmmlab.com/mmcv/dist/cu${CUDA//./}/torch${PYTORCH}/index.html"]
RUN pip install \
    --no-cache-dir\
        mmdet==${MMDET} \
        mmsegmentation==${MMSEG}

# Install MMDetection3D
RUN conda clean --all
COPY . /mmdetection3d
WORKDIR /mmdetection3d
ENV FORCE_CUDA="1"
RUN pip install \
    --requirement requirements/build.txt
RUN pip install \
    --no-cache-dir \
    --editable .
