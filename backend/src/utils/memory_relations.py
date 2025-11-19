# src/utils/memory_relations.py
"""
记忆关联分析系统
用于发现和存储记忆之间的关联关系
"""
from __future__ import annotations
from typing import Dict, Any, List, Set, Tuple
from collections import defaultdict
import json
from pathlib import Path


class MemoryRelationAnalyzer:
    """
    记忆关联分析器
    
    发现记忆之间的关联：
    1. 相同股票的记忆关联
    2. 相似市场条件的记忆关联
    3. 相似决策模式的记忆关联
    """
    
    def __init__(self, root: Path):
        """
        初始化关联分析器
        
        参数:
        - root: 存储根目录
        """
        self.root = Path(root)
        self.relations_file = self.root / "memory" / "index" / "memory_relations.json"
        self.relations: Dict[str, Dict[str, Any]] = {}
        self._load_relations()
    
    def _load_relations(self) -> None:
        """加载关联关系"""
        if self.relations_file.exists():
            try:
                with self.relations_file.open("r", encoding="utf-8") as f:
                    self.relations = json.load(f)
            except Exception:
                self.relations = {}
    
    def _save_relations(self) -> None:
        """保存关联关系"""
        try:
            self.relations_file.parent.mkdir(parents=True, exist_ok=True)
            with self.relations_file.open("w", encoding="utf-8") as f:
                json.dump(self.relations, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[RELATIONS ERROR] Failed to save relations: {e}")
    
    def analyze_memory_relations(self, memory: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        分析单个记忆的关联
        
        参数:
        - memory: 记忆字典
        
        返回:
        - 关联记忆的日期列表（按关联类型分组）
        """
        date_str = memory.get("date", "")
        if not date_str:
            return {}
        
        relations = {
            "same_stocks": [],
            "similar_stance": [],
            "similar_action": [],
        }
        
        # 提取当前记忆的特征
        decision = memory.get("decision", {})
        stocks = set(
            [order.get("symbol") for order in decision.get("buy_orders", []) if order.get("symbol")]
            + [order.get("symbol") for order in decision.get("sell_orders", []) if order.get("symbol")]
        )
        stance = memory.get("discussion", {}).get("final_stance", "")
        action = decision.get("action", "")
        
        # 查找关联记忆
        for other_date, other_meta in self.relations.items():
            if other_date == date_str:
                continue
            
            other_stocks = set(other_meta.get("stocks_involved", []))
            other_stance = other_meta.get("stance", "")
            other_action = other_meta.get("action", "")
            
            # 相同股票
            if stocks and other_stocks and stocks.intersection(other_stocks):
                relations["same_stocks"].append(other_date)
            
            # 相似立场
            if stance and other_stance and stance == other_stance:
                relations["similar_stance"].append(other_date)
            
            # 相似动作
            if action and other_action and action == other_action:
                relations["similar_action"].append(other_date)
        
        return relations
    
    def update_relations(self, memory: Dict[str, Any]) -> None:
        """
        更新关联关系
        
        参数:
        - memory: 记忆字典
        """
        date_str = memory.get("date", "")
        if not date_str:
            return
        
        # 提取记忆特征
        decision = memory.get("decision", {})
        buy_orders = decision.get("buy_orders", [])
        sell_orders = decision.get("sell_orders", [])
        
        stocks_involved = list(set([
            order.get("symbol")
            for order in buy_orders + sell_orders
            if order.get("symbol")
        ]))
        
        self.relations[date_str] = {
            "date": date_str,
            "stance": memory.get("discussion", {}).get("final_stance"),
            "stocks_involved": stocks_involved,
            "action": decision.get("action"),
            "risk_level": memory.get("risk_report", {}).get("overall_risk_level"),
        }
        
        self._save_relations()
    
    def get_related_memories(
        self,
        date_str: str,
        relation_type: Optional[str] = None,
    ) -> List[str]:
        """
        获取关联记忆
        
        参数:
        - date_str: 日期字符串
        - relation_type: 关联类型（"same_stocks", "similar_stance", "similar_action"），None表示所有
        
        返回:
        - 关联记忆的日期列表
        """
        if date_str not in self.relations:
            return []
        
        # 分析关联（需要加载完整记忆，这里简化处理）
        # 实际应该预先计算并存储
        related_dates = set()
        
        current_meta = self.relations[date_str]
        current_stocks = set(current_meta.get("stocks_involved", []))
        current_stance = current_meta.get("stance", "")
        current_action = current_meta.get("action", "")
        
        for other_date, other_meta in self.relations.items():
            if other_date == date_str:
                continue
            
            other_stocks = set(other_meta.get("stocks_involved", []))
            other_stance = other_meta.get("stance", "")
            other_action = other_meta.get("action", "")
            
            if relation_type is None or relation_type == "same_stocks":
                if current_stocks and other_stocks and current_stocks.intersection(other_stocks):
                    related_dates.add(other_date)
            
            if relation_type is None or relation_type == "similar_stance":
                if current_stance and other_stance and current_stance == other_stance:
                    related_dates.add(other_date)
            
            if relation_type is None or relation_type == "similar_action":
                if current_action and other_action and current_action == other_action:
                    related_dates.add(other_date)
        
        return list(related_dates)
    
    def remove_relation(self, date_str: str) -> None:
        """删除关联关系"""
        if date_str in self.relations:
            del self.relations[date_str]
            self._save_relations()

