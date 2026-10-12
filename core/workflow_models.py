"""
Workflow Models — Data models cho workflow nodes & graph.
Hỗ trợ nhiều loại node: Trigger, Action, AI, File, Condition, Loop, Web.
Serialization JSON đầy đủ.
"""

import json
import uuid
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from enum import Enum


class NodeType(str, Enum):
    """Các loại node trong workflow."""
    TRIGGER = "trigger"
    ACTION = "action"
    AI = "ai"
    FILE = "file"
    CONDITION = "condition"
    LOOP = "loop"
    WEB = "web"
    DELAY = "delay"


class TriggerType(str, Enum):
    MANUAL = "manual"
    HOTKEY = "hotkey"
    SCHEDULE = "schedule"
    FILE_WATCH = "file_watch"


class AIAction(str, Enum):
    CHAT = "chat"
    VISION = "vision"
    SUMMARIZE = "summarize"
    TRANSLATE = "translate"
    GENERATE_WORKFLOW = "generate_workflow"
    ANALYZE = "analyze"


class FileAction(str, Enum):
    RENAME = "rename"
    MOVE = "move"
    COPY = "copy"
    DELETE = "delete"
    COMPRESS = "compress"
    AI_RENAME = "ai_rename"
    AI_CLASSIFY = "ai_classify"
    AI_SUMMARIZE = "ai_summarize"


class WebAction(str, Enum):
    OPEN_URL = "open_url"
    SCRAPE_TEXT = "scrape_text"
    FILL_FORM = "fill_form"
    DOWNLOAD = "download"


NODE_TYPE_NAMES = {
    NodeType.TRIGGER: "🎯 Điểm bắt đầu",
    NodeType.ACTION: "🖱️ Thao tác Desktop",
    NodeType.AI: "🤖 AI Gemini",
    NodeType.FILE: "📁 Xử lý File",
    NodeType.CONDITION: "🔀 Điều kiện IF/ELSE",
    NodeType.LOOP: "🔄 Vòng lặp",
    NodeType.WEB: "🌐 Web / URL",
    NodeType.DELAY: "⏳ Chờ/Nghỉ",
}

NODE_TYPE_COLORS = {
    NodeType.TRIGGER: "#22c55e",    # Green
    NodeType.ACTION: "#6366f1",     # Indigo
    NodeType.AI: "#f59e0b",         # Amber
    NodeType.FILE: "#06b6d4",       # Cyan
    NodeType.CONDITION: "#ec4899",  # Pink
    NodeType.LOOP: "#8b5cf6",       # Violet
    NodeType.WEB: "#3b82f6",        # Blue
    NodeType.DELAY: "#64748b",      # Slate
}


@dataclass
class WorkflowNode:
    """Một node trong workflow graph."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "Node mới"
    node_type: str = NodeType.ACTION
    enabled: bool = True

    # Visual position in canvas
    pos_x: float = 100.0
    pos_y: float = 100.0

    # Connections
    next_nodes: List[str] = field(default_factory=list)         # Node IDs tiếp theo
    condition_true_node: Optional[str] = None                    # Node nếu điều kiện TRUE
    condition_false_node: Optional[str] = None                   # Node nếu điều kiện FALSE

    # Parameters (tuỳ loại node)
    params: Dict[str, Any] = field(default_factory=dict)

    # Status (runtime)
    last_status: str = ""
    last_result: str = ""
    execution_count: int = 0

    def get_display_name(self) -> str:
        """Tên hiển thị đẹp."""
        type_icon = NODE_TYPE_NAMES.get(self.node_type, "⚡")
        return f"{type_icon.split(' ')[0]} {self.name}"

    def get_color(self) -> str:
        """Màu node theo loại."""
        return NODE_TYPE_COLORS.get(self.node_type, "#64748b")

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "WorkflowNode":
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        clean = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**clean)


@dataclass
class Workflow:
    """Một workflow hoàn chỉnh gồm nhiều nodes liên kết."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    name: str = "Workflow mới"
    description: str = ""
    nodes: List[WorkflowNode] = field(default_factory=list)
    start_node_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: "")
    updated_at: str = field(default_factory=lambda: "")

    # Execution settings
    max_iterations: int = 100
    timeout_seconds: int = 300
    stop_on_error: bool = True

    def add_node(self, node: WorkflowNode) -> str:
        """Thêm node, trả về node ID."""
        self.nodes.append(node)
        if len(self.nodes) == 1:
            self.start_node_id = node.id
        return node.id

    def remove_node(self, node_id: str):
        """Xoá node và các connection liên quan."""
        self.nodes = [n for n in self.nodes if n.id != node_id]
        for node in self.nodes:
            node.next_nodes = [nid for nid in node.next_nodes if nid != node_id]
            if node.condition_true_node == node_id:
                node.condition_true_node = None
            if node.condition_false_node == node_id:
                node.condition_false_node = None
        if self.start_node_id == node_id:
            self.start_node_id = self.nodes[0].id if self.nodes else None

    def get_node(self, node_id: str) -> Optional[WorkflowNode]:
        """Tìm node theo ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def connect_nodes(self, from_id: str, to_id: str):
        """Kết nối 2 nodes."""
        from_node = self.get_node(from_id)
        if from_node and to_id not in from_node.next_nodes:
            from_node.next_nodes.append(to_id)

    def disconnect_nodes(self, from_id: str, to_id: str):
        """Ngắt kết nối 2 nodes."""
        from_node = self.get_node(from_id)
        if from_node and to_id in from_node.next_nodes:
            from_node.next_nodes.remove(to_id)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "nodes": [n.to_dict() for n in self.nodes],
            "start_node_id": self.start_node_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "max_iterations": self.max_iterations,
            "timeout_seconds": self.timeout_seconds,
            "stop_on_error": self.stop_on_error,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Workflow":
        nodes_data = data.pop("nodes", [])
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        clean = {k: v for k, v in data.items() if k in valid_fields and k != "nodes"}
        wf = cls(**clean)
        wf.nodes = [WorkflowNode.from_dict(n) for n in nodes_data]
        return wf

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> "Workflow":
        data = json.loads(json_str)
        return cls.from_dict(data)

    def save(self, filepath: str):
        """Lưu workflow ra file JSON."""
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, filepath: str) -> "Workflow":
        """Load workflow từ file JSON."""
        with open(filepath, "r", encoding="utf-8") as f:
            return cls.from_json(f.read())
