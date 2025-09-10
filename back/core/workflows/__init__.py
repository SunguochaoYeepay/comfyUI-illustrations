#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流模块
包含各种模型的工作流创建器
"""

from .base_workflow import BaseWorkflow
from .flux_workflow import FluxWorkflow
from .flux1_workflow import Flux1Workflow
from .qwen_workflow import QwenWorkflow
from .qwen_fusion_workflow import QwenFusionWorkflow
from .wan_workflow import WanWorkflow
from .flux1_vector_workflow import Flux1VectorWorkflow
from .gemini_workflow import GeminiWorkflow

__all__ = ['BaseWorkflow', 'FluxWorkflow', 'Flux1Workflow', 'QwenWorkflow', 'QwenFusionWorkflow', 'WanWorkflow', 'Flux1VectorWorkflow', 'GeminiWorkflow']
