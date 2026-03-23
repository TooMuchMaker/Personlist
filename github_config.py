#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 配置文件
只需要修改这里！
"""

# 你的 GitHub 用户名
GITHUB_USERNAME = "TooMuchMaker"

# 仓库名称
GITHUB_REPO = "Personlist"

# 自动生成的配置
def get_update_url():
    """获取 version.json 的地址"""
    return f"https://{GITHUB_USERNAME}.github.io/{GITHUB_REPO}/version.json"

def get_download_url(version):
    """获取 .exe 下载地址"""
    return f"https://github.com/{GITHUB_USERNAME}/{GITHUB_REPO}/releases/download/v{version}/TRAEWORK.exe"
