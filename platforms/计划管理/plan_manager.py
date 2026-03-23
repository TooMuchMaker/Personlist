import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class PlanManager:
    def __init__(self, json_file: str):
        self.json_file = json_file
        self.data = self.load_data()
    
    def load_data(self) -> Dict:
        if os.path.exists(self.json_file):
            with open(self.json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "plans": {
                "long_term": [],
                "mid_term": [],
                "short_term": []
            },
            "current_stage": {
                "name": "当前阶段",
                "start_date": "",
                "end_date": ""
            },
            "settings": {
                "sort_options": ["priority", "start_date", "end_date", "created_at"],
                "priority_levels": ["high", "medium", "low"],
                "status_options": ["pending", "in_progress", "completed", "cancelled"]
            }
        }
    
    def save_data(self):
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def add_plan(self, plan_type: str, title: str, description: str = "", 
                 priority: str = "medium", start_date: str = "", end_date: str = "",
                 tags: List[str] = None, creator: str = "user"):
        if plan_type not in self.data["plans"]:
            print(f"错误：计划类型 '{plan_type}' 不存在")
            return False
        
        if priority not in self.data["settings"]["priority_levels"]:
            print(f"错误：优先级 '{priority}' 不存在")
            return False
        
        plan = {
            "id": len(self.data["plans"][plan_type]) + 1,
            "title": title,
            "description": description,
            "priority": priority,
            "status": "pending",
            "start_date": start_date,
            "end_date": end_date,
            "tags": tags or [],
            "creator": creator,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "progress": 0
        }
        
        self.data["plans"][plan_type].append(plan)
        self.save_data()
        print(f"成功添加计划：{title}")
        return True
    
    def list_plans(self, plan_type: str = None, status: str = None, 
                   sort_by: str = "priority"):
        if plan_type:
            if plan_type not in self.data["plans"]:
                print(f"错误：计划类型 '{plan_type}' 不存在")
                return
            
            plans = self.data["plans"][plan_type]
            if status:
                plans = [p for p in plans if p["status"] == status]
            
            plans = self.sort_plans(plans, sort_by)
            self.display_plans(plans, plan_type)
        else:
            for ptype in self.data["plans"]:
                plans = self.data["plans"][ptype]
                if status:
                    plans = [p for p in plans if p["status"] == status]
                plans = self.sort_plans(plans, sort_by)
                self.display_plans(plans, ptype)
    
    def sort_plans(self, plans: List[Dict], sort_by: str) -> List[Dict]:
        if sort_by == "priority":
            priority_order = {"high": 0, "medium": 1, "low": 2}
            return sorted(plans, key=lambda x: priority_order.get(x["priority"], 1))
        elif sort_by == "start_date":
            return sorted(plans, key=lambda x: x["start_date"] or "9999-99-99")
        elif sort_by == "end_date":
            return sorted(plans, key=lambda x: x["end_date"] or "9999-99-99")
        elif sort_by == "created_at":
            return sorted(plans, key=lambda x: x["created_at"], reverse=True)
        else:
            return plans
    
    def display_plans(self, plans: List[Dict], plan_type: str):
        if not plans:
            return
        
        type_names = {
            "long_term": "长期计划",
            "mid_term": "中期计划",
            "short_term": "短期计划"
        }
        
        print(f"\n{'='*60}")
        print(f"{type_names.get(plan_type, plan_type)}")
        print(f"{'='*60}")
        
        for plan in plans:
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            status_emoji = {
                "pending": "⏳",
                "in_progress": "🔄",
                "completed": "✅",
                "cancelled": "❌"
            }
            
            print(f"\n{priority_emoji.get(plan['priority'], '⚪')} [{plan['id']}] {plan['title']}")
            print(f"   状态: {status_emoji.get(plan['status'], '❓')} {plan['status']}")
            print(f"   创建者: {plan['creator']}")
            if plan['description']:
                print(f"   描述: {plan['description']}")
            if plan['start_date']:
                print(f"   开始日期: {plan['start_date']}")
            if plan['end_date']:
                print(f"   结束日期: {plan['end_date']}")
            if plan['tags']:
                print(f"   标签: {', '.join(plan['tags'])}")
            print(f"   进度: {plan['progress']}%")
    
    def update_plan(self, plan_type: str, plan_id: int, **kwargs):
        if plan_type not in self.data["plans"]:
            print(f"错误：计划类型 '{plan_type}' 不存在")
            return False
        
        for plan in self.data["plans"][plan_type]:
            if plan["id"] == plan_id:
                for key, value in kwargs.items():
                    if key in plan:
                        plan[key] = value
                plan["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.save_data()
                print(f"成功更新计划：{plan['title']}")
                return True
        
        print(f"错误：找不到ID为 {plan_id} 的计划")
        return False
    
    def delete_plan(self, plan_type: str, plan_id: int):
        if plan_type not in self.data["plans"]:
            print(f"错误：计划类型 '{plan_type}' 不存在")
            return False
        
        for i, plan in enumerate(self.data["plans"][plan_type]):
            if plan["id"] == plan_id:
                deleted_plan = self.data["plans"][plan_type].pop(i)
                self.save_data()
                print(f"成功删除计划：{deleted_plan['title']}")
                return True
        
        print(f"错误：找不到ID为 {plan_id} 的计划")
        return False
    
    def set_current_stage(self, name: str, start_date: str, end_date: str):
        self.data["current_stage"] = {
            "name": name,
            "start_date": start_date,
            "end_date": end_date
        }
        self.save_data()
        print(f"成功设置当前阶段：{name} ({start_date} ~ {end_date})")
    
    def get_stage_plans(self, sort_by: str = "priority"):
        stage_start = self.data["current_stage"]["start_date"]
        stage_end = self.data["current_stage"]["end_date"]
        
        if not stage_start or not stage_end:
            print("错误：请先设置当前阶段")
            return
        
        print(f"\n{'='*60}")
        print(f"阶段计划：{self.data['current_stage']['name']}")
        print(f"时间范围：{stage_start} ~ {stage_end}")
        print(f"{'='*60}")
        
        all_plans = []
        for plan_type in self.data["plans"]:
            for plan in self.data["plans"][plan_type]:
                if self.is_plan_in_stage(plan, stage_start, stage_end):
                    plan["plan_type"] = plan_type
                    all_plans.append(plan)
        
        all_plans = self.sort_plans(all_plans, sort_by)
        self.display_stage_plans(all_plans)
    
    def is_plan_in_stage(self, plan: Dict, stage_start: str, stage_end: str) -> bool:
        if not plan["start_date"] and not plan["end_date"]:
            return False
        
        if plan["start_date"] and plan["end_date"]:
            return (plan["start_date"] <= stage_end and 
                    plan["end_date"] >= stage_start)
        elif plan["start_date"]:
            return plan["start_date"] <= stage_end
        elif plan["end_date"]:
            return plan["end_date"] >= stage_start
        
        return False
    
    def display_stage_plans(self, plans: List[Dict]):
        if not plans:
            print("\n当前阶段没有计划")
            return
        
        type_names = {
            "long_term": "长期",
            "mid_term": "中期",
            "short_term": "短期"
        }
        
        for plan in plans:
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            status_emoji = {
                "pending": "⏳",
                "in_progress": "🔄",
                "completed": "✅",
                "cancelled": "❌"
            }
            
            print(f"\n{priority_emoji.get(plan['priority'], '⚪')} [{type_names.get(plan['plan_type'], '')}-{plan['id']}] {plan['title']}")
            print(f"   状态: {status_emoji.get(plan['status'], '❓')} {plan['status']}")
            print(f"   创建者: {plan['creator']}")
            if plan['start_date']:
                print(f"   开始日期: {plan['start_date']}")
            if plan['end_date']:
                print(f"   结束日期: {plan['end_date']}")
            print(f"   进度: {plan['progress']}%")

def main():
    json_file = os.path.join(os.path.dirname(__file__), 'plans.json')
    manager = PlanManager(json_file)
    
    while True:
        print("\n" + "="*60)
        print("TRAEWORK 计划管理系统")
        print("="*60)
        print("1. 添加计划")
        print("2. 查看所有计划")
        print("3. 查看特定类型计划")
        print("4. 更新计划")
        print("5. 删除计划")
        print("6. 设置当前阶段")
        print("7. 查看阶段计划")
        print("8. 退出")
        print("="*60)
        
        choice = input("\n请选择操作 (1-8): ").strip()
        
        if choice == "1":
            print("\n计划类型:")
            print("1. long_term (长期计划)")
            print("2. mid_term (中期计划)")
            print("3. short_term (短期计划)")
            plan_type_choice = input("选择计划类型 (1-3): ").strip()
            
            plan_types = {"1": "long_term", "2": "mid_term", "3": "short_term"}
            plan_type = plan_types.get(plan_type_choice)
            
            if not plan_type:
                print("无效的选择")
                continue
            
            title = input("计划标题: ").strip()
            description = input("计划描述 (可选): ").strip()
            
            print("\n优先级:")
            print("1. high (高)")
            print("2. medium (中)")
            print("3. low (低)")
            priority_choice = input("选择优先级 (1-3, 默认中): ").strip() or "2"
            priorities = {"1": "high", "2": "medium", "3": "low"}
            priority = priorities.get(priority_choice, "medium")
            
            start_date = input("开始日期 (YYYY-MM-DD, 可选): ").strip()
            end_date = input("结束日期 (YYYY-MM-DD, 可选): ").strip()
            
            tags_input = input("标签 (用逗号分隔, 可选): ").strip()
            tags = [tag.strip() for tag in tags_input.split(",")] if tags_input else []
            
            creator = input("创建者 (user/trae, 默认user): ").strip() or "user"
            
            manager.add_plan(plan_type, title, description, priority, 
                           start_date, end_date, tags, creator)
        
        elif choice == "2":
            print("\n排序方式:")
            print("1. priority (按优先级)")
            print("2. start_date (按开始日期)")
            print("3. end_date (按结束日期)")
            print("4. created_at (按创建时间)")
            sort_choice = input("选择排序方式 (1-4, 默认优先级): ").strip() or "1"
            
            sort_options = {"1": "priority", "2": "start_date", "3": "end_date", "4": "created_at"}
            sort_by = sort_options.get(sort_choice, "priority")
            
            status_filter = input("筛选状态 (pending/in_progress/completed/cancelled, 可选): ").strip()
            manager.list_plans(sort_by=sort_by, status=status_filter or None)
        
        elif choice == "3":
            print("\n计划类型:")
            print("1. long_term (长期计划)")
            print("2. mid_term (中期计划)")
            print("3. short_term (短期计划)")
            plan_type_choice = input("选择计划类型 (1-3): ").strip()
            
            plan_types = {"1": "long_term", "2": "mid_term", "3": "short_term"}
            plan_type = plan_types.get(plan_type_choice)
            
            if not plan_type:
                print("无效的选择")
                continue
            
            sort_choice = input("排序方式 (1-4, 默认优先级): ").strip() or "1"
            sort_options = {"1": "priority", "2": "start_date", "3": "end_date", "4": "created_at"}
            sort_by = sort_options.get(sort_choice, "priority")
            
            manager.list_plans(plan_type, sort_by=sort_by)
        
        elif choice == "4":
            print("\n计划类型:")
            print("1. long_term (长期计划)")
            print("2. mid_term (中期计划)")
            print("3. short_term (短期计划)")
            plan_type_choice = input("选择计划类型 (1-3): ").strip()
            
            plan_types = {"1": "long_term", "2": "mid_term", "3": "short_term"}
            plan_type = plan_types.get(plan_type_choice)
            
            if not plan_type:
                print("无效的选择")
                continue
            
            plan_id = input("计划ID: ").strip()
            
            print("\n可更新字段:")
            print("1. title (标题)")
            print("2. description (描述)")
            print("3. priority (优先级)")
            print("4. status (状态)")
            print("5. start_date (开始日期)")
            print("6. end_date (结束日期)")
            print("7. progress (进度)")
            
            field_choice = input("选择要更新的字段 (1-7): ").strip()
            fields = {
                "1": "title", "2": "description", "3": "priority", 
                "4": "status", "5": "start_date", "6": "end_date", "7": "progress"
            }
            field = fields.get(field_choice)
            
            if not field:
                print("无效的选择")
                continue
            
            value = input(f"新的{field}值: ").strip()
            
            if field == "progress":
                try:
                    value = int(value)
                except ValueError:
                    print("进度必须是数字")
                    continue
            
            manager.update_plan(plan_type, int(plan_id), **{field: value})
        
        elif choice == "5":
            print("\n计划类型:")
            print("1. long_term (长期计划)")
            print("2. mid_term (中期计划)")
            print("3. short_term (短期计划)")
            plan_type_choice = input("选择计划类型 (1-3): ").strip()
            
            plan_types = {"1": "long_term", "2": "mid_term", "3": "short_term"}
            plan_type = plan_types.get(plan_type_choice)
            
            if not plan_type:
                print("无效的选择")
                continue
            
            plan_id = input("计划ID: ").strip()
            manager.delete_plan(plan_type, int(plan_id))
        
        elif choice == "6":
            name = input("阶段名称: ").strip()
            start_date = input("开始日期 (YYYY-MM-DD): ").strip()
            end_date = input("结束日期 (YYYY-MM-DD): ").strip()
            manager.set_current_stage(name, start_date, end_date)
        
        elif choice == "7":
            print("\n排序方式:")
            print("1. priority (按优先级)")
            print("2. start_date (按开始日期)")
            print("3. end_date (按结束日期)")
            print("4. created_at (按创建时间)")
            sort_choice = input("选择排序方式 (1-4, 默认优先级): ").strip() or "1"
            
            sort_options = {"1": "priority", "2": "start_date", "3": "end_date", "4": "created_at"}
            sort_by = sort_options.get(sort_choice, "priority")
            
            manager.get_stage_plans(sort_by)
        
        elif choice == "8":
            print("\n感谢使用TRAEWORK计划管理系统！")
            break
        
        else:
            print("无效的选择，请重新输入")

if __name__ == "__main__":
    main()
