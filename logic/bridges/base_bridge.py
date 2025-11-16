from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd

class BridgeContext:
    """
    (GĐ 2) Đối tượng chứa dữ liệu và tham số cần thiết 
    để một cầu (Bridge) chạy tính toán.
    """
    def __init__(self, historical_data: pd.DataFrame, parameters: Optional[Dict[str, Any]] = None):
        """
        Args:
            historical_data (pd.DataFrame): 
                Dữ liệu lịch sử (đã được chuẩn hóa bởi DataService). 
                Thông thường, đây là 1 hoặc 2 hàng (rows) cuối cùng 
                (kỳ trước) để tính toán cho kỳ hiện tại.
            parameters (Optional[Dict[str, Any]]): 
                Các tham số riêng của cầu (ví dụ: chu kỳ, độ lệch...).
        """
        self.historical_data = historical_data 
        self.parameters = parameters or {}

class BridgeResult:
    """
    (GĐ 2) Đối tượng chuẩn hóa đầu ra của một cầu (Bridge).
    """
    def __init__(self, 
                 bridge_id: str, 
                 predictions: List[str], 
                 prediction_type: str = 'STL', 
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Args:
            bridge_id (str): ID định danh duy nhất (ví dụ: 'Classic_C1', 'V17_GDB[0]+G1[4]')
            predictions (List[str]): Danh sách dự đoán (ví dụ: ['01', '10'])
            prediction_type (str): Loại dự đoán (ví dụ: 'STL', 'Loto', 'DanDe')
            metadata (Optional[Dict[str, Any]]): 
                Thông tin thêm (ví dụ: {'win_rate': 55.1, 'streak': 2})
        """
        self.bridge_id = bridge_id 
        self.predictions = predictions 
        self.prediction_type = prediction_type
        self.metadata = metadata or {} 

class BaseBridge(ABC):
    """
    (GĐ 2) "Hợp đồng Cầu" (Bridge Interface) - Lớp Trừu tượng (Abstract Base Class).
    
    Tất cả các "plug-in" cầu (Classic, V16, Memory) phải kế thừa 
    từ lớp này và triển khai các phương thức trừu tượng.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Hàm khởi tạo cơ sở, chạy _initialize().
        """
        self.config = config or {}
        self._initialize()

    def _initialize(self):
        """Hàm (private) tùy chọn để logic con (child) ghi đè."""
        pass

    @abstractmethod
    def get_bridge_name(self) -> str:
        """
        Trả về tên định danh duy nhất cho *nhóm* cầu này.
        (Ví dụ: 'Classic_15_Bridges', 'V17_Managed_Bridges')
        """
        pass

    @abstractmethod
    def get_bridge_version(self) -> str:
        """Trả về phiên bản của logic cầu (ví dụ: 'v1.0')."""
        pass

    @abstractmethod
    def calculate_predictions(self, context: BridgeContext) -> List[BridgeResult]:
        """
        Phương thức lõi: Tính toán dự đoán dựa trên dữ liệu lịch sử.
        
        Trả về một *danh sách* các BridgeResult, vì một "Bridge Plug-in" 
        có thể tạo ra nhiều kết quả.
        """
        pass