#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Settings Manager for Good-GYM
Handles persistence of user preferences across container restarts
"""

import os
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SettingsManager:
    """Manages application settings with automatic persistence"""
    
    def __init__(self, settings_file: str = 'data/user_settings.json'):
        """
        Initialize settings manager
        
        Args:
            settings_file: Path to settings JSON file
        """
        self.settings_file = settings_file
        self.settings: Dict[str, Any] = {}
        self._default_settings = {
            'exercise_type': 'overhead_press',
            'rtsp_url': 'rtsp://admin:ZYF001026@192.168.31.99:554/stream2',
            'source_type': 'rtsp',  # 'camera' or 'rtsp' or 'video'
            'model_type': 'balanced',
            'mirror_mode': True,
            'tts_mode': 'sound'  # 'sound' or 'ha'
        }
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
        
        # Load existing settings
        self.load()
    
    def load(self) -> None:
        """Load settings from file, or create with defaults if not exists"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    stored_settings = json.load(f)
                    # Merge with defaults to handle new settings keys
                    self.settings = {**self._default_settings, **stored_settings}
                    logger.info(f"[Settings] 已加载配置: {self.settings_file}")
            else:
                # Use defaults for first run
                self.settings = self._default_settings.copy()
                self.save()  # Create file with defaults
                logger.info(f"[Settings] 使用默认配置并创建文件: {self.settings_file}")
        except Exception as e:
            logger.error(f"[Settings] 加载配置失败: {e}, 使用默认配置")
            self.settings = self._default_settings.copy()
    
    def save(self) -> None:
        """Save current settings to file"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            logger.info(f"[Settings] 配置已保存: {self.settings_file}")
        except Exception as e:
            logger.error(f"[Settings] 保存配置失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value
        
        Args:
            key: Setting key
            default: Default value if key doesn't exist
            
        Returns:
            Setting value
        """
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any, save_immediately: bool = True) -> None:
        """
        Set a setting value
        
        Args:
            key: Setting key
            value: Setting value
            save_immediately: Whether to save to disk immediately
        """
        self.settings[key] = value
        if save_immediately:
            self.save()
    
    def update(self, updates: Dict[str, Any], save_immediately: bool = True) -> None:
        """
        Update multiple settings at once
        
        Args:
            updates: Dictionary of key-value pairs to update
            save_immediately: Whether to save to disk immediately
        """
        self.settings.update(updates)
        if save_immediately:
            self.save()
    
    def reset_to_defaults(self) -> None:
        """Reset all settings to default values"""
        self.settings = self._default_settings.copy()
        self.save()
        logger.info("[Settings] 配置已重置为默认值")
    
    def get_all(self) -> Dict[str, Any]:
        """Get all settings as dictionary"""
        return self.settings.copy()
