#!/usr/bin/env python3
"""
TRAEWORK 构建脚本
用于打包应用和创建安装程序
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent
BUILD_DIR = PROJECT_ROOT / 'build'
DIST_DIR = PROJECT_ROOT / 'dist'


def clean():
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
        print("Cleaned build directory")
    
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
        print("Cleaned dist directory")


def build_exe():
    print("Building executable with PyInstaller...")
    
    spec_file = PROJECT_ROOT / 'traework.spec'
    
    if not spec_file.exists():
        print("Error: traework.spec not found")
        return False
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        str(spec_file)
    ]
    
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    
    if result.returncode == 0:
        print("Build successful!")
        return True
    else:
        print("Build failed!")
        return False


def create_installer():
    print("Creating installer...")
    
    nsis_script = PROJECT_ROOT / 'installer' / 'installer.nsi'
    
    if not nsis_script.exists():
        print("Warning: NSIS script not found, skipping installer creation")
        return False
    
    nsis_cmd = shutil.which('makensis')
    if not nsis_cmd:
        print("Warning: NSIS not found, skipping installer creation")
        return False
    
    result = subprocess.run([nsis_cmd, str(nsis_script)], cwd=PROJECT_ROOT)
    
    if result.returncode == 0:
        print("Installer created successfully!")
        return True
    else:
        print("Failed to create installer")
        return False


def copy_data_files():
    print("Copying data files...")
    
    dist_exe = DIST_DIR / 'TRAEWORK.exe'
    if not dist_exe.exists():
        print("Error: Built executable not found")
        return False
    
    platforms = ['计划管理', '学校课程', '信竞', '项目管理', 'folder-manager', 'shared']
    
    for platform in platforms:
        src = PROJECT_ROOT / platform
        dst = DIST_DIR / platform
        
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"Copied {platform}")
    
    print("Data files copied successfully!")
    return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='TRAEWORK Build Script')
    parser.add_argument('--clean', '-c', action='store_true', help='Clean build directories')
    parser.add_argument('--build', '-b', action='store_true', help='Build executable')
    parser.add_argument('--installer', '-i', action='store_true', help='Create installer')
    parser.add_argument('--all', '-a', action='store_true', help='Run all build steps')
    
    args = parser.parse_args()
    
    if args.all:
        args.clean = True
        args.build = True
        args.installer = True
    
    if not any([args.clean, args.build, args.installer]):
        args.clean = True
        args.build = True
    
    if args.clean:
        clean()
    
    if args.build:
        if not build_exe():
            sys.exit(1)
        if not copy_data_files():
            sys.exit(1)
    
    if args.installer:
        create_installer()
    
    print("\nBuild process completed!")


if __name__ == '__main__':
    main()
