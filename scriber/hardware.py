"""Hardware capability assessment and dynamic accelerator routing for Scriber.

Provides in-process inspection of NVIDIA GPUs (via NVML), DirectX 12 feature levels
(via Direct3D 12 runtime), and CTranslate2 CUDA accelerator availability.
Intelligently routes between local GPU execution and cloud API bridges.
"""

from __future__ import annotations

import ctypes
from ctypes import byref, c_char, c_int, c_uint, c_ulonglong, Structure
import logging
import os
import sys
import threading
from typing import Any, Dict, Optional, Tuple

from scriber.models import HardwareCapabilities

logger = logging.getLogger(__name__)

# Direct3D Feature Level constants
D3D_FEATURE_LEVEL_12_2 = 0xc200
D3D_FEATURE_LEVEL_12_1 = 0xc100
D3D_FEATURE_LEVEL_12_0 = 0xc000
D3D_FEATURE_LEVEL_11_1 = 0xb100
D3D_FEATURE_LEVEL_11_0 = 0xb000


# NVML Memory structure
class _nvmlMemory_t(Structure):
    _fields_ = [
        ("total", c_ulonglong),
        ("free", c_ulonglong),
        ("used", c_ulonglong),
    ]


_HARDWARE_LOCK = threading.Lock()
_CACHED_HARDWARE: Optional[HardwareCapabilities] = None


def _load_nvml_library() -> Optional[ctypes.CDLL]:
    """Attempts to locate and dynamically load nvml.dll or libnvidia-ml.so."""
    candidates = []
    if sys.platform == "win32":
        candidates.extend([
            "nvml.dll",
            os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "nvml.dll"),
            os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "NVIDIA Corporation", "NVSMI", "nvml.dll"),
        ])
    else:
        candidates.extend([
            "libnvidia-ml.so.1",
            "libnvidia-ml.so",
        ])

    for path in candidates:
        try:
            return ctypes.CDLL(path)
        except (OSError, FileNotFoundError):
            continue
    return None


