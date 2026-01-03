# Tên file: services/analysis_service.py
# Service layer: Logic phân tích, backtest và AI

import itertools
import json
import pandas as pd
import traceback

# Phase 3: Meta-Learner Data Collection
try:
    from logic.phase3_data_collector import log_prediction
    PHASE3_ENABLED =True
except ImportError:
    PHASE3_ENABLED = False
    def log_prediction(*args, **kwargs):
        pass  # Fallback if Phase 3 not available

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
            self._log("DEBUG: Loaded NEW analytics (logic.analytics.dashboard_scorer)")
        except ImportError as e1:
            self._log(f"DEBUG: Failed to load NEW analytics: {e1}")
            # Fallback: thử import tương đối
            try:
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
                self._log("DEBUG: Loaded LEGACY analytics (logic.dashboard_analytics)")
            except ImportError:
                raise ImportError(f"Cannot load NEW or LEGACY analytics. New error: {e1}")
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
    
    def prepare_dashboard_data(self, all_data_ai, data_limit=None, lo_mode=True, de_mode=True):
        """
        Chuẩn bị dữ liệu dashboard (phân tích toàn diện) theo chế độ (On-Demand).

        Args:
            all_data_ai: Dữ liệu A:I
            data_limit: Giới hạn số kỳ
            lo_mode: Có phân tích Lô hay không
            de_mode: Có phân tích Đề hay không

        Returns:
            dict: Dữ liệu đã phân tích
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
            data_limit_dashboard = SETTINGS.DATA_LIMIT_DASHBOARD
        except:
            n_days_stats = 7
            n_days_gan = 15
            high_win_thresh = 47.0

        # Xác định giới hạn cuối cùng
        final_data_limit = data_limit if data_limit is not None else data_limit_dashboard

        # ⚡ ÁP DỤNG GIỚI HẠN DỮ LIỆU TỪ CONFIG
        if final_data_limit > 0 and len(all_data_ai) > final_data_limit:
            all_data_ai = all_data_ai[-final_data_limit:]
            self._log(f"⚡ HIỆU NĂNG: Đang phân tích {final_data_limit} kỳ gần nhất.")
        else:
            final_data_limit = len(all_data_ai)
            self._log(f"⚡ Chế độ Full Data: Đang phân tích toàn bộ {final_data_limit} kỳ.")
            
        last_row = all_data_ai[-1]
        
        # Tính next_ky (Chung)
        try:
            ky_int = int(last_row[0])
            next_ky = f"Kỳ {ky_int + 1}"
        except (ValueError, TypeError):
            next_ky = f"Kỳ {last_row[0]} (Next)"
        
        # Khởi tạo result dict cơ bản
        result = {
        "next_ky": next_ky,
        "n_days_stats": n_days_stats,
        "stats_n_day": [],
        "consensus": [],
        "high_win": [],
        "pending_k2n_data": {},
        "gan_stats": [],
        "top_scores": [],
        "top_memory_bridges": [],
        "ai_predictions": [],
        "df_de": None
        }

        # =======================================================================
        # 🟢 PHÂN TÍCH LÔ (Nặng nhất - Tách biệt)
        # =======================================================================
        if lo_mode:
            self._log("⚡ [LÔ] Bắt đầu tính toán phân hệ Lô...")

            # 1. Thống kê
            self._log(f"... (1/6) Đang thống kê Loto Về Nhiều ({n_days_stats} ngày)...")
            try:
                stats_n_day = self.get_loto_stats_last_n_days(all_data_ai, n=n_days_stats) or []
                self._log(f"... (Stats) Đã tính được {len(stats_n_day)} loto hot")
                result["stats_n_day"] = stats_n_day
            except Exception as e:
                self._log(f"Lỗi thống kê Loto: {e}")
                result["stats_n_day"] = []

            # 2. K2N Cache
            self._log("... (2/6) Đang chạy hàm Cập nhật K2N Cache...")
            try:
                pending_k2n_data, _, cache_message = self.run_and_update_all_bridge_K2N_cache(all_data_ai, self.db_name)
                result["pending_k2n_data"] = pending_k2n_data or {}
                self._log(f"... (Cache K2N) {cache_message}")
            except Exception as e:
                self._log(f"Lỗi Cache K2N: {e}")
                result["pending_k2n_data"] = {}

            # 3. K1N Rates
            self._log("... (2.5/6) Đang cập nhật Tỷ Lệ và Phong Độ 10 Kỳ từ K1N...")
            try:
                count, rate_message = self.run_and_update_all_bridge_rates(all_data_ai, self.db_name)
                self._log(f"... (K1N Rates) {rate_message}")
            except Exception as e:
                self._log(f"Lỗi cập nhật K1N Rates: {e}")

            # 4. Consensus & High Win
            self._log("... (3/6) Đang đọc Consensus và Cầu Tỷ lệ Cao từ cache...")
            try:
                consensus = self.get_prediction_consensus(last_row=last_row, db_name=self.db_name) or []
                result["consensus"] = consensus
                self._log(f"... (Consensus) Đã đọc được {len(consensus)} cặp có vote")
            except Exception: 
                result["consensus"] = []
            
            try:
                high_win = self.get_high_win_rate_predictions(threshold=high_win_thresh) or []
                result["high_win"] = high_win
            except Exception: 
                result["high_win"] = []

            # 5. Gan stats
            self._log(f"... (4/6) Đang tìm Lô Gan (trên {n_days_gan} kỳ)...")
            try:
                gan_stats = self.get_loto_gan_stats(all_data_ai, n_days=n_days_gan) or []
                result["gan_stats"] = gan_stats
            except Exception: 
                result["gan_stats"] = []

            # 6. AI predictions
            self._log("... (5/6) Đang chạy dự đoán AI...")
            try:
                ai_res = self.run_ai_prediction_for_dashboard()
                if ai_res and isinstance(ai_res, tuple) and len(ai_res) >= 2:
                    result["ai_predictions"] = ai_res[0]
                    self._log(f"... (AI) {ai_res[1]}")
                else:
                    result["ai_predictions"] = []
            except Exception as e:
                self._log(f"Lỗi dự đoán AI: {e}")
                result["ai_predictions"] = []

            # 7. Top memory & Top Score
            try:
                top_memory_bridges = self.get_top_memory_bridge_predictions(all_data_ai, last_row, top_n=5) or []
                result["top_memory_bridges"] = top_memory_bridges

                self._log("... (6/6) Tính điểm tổng lực...")
                top_scores = self.get_top_scored_pairs(
                    result.get("stats_n_day"), result.get("consensus"), result.get("high_win"), 
                    result.get("pending_k2n_data"), result.get("gan_stats"), top_memory_bridges, 
                    result.get("ai_predictions")
                )
                result["top_scores"] = top_scores or []
                self._log(f"... (Top Scores) Đã tính được {len(result['top_scores'])} cặp có điểm")
                
                # [PHASE 3] Log predictions for Meta-Learner training
                if PHASE3_ENABLED and top_scores:
                    try:
                        ky_for_logging = str(last_row[0]) if last_row else "unknown"
                        logged_count = 0
                        for score_item in top_scores[:20]:  # Log top 20 predictions
                            pair = score_item.get('pair', '')
                            if '-' in pair:
                                loto1, loto2 = pair.split('-')
                                for loto in [loto1, loto2]:
                                    log_prediction(
                                        ky=ky_for_logging,
                                        loto=loto,
                                        ai_probability=score_item.get('ai_prob', 0.0),
                                        manual_score=score_item.get('score', 0.0),
                                        confidence=score_item.get('confidence', 0),
                                        vote_count=score_item.get('vote_count', 0),
                                        recent_form_score=score_item.get('form_bonus', 0.0)
                                    )
                                    logged_count += 1
                        self._log(f"[Phase 3] Logged {logged_count} predictions for period {ky_for_logging}")
                    except Exception as e_phase3:
                        self._log(f"Warning: Phase 3 logging failed: {e_phase3}")
            except Exception as e:
                self._log(f"Lỗi tính Điểm Tổng Lực: {e}")
                result["top_scores"] = []

        else:
            self._log("⏩ [LÔ] Bỏ qua phân tích Lô.")

        # =======================================================================
        # 🔴 PHÂN TÍCH ĐỀ (Tách biệt)
        # =======================================================================
        if de_mode:
            self._log("⚡ [ĐỀ] Bắt đầu tính toán phân hệ Đề...")
            try:
                # 0. Create DataFrame (Existing)
                cols = ["NB", "NGAY", "GDB", "G1", "G2", "G3", "G4", "G5", "G6", "G7"]
                data_for_df = [r[:10] for r in all_data_ai if r and len(r) >= 10]
                result["df_de"] = pd.DataFrame(data_for_df, columns=cols)
                
                # --- NEW DE ANALYSIS LOGIC ---
                from logic.de_analytics import (
                    analyze_market_trends,
                    calculate_number_scores, 
                    run_intersection_matrix_analysis,
                    build_dan65_with_bo_priority
                )
                from logic.data_repository import get_managed_bridges_with_prediction
                
                # 1. Market Trends (History)
                self._log("... (1/4) Phân tích xu hướng thị trường (Market Trends)...")
                market_stats = analyze_market_trends(all_data_ai, n_days=30)
                # Map keys to UI expected format if needed, mostly used for scoring
                
                # 2. Scanner / Bridges
                self._log("... (2/4) Quét cầu Đề và tính điểm...")
                # Fetch De bridges (enabled only)
                de_bridges = get_managed_bridges_with_prediction(self.db_name, current_data=all_data_ai, only_enabled=True)
                de_bridges = [b for b in de_bridges if str(b.get("type", "")).upper().startswith("DE")]
                
                # Calculate Scores using V4 Anti-Inflation logic
                ranked_numbers = calculate_number_scores(de_bridges, market_stats=market_stats)
                # ranked_numbers is list of (num_str, score, info)
                
                # Convert to UI format (list of dicts) if needed, OR store as is for specialized widgets
                # The UI expects `de_evaluate` usually.
                result["de_evaluate"] = ranked_numbers
                
                # 3. Matrix Analysis
                self._log("... (3/4) Phân tích Ma Trận...")
                matrix_res = run_intersection_matrix_analysis(result["df_de"])
                result["de_matrix"] = matrix_res # ranked, cham_thong, etc.
                
                # 4. Chot So & Dan 65
                self._log("... (4/4) Chốt số VIP & Dàn 65...")
                # Extract Top Matrix for VIP
                top_matrix = [x["so"] for x in matrix_res.get("ranked", [])[:10]]
                
                sorted_dan, inclusions, excluded = build_dan65_with_bo_priority(
                    all_scores=ranked_numbers,
                    freq_bo=market_stats.get("freq_bo", {}),
                    gan_bo=market_stats.get("gan_bo", {}),
                    vip_numbers=top_matrix[:10], # Force include top 10 Matrix
                    focus_numbers=[],
                    top_sets_count=5
                )
                
                result["de_chot_so_vip"] = {
                    "top_matrix": top_matrix,
                    "generated_dan": sorted_dan,
                    "inclusions": inclusions
                }
                
                # 5. Touch Combinations
                from logic.de_analytics import calculate_top_touch_combinations
                touch_combos = calculate_top_touch_combinations(all_data_ai, num_touches=4, days=15, market_stats=market_stats)
                
                # --- UI COMPATIBILITY MAPPING ---
                # Map new keys to legacy keys expected by PyQtDeDashboardTab
                result["scores"] = ranked_numbers  # Alias for de_evaluate
                result["matrix_res"] = matrix_res  # Alias for de_matrix
                result["stats"] = market_stats  # Market trends
                result["bridges"] = de_bridges  # De bridges list
                result["list_data"] = data_for_df  # Raw data rows
                result["touch_combinations"] = touch_combos  # Touch analysis
                
                self._log(f"[ĐỀ] Hoàn tất. Top 1: {ranked_numbers[0] if ranked_numbers else 'None'}")
                
            except Exception as e:
                self._log(f"Lỗi Phân Tích Đề: {e}")
                traceback.print_exc()
                result["df_de"] = None
        else:
            self._log("⏩ [ĐỀ] Bỏ qua phân tích Đề.")
            
        return result

        
    
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
            
            # Lấy bridge config từ DB bằng hàm mới (đảm bảo có pos1_idx)
            bridge_config = get_bridge_by_name(bridge_name, self.db_name)
            if not bridge_config:
                self._log(f"Không tìm thấy cầu '{bridge_name}' trong database.")
                return None
            
            # [DEBUG] Kiểm tra xem config có vị trí không để log cảnh báo
            if bridge_config.get('pos1_idx') is None and "LO_STL_FIXED" not in bridge_name:
                 self._log(f"Cảnh báo: Cầu '{bridge_name}' thiếu thông tin vị trí (pos1_idx). Kết quả có thể rỗng.")

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
        Chạy backtest 30 ngày cho cầu Đề.
        [FIX SHADOW] Ưu tiên cấu hình Managed Bridge từ DB để đồng bộ với Dashboard.
        """
        if not all_data_ai:
            return None
        
        try:
            from services.bridge_service import BridgeService
            from logic.de_backtester_core import run_de_bridge_historical_test
            
            # --- 1. ƯU TIÊN: KIỂM TRA TRONG DB TRƯỚC (Managed Bridge) ---
            # Để đảm bảo logic đồng nhất với Bảng Cầu Động (dùng Index V16)
            bridge_service = BridgeService(self.db_name, logger=self.logger)
            bridge_config = bridge_service.get_de_bridge_config_by_name(bridge_name)
            
            if bridge_config:
                # Nếu tìm thấy trong DB, chạy ngay với config đó (sẽ dùng pos1_idx chuẩn)
                self._log(f"-> Chạy Backtest Managed Bridge: {bridge_name}")
                return run_de_bridge_historical_test(bridge_config, all_data_ai, days=30)

            # --- 2. NẾU KHÔNG CÓ TRONG DB -> CHẠY LOGIC SCANNER TỪ TÊN ---
            is_scanner = False
            def_string = bridge_name
            b_type = "UNKNOWN"
            k_offset = 0

            # CASE A: Cầu Scanner chuẩn mới (VD: GDB.0-G1.0)
            if "G" in bridge_name and "-" in bridge_name and any(c.isdigit() for c in bridge_name):
                is_scanner = True
                if "Bộ" in bridge_name or "DE_SET" in bridge_name: b_type = "DE_SET"
                elif "DE_POS" in bridge_name: b_type = "DE_POS_SUM"
                else: b_type = "DE_DYNAMIC_K"
            
            # CASE B: Cầu Dynamic cũ / Killer / Bộ / Pos / Cầu Bóng (Dạng chuỗi nhưng không có trong DB)
            elif any(x in bridge_name for x in ["DE_DYN_", "DE_KILLER_", "DE_SET_", "DE_POS_"]):
                try:
                    parts = bridge_name.split('_')
                    
                    # [FIX QUAN TRỌNG] Nhận diện cả 'G...' VÀ 'Bong(...)'
                    pos_parts = []
                    for p in parts:
                        if any(c.isdigit() for c in p) and (p.startswith("G") or p.lower().startswith("bong") or "ong(" in p):
                            pos_parts.append(p)
                    
                    if len(pos_parts) >= 2:
                        p1 = pos_parts[0].replace('[', '.').replace(']', '') 
                        p2 = pos_parts[1].replace('[', '.').replace(']', '')
                        
                        def_string = f"{p1}-{p2}"
                        is_scanner = True
                        
                        if "DE_SET_" in bridge_name: b_type = "DE_SET"
                        elif "DE_POS_" in bridge_name: b_type = "DE_POS_SUM"
                        elif "DE_KILLER_" in bridge_name: b_type = "DE_DYNAMIC_K"
                        else: b_type = "DE_DYNAMIC_K"
                            
                        if parts[-1].startswith("K") and parts[-1][1:].isdigit():
                            k_offset = int(parts[-1][1:])
                            
                        self._log(f"-> Converted '{bridge_name}' to Scanner format: '{def_string}'")
                except: pass 

            # --- 3. GỌI BACKTEST SCANNER ---
            if is_scanner:
                scanner_config = {
                    "name": bridge_name,
                    "type": b_type,
                    "is_scanner_result": True, 
                    "def_string": def_string,
                    "k_offset": k_offset
                }
                return run_de_bridge_historical_test(scanner_config, all_data_ai, days=30)
            
            return None
                
        except Exception as e:
            self._log(f"Lỗi Backtest Đề: {e}")
            import traceback
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
