# 📐 TÀI LIỆU KIẾN TRÚC & THUẬT TOÁN HỆ THỐNG (V7.7)

> **Dự án:** Xổ Số Data Analysis System (XS-DAS)
> **Phiên bản:** V7.7 (Special Prize Upgrade)
> **Ngày cập nhật:** 25/11/2025
> **Mục đích:** Tổng hợp quy trình vận hành, luồng dữ liệu và thuật toán cốt lõi để phục vụ việc rà soát, bảo trì và tối ưu hóa.

---

## 1. TỔNG QUAN KIẾN TRÚC (HIGH-LEVEL ARCHITECTURE)

Hệ thống hoạt động theo mô hình **MVP (Model-View-Presenter)** với luồng dữ liệu một chiều, đảm bảo sự tách biệt giữa giao diện và xử lý logic.

```mermaid
graph TD
    User((Người Dùng)) -->|1. Nạp Dữ Liệu/Cấu Hình| UI[Giao Diện (View)]
    UI -->|2. Gửi Lệnh| Controller[Bộ Điều Phối (Presenter)]
    subgraph "CORE ENGINE (Model)"
        Controller --> Scanner[Bộ Quét Cầu]
        Controller --> Analytics[Bộ Thống Kê]
        Controller --> AI[AI Model (XGBoost)]
        Controller --> Backtester[Bộ Kiểm Thử]
    end
    subgraph "STORAGE (Lưu Trữ)"
        Scanner & Analytics <--> DB[(SQLite DB)]
        AI <--> Joblib[File Mô Hình AI]
        Backtester --> Cache[K2N Cache]
    end
    Core -->|3. Trả Kết Quả| UI
    UI -->|4. Hiển Thị| Dashboard[Bảng Quyết Định]
```
---

## 2. PHÂN HỆ 1: QUY TRÌNH SOI CẦU LÔ (CORE LEGACY)

Đây là hệ thống phức tạp nhất, sử dụng cơ chế "Chấm điểm đa tiêu chí" (Multi-criteria Scoring) để tìm ra cặp số Lô đẹp nhất.

### 2.1. Lưu Đồ Thuật Toán (Algorithm Flowchart)

```flowchart TD
    Start([Bắt Đầu]) --> Input[Dữ Liệu 300+ Kỳ]
    subgraph "BƯỚC 1: TÌM KIẾM ỨNG VIÊN (CANDIDATES)"
        Input --> C1[15 Cầu Cổ Điển]
        Input --> C2[756 Cầu Bạc Nhớ]
        Input --> C3[Cầu V17 (Người dùng lưu)]
        C1 & C2 & C3 --> Candidates[Danh Sách Cặp Số Dự Đoán]
    end
    subgraph "BƯỚC 2: KIỂM TRA SỨC KHỎE (BACKTEST)"
        Candidates --> Test{Chạy Backtest K2N}
        Test --> Metric1[Tỷ lệ thắng %]
        Test --> Metric2[Chuỗi ăn thông (Streak)]
        Test --> Metric3[Gan cực đại (Max Lose)]
    end
    subgraph "BƯỚC 3: THAM VẤN (AI & THỐNG KÊ)"
        Input --> AI_Engine[AI XGBoost Dự Đoán]
        Input --> Stats[Thống Kê Gan/Hot]
    end
    subgraph "BƯỚC 4: CHẤM ĐIỂM HỘI TỤ (SCORING MATRIX)"
        Metric1 & Metric2 & Metric3 & AI_Engine & Stats --> Scoring{TÍNH ĐIỂM}
        Scoring -->|Cộng Điểm| P1[+ Vote (Nhiều cầu báo)]
        Scoring -->|Cộng Điểm| P2[+ AI (Máy học xác nhận)]
        Scoring -->|Cộng Điểm| P3[+ Streak (Đang thông)]
        Scoring -->|Trừ Điểm| M1[- Risk (Hay gãy khung)]
        Scoring -->|Trừ Điểm| M2[- Gan (Lâu chưa về)]
    end
    Scoring --> Ranking[Xếp Hạng Top Cặp Số]
    Ranking --> Display[Hiển Thị Dashboard Lô]
```

