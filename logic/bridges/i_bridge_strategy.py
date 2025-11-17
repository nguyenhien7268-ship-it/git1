# logic/bridges/i_bridge_strategy.py

from abc import ABC, abstractmethod
from typing import Any, Dict


class IBridgeStrategy(ABC):
    """
    Interface (Abstract Base Class) cho mọi Chiến lược Phân tích (Bridge).
    Mọi Bridge cụ thể phải kế thừa lớp này và triển khai các phương thức trừu tượng.
    """

    def __init__(self, data_repository: Any, config_manager: Any):
        """
        Khởi tạo Strategy với các Dependency cần thiết.
        (Thay thế Any bằng kiểu dữ liệu chính xác của DataRepository và ConfigManager trong hệ thống của bạn)
        """
        self.data_repo = data_repository
        self.config_manager = config_manager

    @abstractmethod
    def analyze(self, current_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Thực hiện phân tích dữ liệu và trả về kết quả dự đoán.
        """
        pass

    @abstractmethod
    def get_info(self) -> Dict[str, str]:
        """
        Trả về tên, phiên bản và mô tả ngắn gọn của chiến lược.
        """
        pass

    @property
    @abstractmethod
    def STRATEGY_KEY(self) -> str:
        """
        Khóa định danh duy nhất (dạng chuỗi viết thường) cho chiến lược này, dùng trong Factory.
        """
        pass
