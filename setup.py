import os
import platform
import subprocess
import sys

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext

#New System
class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=''):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)


class CMakeBuild(build_ext):
    def run(self):
        try:
            out = subprocess.check_output(['cmake', '--version'])
        except OSError:
            raise RuntimeError(
                "CMake must be installed to build the following extensions: " + ", ".join(e.name for e in self.extensions))

        if platform.system() == "Windows":
            raise RuntimeError("Unsupported on Windows")

        for ext in self.extensions:
            self.build_extension(ext)

    def build_extension(self, ext):
        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))
        cmake_args = ['-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=' + extdir, '-DPYTHON_EXECUTABLE=' + sys.executable]

        cfg = 'Debug' if self.debug else 'Release'
        build_args = ['--config', cfg]

        if platform.system() == "Windows":
            raise RuntimeError("Unsupported on Windows")
        else:
            cmake_args += ['-DCMAKE_BUILD_TYPE=' + cfg]
            build_args += ['--', '-j16']

        cmake_args += ["-DCMAKE_BUILD_WITH_INSTALL_RPATH=TRUE"]
        cmake_args += ["-DCMAKE_INSTALL_RPATH_USE_LINK_PATH=TRUE"]
        try:
            import torch
            if torch.cuda.is_available():
                cmake_args += ["-DUSE_CUDA=TRUE"]
                cmake_args += ["-DUSE_OMP=TRUE"]
        except ImportError:
            raise ImportError("Pytorch not found. Please install pytorch first.")

        if sys.platform == "darwin":
            cmake_args.append('-DCMAKE_INSTALL_RPATH=@loader_path')
        else:  # values: linux*, aix, freebsd, ... just as well win32 & cygwin
            cmake_args.append('-DCMAKE_INSTALL_RPATH=$ORIGIN')
        cmake_args.append("-DCMAKE_EXPORT_COMPILE_COMMANDS=ON")
        cmake_args.append("-DCUDA_TOOLKIT_ROOT_DIR=/usr/local/cuda-12.4/")
        env = os.environ.copy()
        env['CXXFLAGS'] = '{} -DVERSION_INFO=\\"{}\\"'.format(
            env.get('CXXFLAGS', ''),
            self.distribution.get_version())
        env["NVCC"]="/usr/local/cuda/bin/nvcc"

        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)

        print(cmake_args)

        subprocess.check_call(['cmake', ext.sourcedir] + cmake_args,
                              cwd=self.build_temp, env=env)
        subprocess.check_call(['cmake', '--build', '.'] + build_args,
                              cwd=self.build_temp)
        print()  # Add an empty line for cleaner output


only_python = os.environ.get("CELERITAS_ONLY_PYTHON", None)
if only_python:
    setup()
else:
    setup(
        ext_modules=[CMakeExtension('celeritas._pyceleritas')],
        cmdclass=dict(build_ext=CMakeBuild),
    )
