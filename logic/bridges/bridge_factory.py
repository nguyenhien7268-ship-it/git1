# logic/bridges/bridge_factory.py

from typing import Dict, Type, Any, List
from .i_bridge_strategy import IBridgeStrategy

# Import các lớp Bridge cụ thể
# Lưu ý: Cần đảm bảo các lớp này đã tồn tại và tuân thủ IBridgeStrategy
from .bridges_classic import ClassicBridge
from .bridges_memory import MemoryBridge
from .bridges_v16 import V16Bridge

# Sử dụng Dict[str, Type[IBridgeStrategy]] để ánh xạ KEY tới Class
# Dùng một instance tạm thời (None, None) để lấy KEY một cách an toàn
STRATEGY_MAP: Dict[str, Type[IBridgeStrategy]] = {
    "classic": ClassicBridge,
    "memory": MemoryBridge,
    "v16": V16Bridge,
    # Thêm các Strategy mới vào đây khi phát triển
}

def create_bridge_strategy(strategy_key: str, data_repository: Any, config_manager: Any) -> IBridgeStrategy:
    """
    Factory method để khởi tạo và trả về đối tượng Bridge Strategy phù hợp.
    """
    key = strategy_key.lower()
    strategy_class = STRATEGY_MAP.get(key)
    
    if strategy_class:
        # Khởi tạo đối tượng Strategy với các dependency cần thiết
        return strategy_class(data_repository, config_manager)
    else:
        raise ValueError(f"Strategy type '{strategy_key}' is not supported or does not exist.")

def get_available_strategies() -> List[str]:
    """
    Trả về danh sách các khóa chiến lược có sẵn.
    """
    return list(STRATEGY_MAP.keys())