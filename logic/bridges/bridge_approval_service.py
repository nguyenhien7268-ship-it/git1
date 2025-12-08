# Tên file: logic/bridges/bridge_approval_service.py
# (PHIÊN BẢN V11.0 - NEW: BRIDGE APPROVAL WORKFLOW SERVICE)

"""
Service quản lý workflow duyệt cầu (Bridge Approval).

Workflow:
1. Scanner quét và trả về danh sách cầu đề xuất (không tự động lưu)
2. UI hiển thị danh sách để user xem xét
3. User chọn cầu muốn thêm vào quản lý
4. Service này xử lý việc lưu các cầu đã chọn vào DB
"""

import sqlite3
from typing import List, Dict, Any, Tuple
from logic.db_manager import DB_NAME


class BridgeApprovalService:
    """Service xử lý việc duyệt và lưu cầu vào DB quản lý."""
    
    def __init__(self, db_name: str = None):
        self.db_name = db_name or DB_NAME
    
    def approve_single_bridge(self, bridge: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Duyệt và lưu 1 cầu vào DB.
        
        Args:
            bridge: Dictionary chứa thông tin cầu (từ scanner)
        
        Returns:
            (success, message)
        """
        if not bridge:
            return False, "Cầu không hợp lệ"
        
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Kiểm tra xem cầu đã tồn tại chưa
            bridge_name = bridge.get('name', '')
            cursor.execute("SELECT id FROM ManagedBridges WHERE name = ?", (bridge_name,))
            existing = cursor.fetchone()
            
            if existing:
                conn.close()
                return False, f"Cầu '{bridge_name}' đã tồn tại trong DB"
            
            # Chuẩn bị dữ liệu
            desc = bridge.get('display_desc', '')
            full_dan = bridge.get('full_dan', '')
            final_desc = f"{desc}. Dàn: {full_dan}" if full_dan else desc
            streak = bridge.get('streak', 0)
            final_desc += f". Thông {streak} kỳ."
            
            pos1_idx = bridge.get('pos1_idx')
            pos2_idx = bridge.get('pos2_idx')
            win_rate = bridge.get('win_rate', 0)
            
            # Lưu vào DB
            cursor.execute("""
                INSERT INTO ManagedBridges 
                (name, type, description, win_rate_text, current_streak, 
                 next_prediction_stl, is_enabled, pos1_idx, pos2_idx) 
                VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
            """, (
                bridge_name,
                bridge.get('type', ''),
                final_desc,
                f"{win_rate:.0f}%",
                streak,
                bridge.get('predicted_value', ''),
                pos1_idx,
                pos2_idx
            ))
            
            conn.commit()
            conn.close()
            
            return True, f"Đã thêm cầu '{bridge_name}' vào quản lý"
            
        except Exception as e:
            return False, f"Lỗi khi lưu cầu: {e}"
    
    def approve_multiple_bridges(self, bridges: List[Dict[str, Any]]) -> Tuple[int, int, str]:
        """
        Duyệt và lưu nhiều cầu vào DB.
        
        Args:
            bridges: Danh sách các cầu cần duyệt
        
        Returns:
            (success_count, failed_count, message)
        """
        if not bridges:
            return 0, 0, "Không có cầu nào để thêm"
        
        success_count = 0
        failed_count = 0
        errors = []
        
        for bridge in bridges:
            success, msg = self.approve_single_bridge(bridge)
            if success:
                success_count += 1
            else:
                failed_count += 1
                errors.append(msg)
        
        # Tạo message tổng kết
        result_msg = f"Đã thêm {success_count}/{len(bridges)} cầu vào quản lý"
        if failed_count > 0:
            result_msg += f"\nLỗi: {failed_count} cầu"
            if len(errors) <= 5:
                result_msg += "\n" + "\n".join(errors)
        
        return success_count, failed_count, result_msg
    
    def get_bridge_count_in_db(self, bridge_type: str = None) -> int:
        """
        Đếm số lượng cầu đang có trong DB.
        
        Args:
            bridge_type: Lọc theo loại (DE_DYNAMIC_K, DE_SET, etc). None = tất cả
        
        Returns:
            Số lượng cầu
        """
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            if bridge_type:
                cursor.execute("SELECT COUNT(*) FROM ManagedBridges WHERE type = ?", (bridge_type,))
            else:
                cursor.execute("SELECT COUNT(*) FROM ManagedBridges")
            
            count = cursor.fetchone()[0]
            conn.close()
            return count
            
        except Exception:
            return 0
    
    def clear_auto_bridges(self) -> Tuple[bool, str]:
        """
        Xóa tất cả cầu tự động (để chuẩn bị cho một đợt quét mới).
        CHỈ xóa cầu có type bắt đầu bằng 'DE_' (cầu tự động).
        
        Returns:
            (success, message)
        """
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Xóa cầu tự động
            cursor.execute("""
                DELETE FROM ManagedBridges 
                WHERE type IN ('DE_DYNAMIC_K', 'DE_POS_SUM', 'DE_SET', 
                               'DE_PASCAL', 'DE_KILLER', 'DE_MEMORY')
            """)
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            return True, f"Đã xóa {deleted_count} cầu tự động"
            
        except Exception as e:
            return False, f"Lỗi khi xóa cầu: {e}"


# Singleton instance
_approval_service = None

def get_approval_service(db_name: str = None) -> BridgeApprovalService:
    """Factory function để lấy service instance."""
    global _approval_service
    if _approval_service is None:
        _approval_service = BridgeApprovalService(db_name)
    return _approval_service


# Convenience functions
def approve_bridge(bridge: Dict[str, Any]) -> Tuple[bool, str]:
    """Duyệt 1 cầu."""
    return get_approval_service().approve_single_bridge(bridge)


def approve_bridges(bridges: List[Dict[str, Any]]) -> Tuple[int, int, str]:
    """Duyệt nhiều cầu."""
    return get_approval_service().approve_multiple_bridges(bridges)


def get_managed_bridge_count(bridge_type: str = None) -> int:
    """Đếm số cầu trong DB."""
    return get_approval_service().get_bridge_count_in_db(bridge_type)


def clear_auto_managed_bridges() -> Tuple[bool, str]:
    """Xóa tất cả cầu tự động."""
    return get_approval_service().clear_auto_bridges()
