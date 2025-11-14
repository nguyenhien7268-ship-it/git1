from abc import ABC, abstractmethod

class BaseBridge(ABC):
    """
    (MỚI - GĐ 2) Lớp Cơ sở Trừu tượng (Hợp đồng) cho tất cả các Cầu.

    Bất kỳ lớp Cầu nào (ví dụ: BacNhoBridge, V16Bridge) ĐỀU PHẢI
    kế thừa từ lớp này và triển khai TẤT CẢ các phương thức @abstractmethod.

    Điều này đảm bảo tính nhất quán và cho phép BridgeManager, Backtester
    làm việc với bất kỳ cầu nào mà không cần biết logic bên trong của nó.
    """

    def __init__(self, bridge_name, description=""):
        """
        Khởi tạo một cầu.
        
        Args:
            bridge_name (str): Tên duy nhất của cầu (ví dụ: "GDB[0] + G1[4]").
            description (str, optional): Mô tả về cầu.
        """
        self._bridge_name = bridge_name
        self._description = description

    @abstractmethod
    def get_bridge_name(self):
        """
        Trả về tên duy nhất, có thể nhận dạng của cầu.
        (Ví dụ: "GDB[0] + G1[4]", "Bạc Nhớ Đầu Câm 1")
        """
        pass

    @abstractmethod
    def get_bridge_description(self):
        """
        Trả về mô tả ngắn gọn về cách thức hoạt động của cầu.
        """
        pass

    @abstractmethod
    def calculate_predictions(self, data_service, historical_kys):
        """
        Phương thức tính toán cốt lõi.
        
        Đây là nơi logic "soi cầu" (ví dụ: bạc nhớ, ghép số) được thực thi
        dựa trên dữ liệu lịch sử được cung cấp.

        Args:
            data_service (DataService): Thực thể DataService (đã chứa toàn bộ dữ liệu).
            historical_kys (list): Danh sách các MaSoKy lịch sử (đã được lọc)
                                   mà cầu này nên sử dụng để tính toán.
                                   (Ví dụ: 3 ngày qua, 100 ngày qua...)

        Returns:
            list[dict]: Một danh sách các dự đoán cho NGÀY TIẾP THEO.
            Định dạng chuẩn:
            [
                {
                    "number": "12",             # Số dự đoán (STL)
                    "source_bridge": self.get_bridge_name(), # Tên cầu
                    "confidence": 0.85,         # (Tùy chọn) Độ tin cậy
                    "details": "Chi tiết..."    # (Tùy chọn) Giải thích
                },
                ...
            ]
            Nếu không có dự đoán, trả về [].
        """
        pass

    @abstractmethod
    def run_backtest(self, data_service, full_ky_list):
        """
        Chạy backtest (kiểm thử ngược) cho CHỈ cầu này.

        Args:
            data_service (DataService): Thực thể DataService.
            full_ky_list (list): TOÀN BỘ danh sách MaSoKy (sắp xếp TĂNG DẦN).

        Returns:
            dict: Một từ điển chứa kết quả thống kê của backtest.
            Định dạng chuẩn:
            {
                "bridge_name": self.get_bridge_name(),
                "total_days": 1000,
                "total_predictions": 500,
                "total_wins": 250,
                "win_rate": 0.50, # (total_wins / total_predictions)
                "win_history": [True, False, True, ...], # Lịch sử thắng/thua
                "max_lose_streak": 5,
                # ... (thêm các số liệu thống kê khác nếu cần)
            }
        """
        pass