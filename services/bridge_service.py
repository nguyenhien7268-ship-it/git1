# Tên file: services/bridge_service.py
# Service layer: Logic quản lý cầu

import traceback

# Import các hàm Data Repository với alias để hỗ trợ testing và mocking
try:
    from logic.data_repository import get_all_managed_bridges as data_repo_get_all_managed_bridges
    from logic.data_repository import get_bridge_by_name as data_repo_get_bridge_by_name
except ImportError:
    # Fallback nếu không import được
    data_repo_get_all_managed_bridges = None
    data_repo_get_bridge_by_name = None

# Import các hàm DB Manager với alias nếu cần
try:
    from logic.db_manager import update_managed_bridge as db_manager_update_managed_bridge
    from logic.db_manager import toggle_pin_bridge as db_manager_toggle_pin_bridge
    # Alias cho update_bridge_status (có thể là wrapper hoặc tên khác của update_managed_bridge)
    # Nếu hàm update_bridge_status không tồn tại, sử dụng update_managed_bridge làm alias
    try:
        from logic.db_manager import update_bridge_status as db_manager_update_bridge_status
    except ImportError:
        # Fallback: Sử dụng update_managed_bridge làm alias cho update_bridge_status
        from logic.db_manager import update_managed_bridge as db_manager_update_bridge_status
except ImportError:
    # Fallback nếu không import được
    db_manager_update_managed_bridge = None
    db_manager_toggle_pin_bridge = None
    db_manager_update_bridge_status = None

