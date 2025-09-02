#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flux1工作流实现
"""

from .base_workflow import BaseWorkflow


class Flux1Workflow(BaseWorkflow):
    """Flux1工作流创建器"""
    
    def create_workflow(self, reference_image_path: str, description: str, parameters):
        """创建Flux1工作流"""
        # 临时实现
        return {}
