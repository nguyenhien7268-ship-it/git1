# Tên file: services/analysis_service.py
# Service layer: Logic phân tích, backtest và AI

import itertools
import json
import pandas as pd
import traceback

class AnalysisService:
    """Service phân tích và backtest"""
    
    def __init__(self, db_name, logger=None):
        self.db_name = db_name
        self.logger = logger
        
        # Import các hàm backtest từ lottery_service
        try:
            from lottery_service import (
                BACKTEST_15_CAU_K2N_V30_AI_V8,
                BACKTEST_15_CAU_N1_V31_AI_V8,
                BACKTEST_CUSTOM_CAU_V16,
                BACKTEST_MANAGED_BRIDGES_K2N,
                BACKTEST_MANAGED_BRIDGES_N1,
                BACKTEST_MEMORY_BRIDGES,
                getAllLoto_V30,
                run_ai_prediction_for_dashboard,
                run_ai_training_threaded,
                run_and_update_all_bridge_K2N_cache,
                run_and_update_all_bridge_rates,
            )
            self.BACKTEST_15_CAU_K2N = BACKTEST_15_CAU_K2N_V30_AI_V8
            self.BACKTEST_15_CAU_N1 = BACKTEST_15_CAU_N1_V31_AI_V8
            self.BACKTEST_CUSTOM = BACKTEST_CUSTOM_CAU_V16
            self.BACKTEST_MANAGED_K2N = BACKTEST_MANAGED_BRIDGES_K2N
            self.BACKTEST_MANAGED_N1 = BACKTEST_MANAGED_BRIDGES_N1
            self.BACKTEST_MEMORY = BACKTEST_MEMORY_BRIDGES
            self.getAllLoto_V30 = getAllLoto_V30
            self.run_ai_prediction_for_dashboard = run_ai_prediction_for_dashboard
            self.run_ai_training_threaded = run_ai_training_threaded
            self.run_and_update_all_bridge_K2N_cache = run_and_update_all_bridge_K2N_cache
            self.run_and_update_all_bridge_rates = run_and_update_all_bridge_rates
        except ImportError as e:
            self._log(f"Lỗi import backtest functions: {e}")
        
        # Import các hàm dashboard analytics TRỰC TIẾP từ module mới (FIX REGRESSION BUG)
        try:
            # Thử import tuyệt đối trước
            try:
                from logic.analytics.dashboard_scorer import (
                    get_loto_gan_stats,
                    get_loto_stats_last_n_days,
                    get_prediction_consensus,
                    get_high_win_rate_predictions,
                    get_top_memory_bridge_predictions,
                    get_top_scored_pairs,
                )
            except ImportError:
                # Fallback: thử import tương đối
                from logic.dashboard_analytics import (
                    get_loto_gan_stats,
                    get_loto_stats_last_n_days,
                    get_prediction_consensus,
                    get_high_win_rate_predictions,
                    get_top_memory_bridge_predictions,
                    get_top_scored_pairs,
                )
            
            self.get_loto_gan_stats = get_loto_gan_stats
            self.get_loto_stats_last_n_days = get_loto_stats_last_n_days
            self.get_prediction_consensus = get_prediction_consensus
            self.get_high_win_rate_predictions = get_high_win_rate_predictions
            self.get_top_memory_bridge_predictions = get_top_memory_bridge_predictions
            self.get_top_scored_pairs = get_top_scored_pairs
        except ImportError as e:
            self._log(f"LỖI NGHIÊM TRỌNG: Không thể import dashboard analytics functions: {e}")
            # Tạo dummy functions để tránh crash
            def dummy_func(*args, **kwargs):
                return []
            self.get_loto_gan_stats = dummy_func
            self.get_loto_stats_last_n_days = dummy_func
            self.get_prediction_consensus = dummy_func
            self.get_high_win_rate_predictions = dummy_func
            self.get_top_memory_bridge_predictions = dummy_func
            self.get_top_scored_pairs = dummy_func
    
    def _log(self, message):
        """Helper để log messages"""
        if self.logger:
            self.logger.log(message)
    
    def run_backtest(self, all_data_ai, mode, title):
        """
        Chạy backtest dựa trên mode và title.
        
        Args:
            all_data_ai: Dữ liệu A:I
            mode: "N1" hoặc "K2N"
            title: Tiêu đề backtest (để phân loại)
        
        Returns:
            list: Kết quả backtest hoặc None nếu lỗi
        """
        if not all_data_ai:
            return None
        
        ky_bat_dau = 2
        ky_ket_thuc = len(all_data_ai) + (ky_bat_dau - 1)
        self._log(f"Đang chạy backtest trên {len(all_data_ai)} hàng dữ liệu...")
        
        func_to_call = None
        
        if "15" in title:
            func_to_call = self.BACKTEST_15_CAU_N1 if mode == "N1" else self.BACKTEST_15_CAU_K2N
        else:
            if mode == "N1":
                func_to_call = self.BACKTEST_MANAGED_N1
            else:
                func_to_call = lambda a, b, c: self.BACKTEST_MANAGED_K2N(a, b, c, history=True)
        
        if not func_to_call:
            return None
        
        try:
            results = func_to_call(all_data_ai, ky_bat_dau, ky_ket_thuc)
            self._log("Backtest hoàn tất.")
            return results
        except Exception as e:
            self._log(f"Lỗi backtest: {e}")
            return None
    
    def run_custom_backtest(self, all_data_ai, mode, custom_bridge_name):
        """
        Chạy backtest cho cầu tùy chỉnh.
        
        Args:
            all_data_ai: Dữ liệu A:I
            mode: "N1" hoặc "K2N"
            custom_bridge_name: Tên cầu tùy chỉnh
        
        Returns:
            tuple: (results, adjusted_mode, adjusted_title)
        """
        if not all_data_ai:
            return None, mode, None
        
        ky_bat_dau = 2
        ky_ket_thuc = len(all_data_ai) + (ky_bat_dau - 1)
        
        adjusted_mode = mode
        adjusted_title = f"Test Cầu {mode}: {custom_bridge_name}"
        
        if ("Tổng(" in custom_bridge_name or "Hiệu(" in custom_bridge_name) and mode == "K2N":
            self._log("Lỗi: Cầu Bạc Nhớ chỉ hỗ trợ Backtest N1. Đang chạy N1...")
            adjusted_mode = "N1"
            adjusted_title = f"Test Cầu N1: {custom_bridge_name}"
        
        if "Tổng(" in custom_bridge_name or "Hiệu(" in custom_bridge_name:
            self._log("Lỗi: Chức năng test cầu Bạc Nhớ tùy chỉnh chưa được hỗ trợ.")
            return None, adjusted_mode, adjusted_title
        
        try:
            results = self.BACKTEST_CUSTOM(all_data_ai, ky_bat_dau, ky_ket_thuc, custom_bridge_name, adjusted_mode)
            return results, adjusted_mode, adjusted_title
        except Exception as e:
            self._log(f"Lỗi custom backtest: {e}")
            return None, adjusted_mode, adjusted_title
    
    def run_backtest_memory(self, all_data_ai):
        """Chạy backtest cầu Bạc Nhớ"""
        if not all_data_ai:
            return None
        
        ky_bat_dau = 2
        ky_ket_thuc = len(all_data_ai) + (ky_bat_dau - 1)
        
        try:
            results = self.BACKTEST_MEMORY(all_data_ai, ky_bat_dau, ky_ket_thuc)
            return results
        except Exception as e:
            self._log(f"Lỗi backtest memory: {e}")
            return None
    
    def run_backtest_managed_n1(self, all_data_ai):
        """Chạy backtest cầu đã lưu N1"""
        if not all_data_ai:
            return None
        
        ky_bat_dau = 2
        ky_ket_thuc = len(all_data_ai) + (ky_bat_dau - 1)
        
        try:
            results = self.BACKTEST_MANAGED_N1(all_data_ai, ky_bat_dau, ky_ket_thuc)
            return results
        except Exception as e:
            self._log(f"Lỗi backtest managed N1: {e}")
            return None
    
    def run_backtest_managed_k2n(self, all_data_ai):
        """Chạy backtest cầu đã lưu K2N"""
        if not all_data_ai:
            return None
        
        ky_bat_dau = 2
        ky_ket_thuc = len(all_data_ai) + (ky_bat_dau - 1)
        
        try:
            results = self.BACKTEST_MANAGED_K2N(all_data_ai, ky_bat_dau, ky_ket_thuc, history=True)
            return results
        except Exception as e:
            self._log(f"Lỗi backtest managed K2N: {e}")
            return None
    
    def train_ai(self, callback=None):
        """
        Huấn luyện AI model.
        
        Args:
            callback: Hàm callback(success, message)
        
        Returns:
            tuple: (success: bool, message: str)
        """
        def train_callback_wrapper(success, message):
            if callback:
                callback(success, message)
            if success:
                self._log(f">>> Huấn luyện AI HOÀN TẤT: {message}")
            else:
                self._log(f"LỖI huấn luyện AI: {message}")
        
        try:
            success, message = self.run_ai_training_threaded(callback=train_callback_wrapper)
            if not success:
                self._log(f"LỖI KHỞI CHẠY LUỒNG: {message}")
            return success, message
        except Exception as e:
            error_msg = f"Lỗi train AI: {e}"
            self._log(error_msg)
            return False, error_msg
    
    def prepare_dashboard_data(self, all_data_ai, data_limit=None):

        """

        Chuẩn bị dữ liệu cho dashboard (phân tích toàn diện).

        

        Args:

            all_data_ai: Dữ liệu A:I

            data_limit: Giới hạn số kỳ (None = lấy từ Config DATA_LIMIT_DASHBOARD)

        

        Returns:

            dict: Dữ liệu đã phân tích với các keys: next_ky, stats, consensus, etc.

        """

        if not all_data_ai or len(all_data_ai) < 2:

            return None

        

        # Load settings VÀ xác định giới hạn dữ liệu

        data_limit_dashboard = 0 # Default (no limit)

        try:

            from logic.config_manager import SETTINGS

            SETTINGS.load_settings()

            n_days_stats = SETTINGS.STATS_DAYS

            n_days_gan = SETTINGS.GAN_DAYS

            high_win_thresh = SETTINGS.HIGH_WIN_THRESHOLD

            # Lấy giới hạn từ config (hiện đang là 500) nếu không được truyền vào

            data_limit_dashboard = SETTINGS.DATA_LIMIT_DASHBOARD

        except:

            n_days_stats = 7

            n_days_gan = 15

            high_win_thresh = 47.0

        

        # Xác định giới hạn cuối cùng

        final_data_limit = data_limit if data_limit is not None else data_limit_dashboard



        # ⚡ ÁP DỤNG GIỚI HẠN DỮ LIỆU TỪ CONFIG (500 KỲ GẦN NHẤT)

        # Dữ liệu all_data_ai sau bước này là 500 kỳ gần nhất, đảm bảo tính toán K1N chỉ trên 500 kỳ.

        if final_data_limit > 0 and len(all_data_ai) > final_data_limit:

            all_data_ai = all_data_ai[-final_data_limit:]

            self._log(f"⚡ HIỆU NĂNG: Đang phân tích {final_data_limit} kỳ gần nhất.")

        else:

            final_data_limit = len(all_data_ai)

            self._log(f"⚡ Chế độ Full Data: Đang phân tích toàn bộ {final_data_limit} kỳ.")

            

        last_row = all_data_ai[-1]

        

        # Tính next_ky

        try:

            ky_int = int(last_row[0])

            next_ky = f"Kỳ {ky_int + 1}"

        except (ValueError, TypeError):

            next_ky = f"Kỳ {last_row[0]} (Next)"

        

        # Thống kê

        self._log(f"... (1/6) Đang thống kê Loto Về Nhiều ({n_days_stats} ngày)...")

        try:

            stats_n_day = self.get_loto_stats_last_n_days(all_data_ai, n=n_days_stats)

            if stats_n_day is None:

                stats_n_day = []

            self._log(f"... (Stats) Đã tính được {len(stats_n_day)} loto hot")

        except Exception as e:

            self._log(f"Lỗi thống kê Loto: {e}")

            import traceback

            self._log(traceback.format_exc())

            stats_n_day = []

        

        # K2N Cache

        # Chú ý: all_data_ai ở đây đã được cắt lát 500 kỳ

        self._log("... (2/6) Đang chạy hàm Cập nhật K2N Cache...")

        try:

            # run_and_update_all_bridge_K2N_cache sẽ chạy backtest K2N trên 500 kỳ

            pending_k2n_data, _, cache_message = self.run_and_update_all_bridge_K2N_cache(all_data_ai, self.db_name)

            if pending_k2n_data is None:

                pending_k2n_data = {}

            self._log(f"... (Cache K2N) {cache_message}")

        except Exception as e:

            self._log(f"Lỗi Cache K2N: {e}")

            pending_k2n_data = {}

        

        # K1N Rates & Recent Win Count (Phong Độ 10 Kỳ)

        # Yêu cầu của bạn: K1N trên 500 kỳ đã được đảm bảo vì all_data_ai đã cắt lát

        self._log("... (2.5/6) Đang cập nhật Tỷ Lệ và Phong Độ 10 Kỳ từ K1N...")

        try:

            # run_and_update_all_bridge_rates sẽ chạy backtest K1N trên 500 kỳ

            count, rate_message = self.run_and_update_all_bridge_rates(all_data_ai, self.db_name)

            self._log(f"... (K1N Rates) {rate_message}")

        except Exception as e:

            self._log(f"Lỗi cập nhật K1N Rates: {e}")

            import traceback

            self._log(traceback.format_exc())

        

        # Consensus & High Win

        self._log("... (3/6) Đang đọc Consensus và Cầu Tỷ lệ Cao từ cache...")

        try:

            # Truyền last_row để tính toán trực tiếp (ưu tiên hơn cache)

            consensus = self.get_prediction_consensus(last_row=last_row, db_name=self.db_name)

            if consensus is None:

                consensus = []

            self._log(f"... (Consensus) Đã đọc được {len(consensus)} cặp có vote")

        except Exception as e:

            self._log(f"Lỗi đọc Consensus: {e}")

            import traceback

            self._log(traceback.format_exc())

            consensus = []

        

        try:

            high_win = self.get_high_win_rate_predictions(threshold=high_win_thresh)

            if high_win is None:

                high_win = []

        except Exception as e:

            self._log(f"Lỗi đọc High Win: {e}")

            high_win = []

        

        # Gan stats

        self._log(f"... (4/6) Đang tìm Lô Gan (trên {n_days_gan} kỳ)...")

        try:

            gan_stats = self.get_loto_gan_stats(all_data_ai, n_days=n_days_gan)

            if gan_stats is None:

                gan_stats = []

        except Exception as e:

            self._log(f"Lỗi tìm Lô Gan: {e}")

            gan_stats = []

        

        # AI predictions

        self._log("... (5/6) Đang chạy dự đoán AI...")

        try:

            ai_result = self.run_ai_prediction_for_dashboard()

            if ai_result and isinstance(ai_result, tuple) and len(ai_result) >= 2:

                ai_predictions, ai_message = ai_result[0], ai_result[1]

            else:

                ai_predictions, ai_message = None, "Không có dự đoán AI"

            if ai_predictions is None:

                ai_predictions = []

            self._log(f"... (AI) {ai_message}")

        except Exception as e:

            self._log(f"Lỗi dự đoán AI: {e}")

            ai_predictions = []

        

        # Top memory bridges

        try:

            top_memory_bridges = self.get_top_memory_bridge_predictions(all_data_ai, last_row, top_n=5)

            if top_memory_bridges is None:

                top_memory_bridges = []

        except Exception as e:

            self._log(f"Lỗi tính Cầu Bạc Nhớ: {e}")

            top_memory_bridges = []

        

        # Top scored pairs

        try:

            self._log(f"... (Top Scores) Đang tính điểm với: stats={len(stats_n_day)}, consensus={len(consensus)}, high_win={len(high_win)}, pending_k2n={len(pending_k2n_data)}, gan={len(gan_stats)}, memory={len(top_memory_bridges)}, ai={len(ai_predictions)}")

            top_scores = self.get_top_scored_pairs(

                stats_n_day, consensus, high_win, pending_k2n_data,

                gan_stats, top_memory_bridges, ai_predictions

            )

            if top_scores is None:

                top_scores = []

            self._log(f"... (Top Scores) Đã tính được {len(top_scores)} cặp có điểm")

        except Exception as e:

            self._log(f"Lỗi tính Điểm Tổng Lực: {e}")

            import traceback

            self._log(traceback.format_exc())

            top_scores = []

        

        # Prepare DE dashboard data

        df_de = None

        try:

            cols = ["NB", "NGAY", "GDB", "G1", "G2", "G3", "G4", "G5", "G6", "G7"]

            data_for_df = [r[:10] for r in all_data_ai if r and len(r) >= 10]

            df_de = pd.DataFrame(data_for_df, columns=cols)

        except Exception as e:

            self._log(f"Cảnh báo: Lỗi tạo DataFrame cho DE: {e}")

        

        return {

            "next_ky": next_ky,

            "stats_n_day": stats_n_day,

            "n_days_stats": n_days_stats,

            "consensus": consensus,

            "high_win": high_win,

            "pending_k2n_data": pending_k2n_data,

            "gan_stats": gan_stats,

            "top_scores": top_scores,

            "top_memory_bridges": top_memory_bridges,

            "ai_predictions": ai_predictions,

            "df_de": df_de,

        }
    
    def train_ai(self, callback=None):
        """
        Huấn luyện AI model.
        
        Args:
            callback: Hàm callback(success, message)
        
        Returns:
            tuple: (success: bool, message: str)
        """
        def train_callback_wrapper(success, message):
            if callback:
                callback(success, message)
            if success:
                self._log(f">>> Huấn luyện AI HOÀN TẤT: {message}")
            else:
                self._log(f"LỖI huấn luyện AI: {message}")
        
        try:
            success, message = self.run_ai_training_threaded(callback=train_callback_wrapper)
            if not success:
                self._log(f"LỖI KHỞI CHẠY LUỒNG: {message}")
            return success, message
        except Exception as e:
            error_msg = f"Lỗi train AI: {e}"
            self._log(error_msg)
            return False, error_msg
    
    def run_parameter_tuning(self, all_data_ai, param_key, val_from, val_to, val_step, log_callback):
        """
        Chạy parameter tuning cho một tham số cụ thể.
        
        Args:
            all_data_ai: Dữ liệu A:I
            param_key: Tên tham số cần tune
            val_from, val_to, val_step: Phạm vi và bước nhảy
            log_callback: Hàm callback để log (nhận message string)
        
        Returns:
            None (kết quả được log qua callback)
        """
        try:
            from logic.config_manager import SETTINGS
            from logic.data_repository import get_all_managed_bridges
            from lottery_service import TIM_CAU_TOT_NHAT_V16, TIM_CAU_BAC_NHO_TOT_NHAT
            
            if not all_data_ai or len(all_data_ai) < 2:
                log_callback("LỖI: Không thể tải dữ liệu A:I.")
                return
            
            last_row = all_data_ai[-1]
            log_callback(f"...Tải thành công {len(all_data_ai)} kỳ.")
            
            def float_range(start, stop, step):
                if step == 0:
                    yield start
                    return
                n = start
                while n < (stop + (step * 0.5)):
                    yield n
                    n += step
            
            def test_gan_days(p_key, v_from, v_to, v_step):
                log_callback(f"--- Bắt đầu kiểm thử: {p_key} ---")
                for i in float_range(v_from, v_to, v_step):
                    n = int(i)
                    if n <= 0:
                        continue
                    gan_stats = self.get_loto_gan_stats(all_data_ai, n_days=n)
                    log_callback(f"Kiểm thử {p_key} = {n}: Tìm thấy {len(gan_stats)} loto gan.")
                log_callback(f"--- Hoàn tất kiểm thử {p_key} ---")
            
            def test_high_win_threshold(p_key, v_from, v_to, v_step):
                log_callback(f"--- Bắt đầu kiểm thử: {p_key} ---")
                log_callback("... (Chạy Cache K2N một lần để lấy dữ liệu mới nhất)...")
                self.run_and_update_all_bridge_K2N_cache(all_data_ai, self.db_name)
                log_callback("... (Cache K2N hoàn tất. Bắt đầu lặp)...")
                for i in float_range(v_from, v_to, v_step):
                    high_win_bridges = self.get_high_win_rate_predictions(threshold=i)
                    log_callback(f"Kiểm thử {p_key} >= {i:.1f}%: Tìm thấy {len(high_win_bridges)} cầu đạt chuẩn.")
                log_callback(f"--- Hoàn tất kiểm thử {p_key} ---")
            
            def test_auto_add_rate(p_key, v_from, v_to, v_step):
                log_callback(f"--- Bắt đầu kiểm thử: {p_key} ---")
                log_callback("... (Chạy Dò Cầu V17... Rất nặng, vui lòng chờ)...")
                ky_bat_dau = 2
                ky_ket_thuc = len(all_data_ai) + (ky_bat_dau - 1)
                results_v17 = TIM_CAU_TOT_NHAT_V16(all_data_ai, ky_bat_dau, ky_ket_thuc, self.db_name)
                log_callback("... (Chạy Dò Cầu Bạc Nhớ...)...")
                results_memory = TIM_CAU_BAC_NHO_TOT_NHAT(all_data_ai, ky_bat_dau, ky_ket_thuc)
                combined_results = []
                if results_v17 and len(results_v17) > 1:
                    combined_results.extend([row for row in results_v17[1:] if "---" not in str(row[0])])
                if results_memory and len(results_memory) > 1:
                    combined_results.extend([row for row in results_memory[1:] if "---" not in str(row[0])])
                if not combined_results:
                    log_callback("LỖI: Không dò được cầu nào.")
                    return
                log_callback(f"... (Dò cầu hoàn tất. Tổng cộng {len(combined_results)} cầu. Bắt đầu lặp)...")
                for i in float_range(v_from, v_to, v_step):
                    count = 0
                    for row in combined_results:
                        try:
                            rate = float(str(row[3]).replace("%", ""))
                            if rate >= i:
                                count += 1
                        except (ValueError, IndexError):
                            continue
                    log_callback(f"Kiểm thử {p_key} >= {i:.1f}%: Sẽ thêm/cập nhật {count} cầu.")
                log_callback(f"--- Hoàn tất kiểm thử {p_key} ---")
            
            def test_auto_prune_rate(p_key, v_from, v_to, v_step):
                log_callback(f"--- Bắt đầu kiểm thử: {p_key} ---")
                log_callback("... (Chạy Cache K2N một lần để lấy dữ liệu mới nhất)...")
                self.run_and_update_all_bridge_K2N_cache(all_data_ai, self.db_name)
                log_callback("... (Cache K2N hoàn tất. Bắt đầu lặp)...")
                enabled_bridges = get_all_managed_bridges(self.db_name, only_enabled=True)
                if not enabled_bridges:
                    log_callback("LỖI: Không có cầu nào đang Bật để kiểm thử.")
                    return
                for i in float_range(v_from, v_to, v_step):
                    count = 0
                    for bridge in enabled_bridges:
                        try:
                            rate_str = str(bridge.get("win_rate_text", "100%")).replace("%", "")
                            if not rate_str or rate_str == "N/A":
                                continue
                            rate = float(rate_str)
                            if rate < i:
                                count += 1
                        except ValueError:
                            continue
                    log_callback(f"Kiểm thử {p_key} < {i:.1f}%: Sẽ TẮT {count} cầu.")
                log_callback(f"--- Hoàn tất kiểm thử {p_key} ---")
            
            def test_k2n_risk_logic(p_key, v_from, v_to, v_step):
                log_callback(f"--- Bắt đầu kiểm thử: {p_key} ---")
                log_callback("... (Chạy Cache K2N một lần để lấy dữ liệu nền)...")
                pending_k2n, _, _ = self.run_and_update_all_bridge_K2N_cache(all_data_ai, self.db_name)
                stats_n_day = self.get_loto_stats_last_n_days(all_data_ai)
                # Truyền last_row nếu có để tính toán trực tiếp
                test_last_row = all_data_ai[-1] if all_data_ai else None
                consensus = self.get_prediction_consensus(last_row=test_last_row, db_name=self.db_name)
                high_win = self.get_high_win_rate_predictions()
                gan_stats = self.get_loto_gan_stats(all_data_ai)
                top_memory = self.get_top_memory_bridge_predictions(all_data_ai, last_row)
                ai_preds, _ = self.run_ai_prediction_for_dashboard()
                log_callback("... (Dữ liệu nền hoàn tất. Bắt đầu lặp)...")
                original_value = SETTINGS.get_all_settings().get(p_key)
                for i in float_range(v_from, v_to, v_step):
                    val = i
                    if p_key == "K2N_RISK_START_THRESHOLD":
                        val = int(i)
                    setattr(SETTINGS, p_key, val)
                    top_scores = self.get_top_scored_pairs(stats_n_day, consensus, high_win, pending_k2n, gan_stats, top_memory, ai_preds)
                    if not top_scores:
                        log_callback(f"Kiểm thử {p_key} = {val}: Không có cặp nào đạt điểm.")
                    else:
                        top_score_item = top_scores[0]
                        log_callback(f"Kiểm thử {p_key} = {val}: Top 1 là {top_score_item['pair']} (Điểm: {top_score_item['score']})")
                if original_value is not None:
                    setattr(SETTINGS, p_key, original_value)
                log_callback(f"--- Hoàn tất kiểm thử {p_key} ---")
            
            # Dispatch
            if param_key == "GAN_DAYS":
                test_gan_days(param_key, val_from, val_to, val_step)
            elif param_key == "HIGH_WIN_THRESHOLD":
                test_high_win_threshold(param_key, val_from, val_to, val_step)
            elif param_key == "AUTO_ADD_MIN_RATE":
                test_auto_add_rate(param_key, val_from, val_to, val_step)
            elif param_key == "AUTO_PRUNE_MIN_RATE":
                test_auto_prune_rate(param_key, val_from, val_to, val_step)
            elif param_key in ["K2N_RISK_START_THRESHOLD", "K2N_RISK_PENALTY_PER_FRAME"]:
                test_k2n_risk_logic(param_key, val_from, val_to, val_step)
            else:
                log_callback(f"Lỗi: Chưa định nghĩa logic kiểm thử cho {param_key}")
        except Exception as e:
            log_callback(f"LỖI: {e}")
            import traceback
            log_callback(traceback.format_exc())
    
    def run_strategy_optimization(self, all_data_ai, days_to_test, param_ranges, log_callback, update_results_callback):
        """
        Chạy tối ưu hóa chiến lược (strategy optimization).
        
        Args:
            all_data_ai: Dữ liệu A:I
            days_to_test: Số ngày để test
            param_ranges: Dict các tham số cần optimize {param: (from, to, step)}
            log_callback: Hàm callback để log (nhận message string)
            update_results_callback: Hàm callback để update kết quả (nhận results_list)
        
        Returns:
            None (kết quả được gọi qua callbacks)
        """
        try:
            from logic.config_manager import SETTINGS
            from logic.dashboard_analytics import prepare_daily_features, calculate_score_from_features
            
            if not all_data_ai or len(all_data_ai) < days_to_test + 50:
                log_callback(f"LỖI: Cần ít nhất {days_to_test + 50} kỳ dữ liệu để kiểm thử.")
                return
            
            log_callback(f"...Tải dữ liệu thành công ({len(all_data_ai)} kỳ).")
            
            # Data limit
            try:
                limit = getattr(SETTINGS, "DATA_LIMIT_RESEARCH", 0)
            except:
                limit = 0
            if limit > 0 and len(all_data_ai) > limit:
                data_processing = all_data_ai[-limit:]
                log_callback(f"⚡ HIỆU NĂNG: Tối ưu hóa trên {limit} kỳ gần nhất.")
            else:
                data_processing = all_data_ai
                log_callback(f"⚡ Chế độ Full Data: Tối ưu hóa trên toàn bộ {len(all_data_ai)} kỳ.")
            
            def float_range(start, stop, step):
                if step == 0:
                    yield start
                    return
                n = start
                while n < (stop + (step * 0.5)):
                    yield n
                    n += step
            
            def generate_combinations(param_ranges, original_settings):
                param_lists = []
                config_keys = list(param_ranges.keys())
                static_keys = [k for k in original_settings.keys() if k not in config_keys]
                for key in config_keys:
                    v_from, v_to, v_step = param_ranges[key]
                    if isinstance(original_settings[key], int):
                        param_lists.append([(key, int(i)) for i in float_range(v_from, v_to, v_step) if i >= 0])
                    else:
                        param_lists.append([(key, round(i, 2)) for i in float_range(v_from, v_to, v_step) if i >= 0])
                if not param_lists:
                    return []
                combinations = []
                for combo in itertools.product(*param_lists):
                    temp_config = {}
                    for static_key in static_keys:
                        temp_config[static_key] = original_settings[static_key]
                    for key, value in combo:
                        temp_config[key] = value
                    combinations.append(temp_config)
                return combinations
            
            original_settings = SETTINGS.get_all_settings()
            combinations = generate_combinations(param_ranges, original_settings)
            total_combos = len(combinations)
            if total_combos == 0:
                log_callback("Lỗi: Không tạo được tổ hợp kiểm thử.")
                return
            
            log_callback(f"Đã tạo {total_combos} tổ hợp. Bắt đầu chuẩn bị features cache...")
            
            # Precompute features
            cached_features = []
            offset = len(data_processing) - days_to_test
            for i in range(days_to_test):
                day_index = offset + i
                log_callback(f"Đang chuẩn bị dữ liệu ngày {day_index + 1 - offset}/{days_to_test} ...")
                try:
                    features = prepare_daily_features(data_processing, day_index)
                    cached_features.append(features)
                except Exception as e:
                    log_callback(f"Lỗi khi prepare features ngày {i+1}: {e}")
                    cached_features.append(None)
            
            results_list = []
            log_callback(f"Chuẩn bị xong features. Bắt đầu Loop tối ưu ({total_combos} tổ hợp)...")
            for ci, config in enumerate(combinations):
                log_callback(f"--- Đang kiểm thử [{ci + 1}/{total_combos}]: {config} ---")
                total_hits = 0
                days_tested = 0
                for fidx, features in enumerate(cached_features):
                    if not features:
                        continue
                    try:
                        top_scores = calculate_score_from_features(features, config)
                    except Exception as e:
                        log_callback(f"Lỗi tính score ngày {fidx+1}: {e}")
                        continue
                    days_tested += 1
                    if not top_scores:
                        continue
                    top1 = top_scores[0]
                    last_row = features['recent_data'][-1] if 'recent_data' in features else None
                    if last_row:
                        actual_lotos = set(self.getAllLoto_V30(last_row))
                        loto1, loto2 = top1['pair'].split('-')
                        if loto1 in actual_lotos or loto2 in actual_lotos:
                            total_hits += 1
                rate = total_hits / days_tested if days_tested > 0 else 0
                hits_str = f"{total_hits}/{days_tested}"
                config_str_json = json.dumps(config)
                params_str_display = ", ".join([f"{key}: {value}" for key, value in config.items() if key in param_ranges])
                results_list.append((rate, hits_str, params_str_display, config_str_json))
                log_callback(f"-> Kết quả: {hits_str} ({rate * 100:.1f}%)")
            
            log_callback("Đang sắp xếp kết quả...")
            results_list.sort(key=lambda x: x[0], reverse=True)
            if update_results_callback:
                update_results_callback(results_list)
            log_callback("--- HOÀN TẤT TỐI ƯU HÓA ---")
        except Exception as e:
            log_callback(f"LỖI: {e}")
            import traceback
            log_callback(traceback.format_exc())
    
    def run_lo_backtest_30_days(self, bridge_name, all_data_ai):
        """
        Chạy backtest 30 ngày cho một cầu Lô cụ thể.
        
        Args:
            bridge_name: Tên cầu
            all_data_ai: Toàn bộ dữ liệu A:I
        
        Returns:
            list: List các dict với kết quả backtest hoặc None nếu lỗi
        """
        if not all_data_ai:
            return None
        
        try:
            from logic.data_repository import get_bridge_by_name
            from logic.backtester import run_backtest_lo_30_days
            
            # Lấy bridge config từ DB
            bridge_config = get_bridge_by_name(bridge_name, self.db_name)
            if not bridge_config:
                self._log(f"Không tìm thấy cầu '{bridge_name}' trong database.")
                return None
            
            # Chạy backtest
            results = run_backtest_lo_30_days(bridge_config, all_data_ai)
            return results
        except Exception as e:
            self._log(f"Lỗi chạy backtest 30 ngày: {e}")
            import traceback
            self._log(traceback.format_exc())
            return None
    
    def run_de_backtest_30_days(self, bridge_name, all_data_ai):
        """
        Chạy backtest 30 ngày cho một cầu Đề cụ thể.
        
        Args:
            bridge_name: Tên cầu
            all_data_ai: Toàn bộ dữ liệu A:I
        
        Returns:
            list: List các dict với kết quả backtest hoặc None nếu lỗi
        """
        print(f"[DEBUG] run_de_backtest_30_days BẮT ĐẦU: bridge_name='{bridge_name}', data_length={len(all_data_ai) if all_data_ai else 0}")
        
        if not all_data_ai:
            print(f"[ERROR] all_data_ai rỗng!")
            return None
        
        try:
            from services.bridge_service import BridgeService
            from logic.de_backtester_core import run_de_bridge_historical_test
            
            # Bước 1: Lấy Config từ BridgeService
            print(f"[DEBUG] Đang lấy bridge config từ BridgeService...")
            bridge_service = BridgeService(self.db_name, logger=self.logger)
            bridge_config = bridge_service.get_de_bridge_config_by_name(bridge_name)
            
            print(f"[DEBUG] Bridge config: {bridge_config}")
            
            # Bước 2: Phân loại & Chạy Logic
            if bridge_config:
                # Tìm thấy cấu hình cầu DB (DE_POS hoặc DE_DYNAMIC_K đã lưu)
                # Dùng full bridge object từ DB (có pos1_idx, pos2_idx) làm input
                log_msg = f"Đã tìm thấy cấu hình cầu '{bridge_name}' trong DB. Sử dụng config từ DB."
                print(f"[DEBUG] {log_msg}")
                self._log(log_msg)
                print(f"[DEBUG] Đang gọi run_de_bridge_historical_test với config từ DB...")
                results = run_de_bridge_historical_test(bridge_config, all_data_ai, days=30)
                print(f"[DEBUG] run_de_bridge_historical_test trả về {len(results) if results else 0} kết quả.")
                return results
            else:
                # Không tìm thấy trong DB (DE_DYN chưa lưu hoặc cầu mới)
                # Fallback: Tạo bridge config từ tên cầu
                log_msg = f"Cầu '{bridge_name}' chưa có trong DB. Sử dụng logic parse từ tên cầu."
                print(f"[DEBUG] {log_msg}")
                self._log(log_msg)
                fallback_config = {
                    "name": bridge_name,
                    "type": "DE_DYNAMIC_K" if "DE_DYN_" in bridge_name else "DE_POS_SUM" if "DE_POS_" in bridge_name else "UNKNOWN"
                }
                print(f"[DEBUG] Fallback config: {fallback_config}")
                print(f"[DEBUG] Đang gọi run_de_bridge_historical_test với fallback config...")
                results = run_de_bridge_historical_test(fallback_config, all_data_ai, days=30)
                print(f"[DEBUG] run_de_bridge_historical_test trả về {len(results) if results else 0} kết quả.")
                return results
        except Exception as e:
            error_msg = f"Lỗi chạy backtest Đề 30 ngày: {e}"
            print(f"[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            self._log(error_msg)
            self._log(traceback.format_exc())
            return None

    def calculate_lo_scoring_engine(self, all_data_ai):
        """
        [NEW V3.8 - ROBUST] Chạy Scoring Engine cho Lô.
        Sử dụng kết nối SQL trực tiếp để tránh lỗi import vòng (Circular Import).
        """
        try:
            # Import logic tính điểm
            from logic.lo_analytics import calculate_lo_scores
            import sqlite3
            
            self._log("--- Bắt đầu Scoring Engine Lô (Direct SQL Mode) ---")

            # 1. Lấy dữ liệu Cầu (Managed Bridges) - QUAN TRỌNG: Dùng SQL trực tiếp
            bridges = []
            try:
                # Kết nối trực tiếp DB để lấy cầu active
                conn = sqlite3.connect(self.db_name)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM ManagedBridges WHERE is_enabled = 1")
                rows = cursor.fetchall()
                # Convert row object to dict
                bridges = [dict(row) for row in rows]
                conn.close()
                self._log(f"-> [SQL] Đã tải {len(bridges)} cầu hoạt động.")
            except Exception as e:
                self._log(f"⚠️ Lỗi kết nối DB lấy cầu: {e}")
                bridges = []
            
            # 2. Lấy dữ liệu Thống kê (Gan & Tần suất)
            gan_stats = self.get_loto_gan_stats(all_data_ai, n_days=10) or []
            freq_stats = self.get_loto_stats_last_n_days(all_data_ai, n=30) or []
            
            # 3. Lấy Bạc nhớ
            last_row = all_data_ai[-1] if all_data_ai else None
            top_memory = self.get_top_memory_bridge_predictions(all_data_ai, last_row, top_n=5) or []
            
            # 4. Tính điểm
            scores = calculate_lo_scores(bridges, gan_stats, freq_stats, top_memory)
            self._log(f"-> Tính điểm xong. Top 1: {scores[0] if scores else 'None'}")
            
            return scores, gan_stats
            
        except Exception as e:
            self._log(f"❌ LỖI CRITICAL Scoring Engine: {e}")
            import traceback
            self._log(traceback.format_exc())
            return [], []