def _query_nvml_gpu() -> Optional[Dict[str, Any]]:
    """Probes NVIDIA GPU via NVML C API.
    
    Returns a dictionary of GPU metrics if successful, or None if NVML is unavailable.
    """
    nvml = _load_nvml_library()
    if nvml is None:
        return None

    # Resolve function pointers with version fallback (_v2 or legacy)
    init_fn = getattr(nvml, "nvmlInit_v2", getattr(nvml, "nvmlInit", None))
    shutdown_fn = getattr(nvml, "nvmlShutdown", None)
    get_count_fn = getattr(nvml, "nvmlDeviceGetCount_v2", getattr(nvml, "nvmlDeviceGetCount", None))
    get_handle_fn = getattr(nvml, "nvmlDeviceGetHandleByIndex_v2", getattr(nvml, "nvmlDeviceGetHandleByIndex", None))
    get_name_fn = getattr(nvml, "nvmlDeviceGetName", None)
    get_mem_fn = getattr(nvml, "nvmlDeviceGetMemoryInfo", None)
    get_cc_fn = getattr(nvml, "nvmlDeviceGetCudaComputeCapability", None)
    get_driver_fn = getattr(nvml, "nvmlSystemGetDriverVersion", None)
    get_cuda_ver_fn = getattr(nvml, "nvmlSystemGetCudaDriverVersion", None)

    if not all([init_fn, shutdown_fn, get_count_fn, get_handle_fn, get_name_fn, get_mem_fn]):
        return None

    initialized = False
    try:
        ret = init_fn()
        if ret != 0:
            return None
        initialized = True

        dev_count = c_uint()
        if get_count_fn(byref(dev_count)) != 0 or dev_count.value == 0:
            return None

        # Inspect available GPUs and select device with largest total VRAM
        best_gpu: Optional[Dict[str, Any]] = None
        max_vram = -1.0

        for idx in range(dev_count.value):
            handle = ctypes.c_void_p()
            if get_handle_fn(idx, byref(handle)) != 0:
                continue

            name_buf = (c_char * 96)()
            name = "NVIDIA GPU"
            if get_name_fn(handle, name_buf, 96) == 0:
                try:
                    name = name_buf.value.decode("utf-8", errors="replace").strip()
                except Exception:
                    pass

            mem = _nvmlMemory_t()
            vram_total_mb = 0.0
            vram_free_mb = 0.0
            if get_mem_fn(handle, byref(mem)) == 0:
                vram_total_mb = round(mem.total / (1024.0 * 1024.0), 1)
                vram_free_mb = round(mem.free / (1024.0 * 1024.0), 1)

            major = c_int(0)
            minor = c_int(0)
            cc = (0, 0)
            if get_cc_fn and get_cc_fn(handle, byref(major), byref(minor)) == 0:
                cc = (major.value, minor.value)

            drv_ver = ""
            if get_driver_fn:
                drv_buf = (c_char * 80)()
                if get_driver_fn(drv_buf, 80) == 0:
                    try:
                        drv_ver = drv_buf.value.decode("utf-8", errors="replace").strip()
                    except Exception:
                        pass

            cuda_ver_str = ""
            if get_cuda_ver_fn:
                cver = c_int(0)
                if get_cuda_ver_fn(byref(cver)) == 0 and cver.value > 0:
                    major_c = cver.value // 1000
                    minor_c = (cver.value % 1000) // 10
                    cuda_ver_str = f"{major_c}.{minor_c}"

            gpu_candidate = {
                "gpu_name": name,
                "vram_total_mb": vram_total_mb,
                "vram_free_mb": vram_free_mb,
                "compute_capability": cc,
                "driver_version": drv_ver,
                "cuda_version": cuda_ver_str,
            }

            if vram_total_mb > max_vram:
                max_vram = vram_total_mb
                best_gpu = gpu_candidate

        return best_gpu

    except Exception as e:
        logger.debug(f"NVML probe encountered exception: {e}")
        return None
    finally:
        if initialized and shutdown_fn:
            try:
                shutdown_fn()
            except Exception:
                pass


def _query_d3d12() -> Tuple[bool, str]:
    """Inspects DirectX 12 hardware support using d3d12.dll across feature levels.
    
    Returns (directx_12_supported, highest_feature_level_string).
    """
    if sys.platform != "win32":
        return False, ""

    try:
        d3d12 = getattr(ctypes, "windll", None)
        if d3d12 is None or not hasattr(d3d12, "d3d12"):
            d3d12_lib = ctypes.WinDLL("d3d12.dll")
        else:
            d3d12_lib = d3d12.d3d12

        create_device_fn = getattr(d3d12_lib, "D3D12CreateDevice", None)
        if not create_device_fn:
            return False, ""

        feature_levels = [
            (D3D_FEATURE_LEVEL_12_2, "12_2"),
            (D3D_FEATURE_LEVEL_12_1, "12_1"),
            (D3D_FEATURE_LEVEL_12_0, "12_0"),
            (D3D_FEATURE_LEVEL_11_1, "11_1"),
            (D3D_FEATURE_LEVEL_11_0, "11_0"),
        ]

        highest_supported = ""
        is_d3d12_supported = False

        for fl_val, fl_str in feature_levels:
            try:
                hr = create_device_fn(None, fl_val, None, None)
                # D3D12CreateDevice returns S_OK (0) or S_FALSE (1) when ppDevice is NULL and FL is supported
                if hr in (0, 1):
                    if not highest_supported:
                        highest_supported = fl_str
                    if fl_val >= D3D_FEATURE_LEVEL_12_0:
                        is_d3d12_supported = True
            except Exception:
                continue

        return is_d3d12_supported, highest_supported

    except (OSError, AttributeError, Exception) as e:
        logger.debug(f"Direct3D 12 probe encountered exception: {e}")
        return False, ""


def _query_ctranslate2_cuda() -> int:
    """Returns the count of CUDA devices available to CTranslate2."""
    try:
        import ctranslate2
        return int(ctranslate2.get_cuda_device_count())
    except Exception:
        return 0