class BridgeService:
    """Service quản lý cầu (Lô & Đề)"""
    
    def __init__(self, db_name, logger=None):
        self.db_name = db_name
        self.logger = logger
    
    def _log(self, message):
        """Helper để log messages"""
        if self.logger:
            self.logger.log(message)
    
    def find_and_scan_bridges(self, all_data_ai, scan_limit=None):
        """
        Quét và tìm cầu Lô & Đề tự động.
        
        Args:
            all_data_ai: Dữ liệu A:I
            scan_limit: Giới hạn số kỳ để quét (None = toàn bộ)
        
        Returns:
            dict: Kết quả quét với keys 'lo' và 'de'
        """
        if not all_data_ai:
            return {"lo": None, "de": None}
        
        # Áp dụng scan limit nếu có
        if scan_limit and scan_limit > 0 and len(all_data_ai) > scan_limit:
            self._log(f"⚡ TỰ ĐỘNG TỐI ƯU: Hệ thống chỉ quét trên {scan_limit} kỳ gần nhất để tăng tốc độ.")
            scan_data = all_data_ai[-scan_limit:]
        else:
            scan_data = all_data_ai
        
        result = {"lo": None, "de": None}
        
        # 1. Quét cầu Lô
        try:
            self._log(">>> Đang quét cầu Lô (V17 & Bạc Nhớ)...")
            from lottery_service import find_and_auto_manage_bridges
            msg_lo = find_and_auto_manage_bridges(scan_data, self.db_name)
            result["lo"] = msg_lo
            self._log(f"Lô: {msg_lo}")
        except Exception as e:
            self._log(f"Lỗi quét Lô: {e}")
        
        # 2. Quét cầu Đề
        try:
            self._log(">>> Đang quét cầu Đề (Chạm/Tổng/Bộ)...")
            from logic.bridges.de_bridge_scanner import run_de_scanner
            count, bridges = run_de_scanner(scan_data)
            result["de"] = f"Đã tìm thấy và lưu {count} cầu Đề đang thông."
            self._log(result["de"])
        except Exception as e:
            self._log(f"Lỗi quét Đề: {e}")
        
        return result
    
    def prune_bad_bridges(self, all_data_ai):
        """
        Xóa các cầu có tỷ lệ thấp.
        
        Args:
            all_data_ai: Dữ liệu A:I
        
        Returns:
            str: Thông báo kết quả
        """
        if not all_data_ai:
            return "Lỗi: Không có dữ liệu"
        
        try:
            from lottery_service import prune_bad_bridges
            return prune_bad_bridges(all_data_ai, self.db_name)
        except ImportError:
            try:
                from services.bridge_service import prune_bad_bridges as _prune
                return _prune(all_data_ai, self.db_name)
            except:
                return "Lỗi: Không thể import prune_bad_bridges"
    
    def auto_manage_bridges(self, all_data_ai):
        """
        Tự động BẬT/TẮT cầu dựa trên tỷ lệ K2N.
        
        Args:
            all_data_ai: Dữ liệu A:I
        
        Returns:
            str: Thông báo kết quả
        """
        if not all_data_ai:
            return "Lỗi: Không có dữ liệu"
        
        try:
            from lottery_service import auto_manage_bridges
            return auto_manage_bridges(all_data_ai, self.db_name)
        except ImportError:
            return "Lỗi: Không thể import auto_manage_bridges"
    
    def smart_optimization(self, all_data_ai):
        """
        Gộp chức năng: Lọc cầu yếu + Quản lý tự động.
        
        Args:
            all_data_ai: Dữ liệu A:I
        
        Returns:
            tuple: (prune_message: str, manage_message: str)
        """
        if not all_data_ai:
            return None, None
        
        self._log("\n--- ⚡ BẮT ĐẦU: Tối Ưu Hóa Cầu ---")
        
        # Bước 1: Prune
        self._log("(1/2) Đang quét và TẮT các cầu hiệu quả kém...")
        msg_prune = self.prune_bad_bridges(all_data_ai)
        self._log(f"-> Kết quả lọc: {msg_prune}")
        
        # Bước 2: Auto Manage
        self._log("(2/2) Đang kiểm tra và BẬT lại các cầu tiềm năng...")
        msg_manage = self.auto_manage_bridges(all_data_ai)
        self._log(f"-> Kết quả quản lý: {msg_manage}")
        
        self._log("✅ TỐI ƯU HÓA HOÀN TẤT!")
        
        return msg_prune, msg_manage
    
    def update_k2n_cache(self, all_data_ai):
        """
        Cập nhật cache K2N cho các cầu.
        
        Args:
            all_data_ai: Dữ liệu A:I
        
        Returns:
            tuple: (pending_dict, cache_count, message)
        """
        if not all_data_ai:
            return {}, 0, "Lỗi: Không có dữ liệu"
        
        try:
            from lottery_service import run_and_update_all_bridge_K2N_cache
            pending_dict, cache_count, message = run_and_update_all_bridge_K2N_cache(all_data_ai, self.db_name)
            self._log(message)
            return pending_dict, cache_count, message
        except Exception as e:
            error_msg = f"Lỗi cập nhật K2N cache: {e}"
            self._log(error_msg)
            return {}, 0, error_msg
    
    def should_refresh_bridge_manager(self):
        """
        Kiểm tra xem có cần refresh bridge manager window không.
        
        Returns:
            bool: True nếu cần refresh
        """
        # Logic này sẽ được controller xử lý vì cần truy cập app.bridge_manager_window
        return True
    
    def get_de_bridge_config_by_name(self, bridge_name):
        """
        Lấy cấu hình cầu Đề từ DB bằng tên.
        
        Args:
            bridge_name: Tên cầu
        
        Returns:
            dict: Cấu hình cầu (bao gồm pos1_idx, pos2_idx, type, v.v.) hoặc None nếu không tìm thấy
        """
        try:
            # Sử dụng alias đã import ở cấp module (global)
            if data_repo_get_bridge_by_name is None:
                from logic.data_repository import get_bridge_by_name
                bridge_config = get_bridge_by_name(bridge_name, self.db_name)
            else:
                # Sử dụng alias đã được patch trong test
                bridge_config = data_repo_get_bridge_by_name(bridge_name, self.db_name)
            if not bridge_config:
                self._log(f"Không tìm thấy cầu '{bridge_name}' trong database.")
                return None
            
            # Kiểm tra xem có phải cầu Đề không
            bridge_type = bridge_config.get("type", "")
            if not (bridge_type.startswith("DE_") or "DE_" in bridge_name):
                # Không phải cầu Đề, trả về None
                return None
            
            return bridge_config
        except Exception as e:
            self._log(f"Lỗi lấy cấu hình cầu Đề '{bridge_name}': {e}")
            import traceback
            self._log(traceback.format_exc())
            return None
    
    def toggle_pin_bridge(self, bridge_name):
        """
        Đảo ngược trạng thái ghim của cầu (Phase 4 - Pinning).
        
        Args:
            bridge_name: Tên cầu
        
        Returns:
            tuple: (success: bool, message: str, new_pin_state: bool or None)
        """
        try:
            # Sử dụng alias đã import ở cấp module (global)
            # Nếu alias là None, import lại
            if db_manager_toggle_pin_bridge is None:
                from logic.db_manager import toggle_pin_bridge
                success, message, new_pin_state = toggle_pin_bridge(bridge_name, self.db_name)
            else:
                # Sử dụng alias đã được patch trong test
                success, message, new_pin_state = db_manager_toggle_pin_bridge(bridge_name, self.db_name)
            
            if success:
                pin_status = "đã ghim" if new_pin_state else "đã bỏ ghim"
                self._log(f">>> [PIN] Cầu '{bridge_name}' {pin_status}.")
            else:
                self._log(f">>> [PIN] Lỗi: {message}")
            
            return success, message, new_pin_state
        
        except Exception as e:
            error_msg = f"Lỗi khi ghim/bỏ ghim cầu '{bridge_name}': {e}"
            self._log(error_msg)
            import traceback
            self._log(traceback.format_exc())
            return False, error_msg, None
    
    def prune_bad_de_bridges(self, all_data):
        """
        Tự động loại bỏ cầu Đề có chuỗi Gãy lâu nhất vượt quá ngưỡng.
        
        Args:
            all_data: Toàn bộ dữ liệu A:I
        
        Returns:
            str: Thông báo kết quả (số cầu bị vô hiệu hóa)
        """
        if not all_data or len(all_data) < 2:
            return "Lỗi: Không có dữ liệu để kiểm tra."
        
        try:
            # Sử dụng alias đã import ở cấp module (global)
            if data_repo_get_all_managed_bridges is None:
                from logic.data_repository import get_all_managed_bridges
                all_bridges = get_all_managed_bridges(self.db_name, only_enabled=False)
            else:
                # Sử dụng alias đã được patch trong test
                all_bridges = data_repo_get_all_managed_bridges(self.db_name, only_enabled=False)
            
            from logic.de_backtester_core import calculate_de_bridge_max_lose_history
            from logic.config_manager import SETTINGS
            
            # Xử lý all_bridges
            if not all_bridges:
                return "Không có cầu nào trong database."
            
            # Lấy ngưỡng từ SETTINGS
            threshold = 20  # Mặc định
            try:
                if SETTINGS and hasattr(SETTINGS, 'DE_MAX_LOSE_THRESHOLD'):
                    threshold = int(SETTINGS.DE_MAX_LOSE_THRESHOLD)
                elif SETTINGS and hasattr(SETTINGS, 'get'):
                    threshold = int(SETTINGS.get('DE_MAX_LOSE_THRESHOLD', 20))
            except (ValueError, TypeError, AttributeError):
                threshold = 20  # Fallback
            
            self._log(f">>> [DE PRUNING] Bắt đầu kiểm tra cầu Đề (Ngưỡng: {threshold} ngày)...")
            
            # Lọc chỉ cầu Đề (DE_POS, DE_DYN)
            de_bridges = []
            for bridge in all_bridges:
                bridge_type = bridge.get("type", "")
                bridge_name = bridge.get("name", "")
                
                # Kiểm tra xem có phải cầu Đề không
                if bridge_type.startswith("DE_") or "DE_" in bridge_name:
                    de_bridges.append(bridge)
            
            if not de_bridges:
                return "Không có cầu Đề nào trong database."
            
            self._log(f">>> [DE PRUNING] Tìm thấy {len(de_bridges)} cầu Đề. Đang kiểm tra...")
            
            # Duyệt qua từng cầu và tính toán Max Lose History
            pruned_count = 0
            error_count = 0
            
            for bridge in de_bridges:
                try:
                    bridge_name = bridge.get("name", "")
                    bridge_id = bridge.get("id")
                    
                    if not bridge_name or not bridge_id:
                        continue
                    
                    # [PHASE 4 - PINNING] Bỏ qua cầu đã ghim
                    is_pinned = bridge.get("is_pinned", 0)
                    if is_pinned:
                        self._log(f"  📌 Bỏ qua cầu '{bridge_name}' (đã ghim).")
                        continue
                    
                    # Tính toán Max Lose History
                    max_lose = calculate_de_bridge_max_lose_history(bridge, all_data)
                    
                    if max_lose == -1:
                        # Lỗi tính toán, bỏ qua
                        error_count += 1
                        continue
                    
                    # Kiểm tra ngưỡng
                    if max_lose > threshold:
                        # Vượt quá ngưỡng: Vô hiệu hóa cầu
                        try:
                            # Lấy description hiện tại
                            current_desc = bridge.get("description", "")
                            
                            # Cập nhật is_enabled = 0 (sử dụng alias từ cấp module)
                            if db_manager_update_managed_bridge is None:
                                from logic.db_manager import update_managed_bridge
                                success, msg = update_managed_bridge(
                                    bridge_id, 
                                    current_desc, 
                                    0,  # is_enabled = 0 (Disabled)
                                    self.db_name
                                )
                            else:
                                # Sử dụng alias đã được patch trong test
                                success, msg = db_manager_update_managed_bridge(
                                    bridge_id, 
                                    current_desc, 
                                    0,  # is_enabled = 0 (Disabled)
                                    self.db_name
                                )
                            
                            if success:
                                pruned_count += 1
                                self._log(f"  ✂️ Đã vô hiệu hóa cầu '{bridge_name}' (Max Lose: {max_lose} > {threshold})")
                            else:
                                self._log(f"  ⚠️ Lỗi khi vô hiệu hóa cầu '{bridge_name}': {msg}")
                        except Exception as e:
                            self._log(f"  ⚠️ Lỗi khi cập nhật cầu '{bridge_name}': {e}")
                            error_count += 1
                    else:
                        # Không vượt ngưỡng: Giữ nguyên
                        pass
                
                except Exception as e:
                    self._log(f"  ⚠️ Lỗi khi xử lý cầu '{bridge.get('name', 'Unknown')}': {e}")
                    error_count += 1
                    continue
            
            # Tổng kết
            result_msg = f"Đã vô hiệu hóa {pruned_count} cầu Đề (Max Lose > {threshold} ngày)"
            if error_count > 0:
                result_msg += f". {error_count} cầu gặp lỗi."
            
            self._log(f">>> [DE PRUNING] Hoàn tất: {result_msg}")
            return result_msg
        
        except Exception as e:
            error_msg = f"Lỗi khi loại bỏ cầu Đề yếu: {e}"
            self._log(error_msg)
            import traceback
            self._log(traceback.format_exc())
            return error_msg