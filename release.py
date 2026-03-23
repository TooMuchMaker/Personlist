#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRAEWORK 一键发布脚本
简化发布流程！
"""

import os
import sys
import json
import subprocess
from pathlib import Path

# 导入 GitHub 配置
from github_config import GITHUB_USERNAME, GITHUB_REPO, get_update_url, get_download_url

def print_step(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def main():
    print_step("TRAEWORK 一键发布工具")
    
    # 检查配置
    if GITHUB_USERNAME == "你的用户名":
        print("⚠️  请先在 github_config.py 中配置你的 GitHub 用户名！")
        print("   打开 github_config.py，把 '你的用户名' 改成你实际的 GitHub 用户名")
        return
    
    print(f"GitHub 配置: {GITHUB_USERNAME}/{GITHUB_REPO}")
    print(f"Update URL: {get_update_url()}")
    
    # 1. 获取当前版本
    config_file = Path("traework/core/config.py")
    version_json = Path("version.json")
    
    # 读取当前版本
    with open("config.json", "r", encoding="utf-8") as f:
        current_config = json.load(f)
    current_version = current_config["app"]["version"]
    
    print(f"\n当前版本: {current_version}")
    
    # 2. 询问新版本号
    new_version = input(f"请输入新版本号 (当前: {current_version}): ").strip()
    if not new_version:
        new_version = current_version
    
    # 3. 询问更新说明
    release_notes = input("请输入更新说明 (可选): ").strip()
    if not release_notes:
        release_notes = f"TRAEWORK v{new_version} 发布"
    
    # 4. 更新版本号
    print_step(f"更新版本号到 v{new_version}")
    
    # 更新 config.json
    current_config["app"]["version"] = new_version
    current_config["app"]["update_url"] = get_update_url()
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(current_config, f, ensure_ascii=False, indent=2)
    
    # 更新 traework/core/config.py
    with open(config_file, "r", encoding="utf-8") as f:
        config_content = f.read()
    
    import re
    config_content = re.sub(
        r"'version': '.*?'",
        f"'version': '{new_version}'",
        config_content
    )
    config_content = re.sub(
        r"'update_url': '.*?'",
        f"'update_url': '{get_update_url()}'",
        config_content
    )
    
    with open(config_file, "w", encoding="utf-8") as f:
        f.write(config_content)
    
    # 5. 更新 version.json
    print_step("更新 version.json")
    
    update_info = {
        "version": new_version,
        "download_url": get_download_url(new_version),
        "release_notes": release_notes
    }
    
    with open(version_json, "w", encoding="utf-8") as f:
        json.dump(update_info, f, ensure_ascii=False, indent=2)
    
    # 6. 打包
    print_step("开始打包...")
    result = subprocess.run([sys.executable, "-m", "PyInstaller", "traework.spec"])
    
    if result.returncode != 0:
        print("❌ 打包失败！")
        return
    
    print_step("✅ 打包成功！")
    
    # 7. 显示后续步骤
    print("\n" + "="*60)
    print("  🎉 发布准备完成！")
    print("="*60)
    print("\n接下来请按以下步骤操作：")
    print("\n1. 提交代码到 GitHub:")
    print("   git add .")
    print(f"   git commit -m \"Release v{new_version}\"")
    print("   git push")
    print("\n2. 在 GitHub 创建 Release:")
    print("   - 访问: https://github.com/{}/{}/releases/new".format(GITHUB_USERNAME, GITHUB_REPO))
    print("   - Tag: v{}".format(new_version))
    print("   - 上传 dist/TRAEWORK.exe")
    print("\n3. 完成！用户打开软件就能检测到更新了！")
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
