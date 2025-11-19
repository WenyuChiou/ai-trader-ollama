# src/utils/memory_scorer.py
"""
记忆重要性评分系统
用于评估记忆的重要性，优化压缩和检索策略
"""
from __future__ import annotations
from typing import Dict, Any, Optional
from datetime import date, timedelta
import math


class MemoryScorer:
    """
    记忆重要性评分器
    
    评分维度：
    1. 交易影响：基于P&L、交易量
    2. 决策质量：基于后续表现
    3. 信息密度：基于关键信息量
    4. 时间衰减：越新越重要
    """
    
    def __init__(
        self,
        time_decay_factor: float = 0.95,  # 每天衰减5%
        pnl_weight: float = 0.3,
        volume_weight: float = 0.2,
        info_density_weight: float = 0.2,
        time_weight: float = 0.3,
    ):
        """
        初始化评分器
        
        参数:
        - time_decay_factor: 时间衰减因子（每天）
        - pnl_weight: P&L权重
        - volume_weight: 交易量权重
        - info_density_weight: 信息密度权重
        - time_weight: 时间权重
        """
        self.time_decay_factor = time_decay_factor
        self.pnl_weight = pnl_weight
        self.volume_weight = volume_weight
        self.info_density_weight = info_density_weight
        self.time_weight = time_weight
    
    def calculate_importance_score(
        self,
        memory: Dict[str, Any],
        date_str: Optional[str] = None,
    ) -> float:
        """
        计算记忆重要性分数（0-1）
        
        参数:
        - memory: 记忆字典
        - date_str: 日期字符串（如果memory中没有）
        
        返回:
        - 重要性分数（0-1，越高越重要）
        """
        date_key = date_str or memory.get("date", "")
        memory_date = self._parse_date(date_key)
        days_ago = (date.today() - memory_date).days if memory_date else 999
        
        # 1. 时间衰减分数（越新越高）
        time_score = self._calculate_time_score(days_ago)
        
        # 2. 交易影响分数
        pnl_score = self._calculate_pnl_score(memory)
        
        # 3. 交易量分数
        volume_score = self._calculate_volume_score(memory)
        
        # 4. 信息密度分数
        density_score = self._calculate_info_density_score(memory)
        
        # 加权平均
        total_score = (
            self.time_weight * time_score +
            self.pnl_weight * pnl_score +
            self.volume_weight * volume_score +
            self.info_density_weight * density_score
        )
        
        return min(1.0, max(0.0, total_score))
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """解析日期字符串"""
        try:
            from datetime import datetime
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            return None
    
    def _calculate_time_score(self, days_ago: int) -> float:
        """计算时间分数（指数衰减）"""
        if days_ago < 0:
            return 1.0
        
        # 指数衰减：score = decay_factor ^ days_ago
        return math.pow(self.time_decay_factor, days_ago)
    
    def _calculate_pnl_score(self, memory: Dict[str, Any]) -> float:
        """计算P&L分数"""
        executed_trades = memory.get("executed_trades", [])
        if not executed_trades:
            return 0.5  # 无交易，中等分数
        
        total_pnl = 0.0
        total_abs_pnl = 0.0
        
        for trade in executed_trades:
            if isinstance(trade, dict):
                pnl = trade.get("realized_pnl", 0.0) or trade.get("pnl", 0.0)
                if pnl:
                    total_pnl += pnl
                    total_abs_pnl += abs(pnl)
        
        if total_abs_pnl == 0:
            return 0.5
        
        # 归一化：-1到1映射到0到1
        normalized_pnl = total_pnl / (total_abs_pnl + 1.0)
        return (normalized_pnl + 1.0) / 2.0
    
    def _calculate_volume_score(self, memory: Dict[str, Any]) -> float:
        """计算交易量分数"""
        decision = memory.get("decision", {})
        buy_orders = decision.get("buy_orders", [])
        sell_orders = decision.get("sell_orders", [])
        
        total_orders = len(buy_orders) + len(sell_orders)
        
        # 归一化：0-20个订单映射到0-1
        return min(1.0, total_orders / 20.0)
    
    def _calculate_info_density_score(self, memory: Dict[str, Any]) -> float:
        """计算信息密度分数"""
        score = 0.0
        max_score = 0.0
        
        # 检查各个字段
        checks = [
            ("market_analysis", 0.2),
            ("discussion", 0.3),
            ("risk_report", 0.2),
            ("decision", 0.2),
            ("portfolio_snapshot", 0.1),
        ]
        
        for field, weight in checks:
            max_score += weight
            if memory.get(field):
                field_data = memory.get(field, {})
                if isinstance(field_data, dict):
                    # 检查字段丰富度
                    field_score = min(1.0, len(field_data) / 5.0)
                elif isinstance(field_data, (list, str)):
                    # 检查内容长度
                    content_len = len(str(field_data))
                    field_score = min(1.0, content_len / 500.0)
                else:
                    field_score = 0.5
                
                score += weight * field_score
        
        if max_score == 0:
            return 0.5
        
        return score / max_score
    
    def should_keep_detailed(self, memory: Dict[str, Any], date_str: Optional[str] = None) -> bool:
        """
        判断是否应该保留详细信息
        
        参数:
        - memory: 记忆字典
        - date_str: 日期字符串
        
        返回:
        - True表示应该保留详细信息，False表示可以压缩
        """
        score = self.calculate_importance_score(memory, date_str)
        return score >= 0.6  # 阈值：60%以上保留详细信息
    
    def get_compression_level(self, memory: Dict[str, Any], date_str: Optional[str] = None) -> str:
        """
        获取压缩级别
        
        参数:
        - memory: 记忆字典
        - date_str: 日期字符串
        
        返回:
        - "full": 完整保留
        - "summary": 摘要保留
        - "compressed": 高度压缩
        """
        score = self.calculate_importance_score(memory, date_str)
        
        if score >= 0.7:
            return "full"
        elif score >= 0.4:
            return "summary"
        else:
            return "compressed"