def get_hardware_capabilities(force_refresh: bool = False) -> HardwareCapabilities:
    """Inspects the host system to determine GPU, VRAM, CUDA, and DirectX capabilities.
    
    Caches the result after first execution unless force_refresh is True.
    """
    global _CACHED_HARDWARE
    with _HARDWARE_LOCK:
        if _CACHED_HARDWARE is not None and not force_refresh:
            return _CACHED_HARDWARE

        nvml_gpu = _query_nvml_gpu()
        d3d12_supported, d3d12_fl = _query_d3d12()
        ct2_cuda_count = _query_ctranslate2_cuda()

        if nvml_gpu is not None:
            gpu_name = nvml_gpu["gpu_name"]
            vram_total_mb = float(nvml_gpu["vram_total_mb"])
            vram_free_mb = float(nvml_gpu["vram_free_mb"])
            compute_cap = nvml_gpu["compute_capability"]
            cuda_ver = nvml_gpu.get("cuda_version", "")
            cuda_avail = bool(ct2_cuda_count > 0 or (vram_total_mb > 0 and compute_cap[0] > 0))
        else:
            gpu_name = None
            vram_total_mb = 0.0
            vram_free_mb = 0.0
            compute_cap = (0, 0)
            cuda_ver = ""
            cuda_avail = bool(ct2_cuda_count > 0)

        # Device and compute type recommendations:
        # Require dedicated GPU with >= 4000 MB VRAM and CUDA support for "cuda" route
        if cuda_avail and vram_total_mb >= 4000.0:
            recommended_dev = "cuda"
            recommended_compute = "float16"
        else:
            recommended_dev = "cpu"
            recommended_compute = "int8"

        # Local speech LLM / flow-matching companion support:
        # Requires NVIDIA GPU with CUDA and at least 3500 MB free VRAM
        supports_speech_llm = bool(cuda_avail and vram_free_mb >= 3500.0)

        caps = HardwareCapabilities(
            gpu_name=gpu_name,
            vram_total_mb=vram_total_mb,
            vram_free_mb=vram_free_mb,
            compute_capability=compute_cap,
            cuda_available=cuda_avail,
            cuda_version=cuda_ver,
            directx_12_supported=d3d12_supported,
            directx_feature_level=d3d12_fl,
            recommended_device=recommended_dev,
            recommended_compute_type=recommended_compute,
            supports_local_speech_llm=supports_speech_llm,
        )

        _CACHED_HARDWARE = caps
        return caps


def get_transcription_device_config() -> Tuple[str, str]:
    """Returns recommended (device, compute_type) for Faster-Whisper transcription."""
    caps = get_hardware_capabilities()
    return caps.recommended_device, caps.recommended_compute_type


def format_hardware_summary(caps: Optional[HardwareCapabilities] = None) -> str:
    """Returns a formatted human-readable summary of the detected hardware."""
    if caps is None:
        caps = get_hardware_capabilities()
    lines = [
        "=== Scriber Hardware & GPU Acceleration Capability ===",
        f"  GPU Name:                  {caps.gpu_name or 'None (CPU fallback)'}",
        f"  Total VRAM:                {caps.vram_total_mb:.1f} MB",
        f"  Free VRAM:                 {caps.vram_free_mb:.1f} MB",
        f"  Compute Capability:        {caps.compute_capability[0]}.{caps.compute_capability[1]}",
        f"  CUDA Available:            {caps.cuda_available} (Driver: {caps.cuda_version or 'N/A'})",
        f"  DirectX 12 Supported:      {caps.directx_12_supported} (Feature Level: {caps.directx_feature_level or 'N/A'})",
        f"  Recommended Device:        {caps.recommended_device}",
        f"  Recommended Compute Type:  {caps.recommended_compute_type}",
        f"  Supports Local Speech LLM: {caps.supports_local_speech_llm}",
        "=======================================================",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    print(format_hardware_summary())
