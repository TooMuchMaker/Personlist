#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRAEWORK 平台模块
"""

from typing import Dict, Optional, Type
from traework.platforms.base import BasePlatform
from traework.platforms.main import MainPlatform

PLATFORMS: Dict[str, Type[BasePlatform]] = {
    'main': MainPlatform,
}


def get_platform(platform_id: str) -> Optional[Type[BasePlatform]]:
    return PLATFORMS.get(platform_id)


def get_main_platform() -> Optional[MainPlatform]:
    return MainPlatform()