### 2.2. Điểm Cần Rà Soát & Tối Ưu
- **Trọng số (Weights):** Các hệ số cộng/trừ điểm hiện tại đang được cài đặt cứng (hard-coded). Nên đưa vào config.json để dễ tinh chỉnh (Ví dụ: Tăng trọng số AI, giảm trọng số Vote).
- **Hiệu năng:** Backtest K2N là tác vụ nặng nhất. Cần đảm bảo cơ chế Caching hoạt động tốt để không phải tính lại những cầu cũ.

---

## 3. PHÂN HỆ 2: QUY TRÌNH SOI CẦU ĐỀ (NEW V7.7)

Hệ thống này sử dụng tư duy "Phễu Lọc" (Funnel Filtering): Quét diện rộng $\rightarrow$ Chấm điểm $\rightarrow$ Lọc tinh bằng Bộ Số.

### 3.1. Lưu Đồ Thuật Toán

```flowchart TD
    StartDe([Bắt Đầu]) --> DataDe[Dữ Liệu Lịch Sử]
    subgraph "PHASE 1: QUÉT DIỆN RỘNG (DEEP SCAN)"
        DataDe --> ScanCham[Quét Cầu CHẠM]
        DataDe --> ScanTong[Quét Cầu TỔNG]
        DataDe --> ScanBo[Quét Cầu BỘ]
        ScanCham & ScanTong & ScanBo --> FilterStreak{Lọc Streak > 3}
        FilterStreak --> ActiveBridges[Danh Sách Cầu Đang Chạy]
    end
    subgraph "PHASE 2: ĐỊNH LƯỢNG (SCORING)"
        ActiveBridges --> Matrix[Ma Trận Điểm Số 00-99]
        note1[Điểm số của số X = Tổng Streak các cầu báo về X] -.-> Matrix
        ActiveBridges --> StrongSets[Tìm Top Bộ Số Mạnh Nhất]
    end
    subgraph "PHASE 3: PHỄU LỌC (FILTERING)"
        Matrix --> Top65[Dàn 65 Số (Điểm cao nhất)]
        Top65 & StrongSets --> LogicFilter{Logic Giao Thoa}
        LogicFilter -->|Ưu tiên 1| Set1[Số thuộc Top 65 VÀ thuộc Bộ Mạnh]
        LogicFilter -->|Ưu tiên 2| Set2[Số điểm cao còn lại]
        Set1 & Set2 --> Top10[Dàn 10 Số Kết]
        Top10 --> Top4[Dàn 4 Số Tứ Thủ]
    end
    Top4 --> UI_De[Hiển Thị Dashboard Đề]
```

### 3.2. Chiến Thuật Lọc Số (Filtering Strategy)
- **Dàn 65:** Lấy thuần túy theo điểm số (Score). Ai nhiều cầu chỉ vào thì đứng đầu.
- **Top 10:** Áp dụng "Bộ Lọc Cấu Trúc". Chỉ những số điểm cao VÀ nằm trong các Bộ Số (Sets) đang có cầu chạy mới được ưu tiên. Điều này giúp loại bỏ những con số "ăn may" (chỉ dính 1-2 cầu chạm lẻ tẻ).
- **Top 4:** Tinh hoa của Top 10.

---

## 4. CÁC FILE MÃ NGUỒN LIÊN QUAN

**Backend Logic**  
logic/backtester_core.py: Lõi tính toán kiểm thử (Dùng chung).
logic/dashboard_analytics.py: Logic chấm điểm Lô.
logic/de_analytics.py: Logic chấm điểm Đề & Tìm bộ mạnh.
logic/bridges/de_bridge_scanner.py: Bộ quét cầu Đề (Chạm/Tổng/Bộ).

**Frontend UI**  
ui/ui_dashboard.py: Bảng Quyết Định Lô.
ui/ui_de_dashboard.py: Dashboard Đề (3 Cột).

---

## 5. HƯỚNG DẪN TỐI ƯU (OPTIMIZATION PLAN)
- **Tăng tốc độ quét:**
    - Giới hạn scan_depth (số kỳ quét về quá khứ) ở mức 20-30 kỳ.
    - Sử dụng limit_pos (số vị trí quét) khoảng 60-100 vị trí đầu tiên của bảng kết quả.
- **Cải thiện độ chính xác:**
    - Định kỳ chạy v77_phase2_finalize.py để AI học lại dữ liệu mới nhất.
    - Điều chỉnh ngưỡng MIN_STREAK lên 4 hoặc 5 nếu thấy quá nhiều cầu rác.

---

*Tài liệu này được tạo bởi Trợ lý AI (Copilot) ngày 25/11/2025.*
