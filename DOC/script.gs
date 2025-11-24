/**
 * HỆ THỐNG HÀM TÙY CHỈNH TỔNG HỢP V30.0
 * * BAO GỒM 3 CHỨC NĂNG CHÍNH:
 * 1. PHANTICH_V30_LAIGHEP_MIN3: Phân tích (Dự đoán) 6 hạng mục (Tối thiểu 3 ngày).
 * 2. DANHGIA_V30_LAIGHEP_MIN3: Đánh giá kết quả 6 hạng mục.
 * 3. BACKTEST_9_CAU_K2N_V30: Backtest 9 cầu lô theo Khung 2 Ngày (K2N)
 * (Đã tích hợp logic BÓNG KÉP: 44 -> 44,99).
 *
 * HƯỚNG DẪN SỬ DỤNG:
 *
 * 1. ĐỂ PHÂN TÍCH (DỰ ĐOÁN): (Yêu cầu >= 3 ngày dữ liệu A:K)
 * =PHANTICH_V30_LAIGHEP_MIN3(A4:K6)
 *
 * 2. ĐỂ ĐÁNH GIÁ KẾT QUẢ:
 * =DANHGIA_V30_LAIGHEP_MIN3(A7:K7, M6:R6)
 * * 3. ĐỂ BACKTEST KHUNG 2 NGÀY:
 * =BACKTEST_9_CAU_K2N_V30(A2:K21, 3, 21) 
 * (Kiểm tra dữ liệu A2:K21, bắt đầu từ Hàng 3, kết thúc ở Hàng 21)
 */

// ===================================================================================
// I. CẤU HÌNH HỆ THỐNG V30
// ===================================================================================

// Cấu hình cho logic Phân tích Chạm (V28)
const SCORE_WEIGHTS_V30 = {
    FREQ: 50, LATENESS: 25, PAIR: 15, BOSO: 10
};
const BO_SO_DE_V30 = { "01": ["01", "06", "10", "15", "51", "60", "56", "65"], "02": ["02", "07", "20", "70", "25", "52", "57", "75"], "03": ["03", "08", "30", "80", "35", "53", "58", "85"], "04": ["04", "09", "40", "90", "45", "54", "59", "95"], "12": ["12", "21", "17", "71", "26", "62", "67", "76"], "13": ["13", "31", "18", "81", "36", "63", "68", "86"], "14": ["14", "41", "19", "91", "46", "64", "69", "96"], "23": ["23", "32", "28", "82", "37", "73", "78", "87"], "24": ["24", "42", "29", "92", "47", "74", "79", "97"], "34": ["34", "43", "39", "93", "48", "84", "89", "98"], "00": ["00", "05", "50", "55"], "11": 
["11", "16", "61", "66"], "22": ["22", "27", "72", "77"], "33": ["33", "38", "83", "88"], "44": ["44", "49", "94", "99"] };

// Cấu hình cho logic Bóng Kép (Backtest K2N)
const BONG_DUONG_V30 = { '0': '5', '1': '6', '2': '7', '3': '8', '4': '9', '5': '0', '6': '1', '7': '2', '8': '3', '9': '4' };


// ===================================================================================
// II. HÀM CÔNG KHAI 1 & 2: PHÂN TÍCH & ĐÁNH GIÁ (LOGIC V25.2)
// ===================================================================================

/**
 * [V30] Phân tích LAI GHÉP (Cửa sổ >= 3 ngày).
 *
 * @param {range} rangeA_K Dữ liệu lịch sử (từ Cột A đến K).
 * @returns {Array<Array<string>>} Một hàng 6 cột kết quả.
 * @customfunction
 */
function PHANTICH_V30_LAIGHEP_MIN3(rangeA_K) {
  const analysis = analyzeV30_CORE_MIN3(rangeA_K);

  if (!analysis) {
    const soNgay = rangeA_K ? rangeA_K.length : 0;
    if (soNgay < 3) { 
      return [[`Cần ít nhất 3 ngày...`, "", "", "", "", ""]];
    }
    return [["Đang chờ đủ dữ liệu...", "", "", "", "", ""]];
  }
  
  if (typeof analysis === 'string') {
    return [[analysis, "LỖI", "LỖI", "LỖI", "LỖI", "LỖI"]];
  }

  const resultsRow = [
    analysis.de4Cham, 
    analysis.de10So,
    analysis.stl,
    analysis.loKhung,
    analysis.ldp,
    analysis.lo3D
  ];
  
  return [resultsRow];
}

/**
 * [V30] Đánh giá TỰ ĐỘNG 6 hạng mục dự đoán so với kết quả.
 *
 * @param {A15:K15} actualDataRow Hàng KẾT QUẢ THỰC TẾ của ngày đó (1 hàng x 11 cột).
 * @param {M14:R14} predictionDataRow Hàng DỰ ĐOÁN (do hàm TUDONG tạo ra) (1 hàng x 6 cột).
 * @returns {Array<Array<string>>} Một hàng 6 cột kết quả đánh giá.
 * @customfunction
 */
function DANHGIA_V30_LAIGHEP_MIN3(actualDataRow, predictionDataRow) {
  try {
    if (!actualDataRow || !actualDataRow[0] || !actualDataRow[0][1] || !predictionDataRow || !predictionDataRow[0]) {
      return [["Chờ dữ liệu...", "", "", "", "", ""]];
    }
    
    const actuals = {
      de: actualDataRow[0][1].toString().padStart(2, '0'), // Cột B
      allLoto: getAllLoto_V30(actualDataRow[0]), // Dùng hàm V30
      allCang3D: getAllCang3D_V30(actualDataRow[0]) // Dùng hàm V30
    };

    const preds = {
      cham4: predictionDataRow[0][0].split('').map(Number), // Cột M
      de10So: predictionDataRow[0][1].split(', '),          // Cột N
      stl: predictionDataRow[0][2].split(', '),              // Cột O
      khung: predictionDataRow[0][3].split(', '),            // Cột P
      ldp: predictionDataRow[0][4].split(', '),              // Cột Q
      lo3d: predictionDataRow[0][5].split(', ')              // Cột R
    };

    const results = [];
    const deChamThucTe = getChams_V30(actuals.de);
    
    const chamHit = (preds.cham4.includes(deChamThucTe[0]) || preds.cham4.includes(deChamThucTe[1]));
    results.push(chamHit ? `✅ (Ăn ${deChamThucTe.join(',')})` : `❌ (Trượt ${actuals.de})`);

    const de10Hit = preds.de10So.includes(actuals.de);
    results.push(de10Hit ? `✅ (Ăn ${actuals.de})` : `❌ (0/${preds.de10So.length})`);

    const stlHits = preds.stl.filter(p => actuals.allLoto.includes(p)).length;
    results.push(stlHits > 0 ? `✅ (${stlHits}/${preds.stl.length})` : `❌ (0/${preds.stl.length})`);

    const khungHits = preds.khung.filter(p => actuals.allLoto.includes(p)).length;
    results.push(khungHits > 0 ? `✅ (N1: ${khungHits}/${preds.khung.length})` : `❌ (0/${preds.khung.length})`);

    const ldpHits = preds.ldp.filter(p => actuals.allLoto.includes(p)).length;
    results.push(ldpHits > 0 ? `✅ (${ldpHits}/${preds.ldp.length})` : `❌ (0/${preds.ldp.length})`);

    const lo3dHits = preds.lo3d.filter(p => actuals.allLoto.includes(p)).length;
    results.push(lo3dHits > 0 ? `✅ (${lo3dHits}/${preds.lo3d.length})` : `❌ (0/${preds.lo3d.length})`);

    return [results];

  } catch (e) {
    Logger.log(e);
    return [[`LỖI: ${e.message}`, "", "", "", "", ""]];
  }
}

/**
 * [V30] Hàm lõi Phân tích (Lai ghép V24 + V28)
 */
function analyzeV30_CORE_MIN3(historyData) {
  try {
    if (!historyData || historyData.length < 3 || historyData[0].length < 11) {
      return null;
    }

    // === PHẦN 1: CHẠY LOGIC V24 (CHO 5 HẠNG MỤC) ===
    const processedDataV24 = preprocessData_V30(historyData);
    const ganStatsV24 = getGanStats_V30(processedDataV24); 
    
    const lastDay = processedDataV24[processedDataV24.length - 1];
    const prevDay = processedDataV24[processedDataV24.length - 2];

    const analysis = {};

    // === PHẦN 2: CHẠY LOGIC V28 (CHO "ĐỀ 4 CHẠM") ===
    const de_results_for_v28 = historyData.map(row => [row[1]]);
    const combinations4Cham = generateCombinations_V30_MIN3(4); 
    analysis.de4Cham = logic_tim_tonghop_cham_V30_MIN3(de_results_for_v28, combinations4Cham); 
    
    // === PHẦN 3: CHẠY LOGIC V24 (CHO 5 HẠNG MỤC CÒN LẠI) ===
    const stl1 = lastDay.de; 
    let stl2Entry = Object.entries(ganStatsV24.lotoGan)
                        .filter(([num, gan]) => gan >= 3 && gan <= 5)
                        .sort((a, b) => ganStatsV24.lotoFrequency[b[0]] - ganStatsV24.lotoFrequency[a[0]])[0];
    const stl2 = stl2Entry ? stl2Entry[0] : "00"; 
    analysis.stl = [stl1, stl2].join(', ');

    const roiG4G7 = lastDay.g4g7.split(',').map(g => g.slice(-2).padStart(2, '0'));
    const khung1 = roiG4G7[0] || "11"; 
    let khung2Entry = Object.entries(ganStatsV24.lotoGan)
                          .filter(([num, gan]) => gan >= 5 && gan <= 7)
                          .sort((a, b) => ganStatsV24.lotoFrequency[b[0]] - ganStatsV24.lotoFrequency[a[0]])[0];
    const khung2 = khung2Entry ? khung2Entry[0] : "22";
    analysis.loKhung = [khung1, khung2].join(', ');

    const roiG3G5 = lastDay.g3g5.split(',').map(g => g.slice(-2).padStart(2, '0'));
    const ldp1 = roiG3G5[0] || "33"; 
    const freqSorted = Object.entries(ganStatsV24.lotoFrequency)
                               .sort((a, b) => b[1] - a[1]);
    const ldp2 = freqSorted.find(entry => ![stl1, stl2, khung1, khung2].includes(entry[0]))[0]; 
    const ldp3 = Object.entries(ganStatsV24.deGanNumbers).sort((a, b) => b[1] - a[1])[0][0]; 
    analysis.ldp = [ldp1, ldp2, ldp3].join(', ');

    const de10so = [];
    const cham4 = analysis.de4Cham.split('').map(Number); // Dùng chạm V28
    const kep = ["00","11","22","33","44","55","66","77","88","99"];
    const kepLech = ["05","50","16","61","27","72","38","83","49","94"];
    const deRoi = [lastDay.de, prevDay.de];

    [...kep, ...kepLech, ...deRoi].forEach(num => {
      if (de10so.length < 10 && isInCham_V30(num, cham4) && !de10so.includes(num)) {
        de10so.push(num);
      }
    });
    for (let i = 0; i < 100 && de10so.length < 10; i++) {
      const num = i.toString().padStart(2, '0');
      if (isInCham_V30(num, cham4) && !de10so.includes(num)) {
        de10so.push(num);
      }
    }
    analysis.de10So = de10so.join(', ');
    
    const sumGDB = lastDay.gdb.split('').reduce((acc, c) => acc + parseInt(c), 0);
    const cang1 = (sumGDB % 10).toString(); 
    const cang2 = Object.entries(ganStatsV24.cangGan).sort((a, b) => b[1] - a[1])[0][0]; 
    
    const ldpMoi1 = ldp1;
    const ldpMoi2 = ldp2;
    analysis.lo3D = [
      cang1 + ldpMoi1,
      cang2 + ldpMoi1,
      cang1 + ldpMoi2,
      cang2 + ldpMoi2
    ].join(', ');

    return analysis;

  } catch (e) {
    Logger.log(e);
    return `LỖI V30: ${e.message}`;
  }
}

// ===================================================================================
// III. HÀM CÔNG KHAI 3: BACKTEST 9 CẦU KHUNG 2 NGÀY (LOGIC V29_K2N + BÓNG)
// ===================================================================================

/**
 * [V30] Backtest 9 Cầu Lô (Logic Khung 2 Ngày + Bóng Kép)
 * Báo cáo kết quả Ăn N1, Ăn N2, hoặc Trượt K2N.
 *
 * @param {A2:K100} toan_bo_A_K Toàn bộ dải ô A:K chứa dữ liệu.
 * @param {10} ky_bat_dau_kiem_tra Kỳ (hàng) bắt đầu kiểm tra (phải > 1).
 * @param {20} ky_ket_thuc_kiem_tra Kỳ (hàng) kết thúc kiểm tra.
 * @returns {Array<Array<string>>} Bảng kết quả backtest K2N.
 * @customfunction
 */
function BACKTEST_9_CAU_K2N_V30(toan_bo_A_K, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra) {
  if (!toan_bo_A_K || !ky_bat_dau_kiem_tra || !ky_ket_thuc_kiem_tra) {
    return [["LỖI:", "Cần đủ tham số (toan_bo_A_K, ky_bat_dau, ky_ket_thuc)."]];
  }
  
  const startRow = parseInt(ky_bat_dau_kiem_tra, 10);
  const endRow = parseInt(ky_ket_thuc_kiem_tra, 10);
  
  if (isNaN(startRow) || isNaN(endRow) || startRow <= 1 || startRow > endRow) {
    return [["LỖI:", `Kỳ BĐ/KT không hợp lệ. Kỳ BĐ (${startRow}) phải > 1.`]];
  }
  
  const allData = toan_bo_A_K; 
  const maxDataLength = allData.length;
  const finalEndRow = Math.min(endRow, maxDataLength);
  
  if (startRow > finalEndRow) {
    return [["LỖI:", `Dữ liệu chỉ có ${maxDataLength} dòng. Không thể bắt đầu từ ${startRow}.`]];
  }

  // Tiêu đề
  const results = [
    ["Kỳ", "KQ Đề", "KQ Lô", 
     "Cầu 1 (STL+5)", "Cầu 2 (G6+G7)", "Cầu 3 (GĐB+G1)", 
     "Cầu 4 (GĐB+G1)", "Cầu 5 (G7+G7)", "Cầu 6 (G7+G7)", 
     "Cầu Mới 1 (G5+G7)", "Cầu Mới 2 (G3+G4)", "Cầu Mới 3 (GĐB+G1)",
     "Tổng Trúng"]
  ];
  
  // Mảng theo dõi trạng thái K2N cho 9 cầu
  let in_frame = new Array(9).fill(false);
  let prediction_in_frame = new Array(9).fill(null);
  
  // Mảng chứa các hàm dự đoán (để gọi động)
  const cau_functions = [
    getCau1_STL_P5_V30, getCau2_VT1_V30, getCau3_VT2_V30,
    getCau4_VT3_V30, getCau5_TDB1_V30, getCau6_VT5_V30,
    getCau7_Moi1_V30, getCau8_Moi2_V30, getCau9_Moi3_V30
  ];

  Logger.log(`Bắt đầu Backtest V30 (K2N) từ kỳ ${startRow} đến ${finalEndRow}...`);

  for (let k = startRow; k <= finalEndRow; k++) {
    const prevRow = allData[k - 2]; 
    const actualRow = allData[k - 1]; 

    if (!prevRow || !actualRow || !actualRow[1] || !actualRow[10]) {
        results.push([k, "Lỗi dữ liệu hàng", "", "", "", "", "", "", "", "", "", "", 0]);
        continue;
    }
    
    const actualDe = (actualRow[1] || '??').toString().padStart(2, '0');
    const actualLotoSet = new Set(getAllLoto_V30(actualRow));
    const actualLotoStr = Array.from(actualLotoSet).slice(0, 5).join(',') + '...';

    let daily_results_row = [k, actualDe, actualLotoStr];
    let totalHits = 0;

    try {
      // Lặp qua 9 cầu
      for (let j = 0; j < 9; j++) {
        let pred = [];
        let check_result = "";
        let cell_output = "---";

        if (in_frame[j]) {
          // --- Đang ở Ngày 2 (N2) ---
          pred = prediction_in_frame[j];
          check_result = checkHitSet_V30_K2N(pred, actualLotoSet);

          if (check_result.includes("✅")) {
            cell_output = `${pred.join(',')} ✅ (Ăn N2)`;
            totalHits++;
          } else {
            cell_output = `${pred.join(',')} ❌ (Trượt K2N)`;
          }
          in_frame[j] = false;
          prediction_in_frame[j] = null;
          
        } else {
          // --- Đang ở Ngày 1 (N1) ---
          pred = cau_functions[j](prevRow);
          check_result = checkHitSet_V30_K2N(pred, actualLotoSet);

          if (check_result.includes("✅")) {
            cell_output = `${pred.join(',')} ✅ (Ăn N1)`;
            totalHits++;
          } else {
            cell_output = `${pred.join(',')} (Trượt N1...)`;
            in_frame[j] = true;
            prediction_in_frame[j] = pred;
          }
        }
        daily_results_row.push(cell_output);
      } // kết thúc lặp 9 cầu

      daily_results_row.push(totalHits);
      results.push(daily_results_row);

    } catch (e) {
      Logger.log(`Lỗi Backtest K2N V30 tại kỳ ${k}: ${e.message}`);
      results.push([k, actualDe, "Lỗi: " + e.message, "", "", "", "", "", "", "", "", "", 0]);
    }
  }
  
  // Xử lý các khung còn đang mở (nếu hết dữ liệu)
  let finalRow = [`Kỳ ${finalEndRow+1}`, "(Chờ KQ)", ""];
  let openFrames = 0;
  for (let j = 0; j < 9; j++) {
    if (in_frame[j]) {
      finalRow.push(`${prediction_in_frame[j].join(',')} (Đang chờ N2)`);
      openFrames++;
    } else {
      finalRow.push("---");
    }
  }
  finalRow.push(openFrames > 0 ? `${openFrames} khung mở` : "0");
  results.push(finalRow);
  
  Logger.log(`Backtest K2N V30 (9 Cầu) hoàn thành.`);
  return results;
}

// ===================================================================================
// IV. THƯ VIỆN HÀM HỖ TRỢ CHUNG V30
// ===================================================================================

// --- A. HÀM HỖ TRỢ K2N (BÓNG) ---

/**
 * [V30] Lấy số bóng dương (0-5, 1-6, 2-7, 3-8, 4-9)
 */
function getBongDuong_V30(digit) {
  return BONG_DUONG_V30[digit.toString()] || digit.toString();
}

/**
 * [V30] Hàm tạo STL (Tự động xử lý Kép -> Bóng)
 */
function taoSTL_V30_Bong(a, b) {
  const strA = a.toString();
  const strB = b.toString();

  // Rule 1: Kép (e.g., a='3', b='3')
  if (strA === strB) {
    const kep = `${strA}${strB}`.padStart(2, '0');
    const bongDigit = getBongDuong_V30(strA);
    const bongKep = `${bongDigit}${bongDigit}`.padStart(2, '0');
    return [kep, bongKep];
  }
  
  // Rule 2: Standard Lộn
  const lo1 = `${strA}${strB}`.padStart(2, '0');
  const lo2 = `${strB}${strA}`.padStart(2, '0');
  return [lo1, lo2];
}

/**
 * [V30] Kiểm tra xem 1 cặp STL có trúng trong 1 Set Lô không
 */
function checkHitSet_V30_K2N(stlPair, lotoSet) {
  try {
    const hit1 = lotoSet.has(stlPair[0]);
    const hit2 = lotoSet.has(stlPair[1]);
    
    if (hit1 && hit2) return "✅ (Ăn 2)";
    if (hit1 || hit2) return "✅ (Ăn 1)";
    
    return "❌";
  } catch (e) {
    return "Lỗi check";
  }
}

/**
 * [V30] Lấy tất cả 27 lô từ 1 hàng A:K
 */
function getAllLoto_V30(row) {
  const lotos = [];
  try {
    lotos.push(row[1].toString().padStart(2, '0')); // B: Đề
    lotos.push(row[4].toString().slice(-2).padStart(2, '0')); // E: G1
    row[5].toString().split(',').forEach(g => lotos.push(g.slice(-2).padStart(2, '0'))); // F: G2
    row[6].toString().split(',').forEach(g => lotos.push(g.slice(-2).padStart(2, '0'))); // G: G3
    row[7].toString().split(',').forEach(g => lotos.push(g.slice(-2).padStart(2, '0'))); // H: G4
    row[8].toString().split(',').forEach(g => lotos.push(g.slice(-2).padStart(2, '0'))); // I: G5
    row[9].toString().split(',').forEach(g => lotos.push(g.slice(-2).padStart(2, '0'))); // J: G6
    row[10].toString().split(',').forEach(g => lotos.push(g.slice(-2).padStart(2, '0'))); // K: G7
  } catch (e) {}
  return lotos.filter(l => l && l.length === 2 && !isNaN(l));
}

// --- B. 9 HÀM LOGIC CẦU LÔ (DÙNG CHO K2N) ---

/** [V30] Cầu 1: STL +5 (Tính toán) */
function getCau1_STL_P5_V30(row) {
  try {
    const gdb = (row[3] || '00000').toString();
    const de = gdb.slice(-2).padStart(2, '0');
    const a = parseInt(de[0]), b = parseInt(de[1]);
    const x = (a + 5) % 10;
    const y = (b + 5) % 10;
    return taoSTL_V30_Bong(x, y);
  } catch(e) { return ['00', '55']; }
}

/** [V30] Cầu 2: VT 1 (G6.3_cuối + G7.4_cuối) */
function getCau2_VT1_V30(row) {
  try {
    const g6 = (row[9] || ',,').toString().split(',');
    const g7 = (row[10] || ',,,').toString().split(',');
    const a = (g6[2] || '0').slice(-1);
    const b = (g7[3] || '0').slice(-1);
    return taoSTL_V30_Bong(a, b);
  } catch(e) { return ['00', '55']; }
}

/** [V30] Cầu 3: VT 2 (GĐB_cuối + G1_cuối) */
function getCau3_VT2_V30(row) {
  try {
    const a = (row[3] || '0').toString().slice(-1); // GĐB
    const b = (row[4] || '0').toString().slice(-1); // G1
    return taoSTL_V30_Bong(a, b);
  } catch(e) { return ['00', '55']; }
}

/** [V30] Cầu 4: VT 3 (GĐB[4] + G1_cuối) */
function getCau4_VT3_V30(row) {
  try {
    const a = (row[3] || '00000').toString().slice(-2, -1); // GĐB[4]
    const b = (row[4] || '0').toString().slice(-1); // G1
    return taoSTL_V30_Bong(a, b);
  } catch(e) { return ['00', '55']; }
}

/** [V30] Cầu 5: TĐB 1 (G7.1_đầu + G7.4_cuối) */
function getCau5_TDB1_V30(row) {
  try {
    const g7 = (row[10] || ',,,').toString().split(',');
    const a = (g7[0] || '0').slice(0, 1);
    const b = (g7[3] || '0').slice(-1);
    return taoSTL_V30_Bong(a, b);
  } catch(e) { return ['00', '55']; }
}

/** [V30] Cầu 6: VT 5 (G7.2_cuối + G7.3_đầu) */
function getCau6_VT5_V30(row) {
  try {
    const g7 = (row[10] || ',,,').toString().split(',');
    const a = (g7[1] || '0').slice(-1);
    const b = (g7[2] || '0').slice(0, 1);
    return taoSTL_V30_Bong(a, b);
  } catch(e) { return ['00', '55']; }
}

/** [V30] Cầu 7 (Mới 1): G5.1_đầu + G7.1_đầu */
function getCau7_Moi1_V30(row) {
  try {
    const g5 = (row[8] || ',,,,,').toString().split(',');
    const g7 = (row[10] || ',,,').toString().split(',');
    const a = (g5[0] || '0').slice(0, 1);
    const b = (g7[0] || '0').slice(0, 1);
    return taoSTL_V30_Bong(a, b);
  } catch(e) { return ['00', '55']; }
}

/** [V30] Cầu 8 (Mới 2): G3.1_đầu + G4.1_đầu */
function getCau8_Moi2_V30(row) {
  try {
    const g3 = (row[6] || ',,,,,').toString().split(',');
    const g4 = (row[7] || ',,,').toString().split(',');
    const a = (g3[0] || '0').slice(0, 1);
    const b = (g4[0] || '0').slice(0, 1);
    return taoSTL_V30_Bong(a, b);
  } catch(e) { return ['00', '55']; }
}

/** [V30] Cầu 9 (Mới 3): GĐB.1_đầu + G1.1_đầu */
function getCau9_Moi3_V30(row) {
  try {
    const a = (row[3] || '0').toString().slice(0, 1); // GĐB
    const b = (row[4] || '0').toString().slice(0, 1); // G1
    return taoSTL_V30_Bong(a, b);
  } catch(e) { return ['00', '55']; }
}

// --- C. HÀM HỖ TRỢ CHẠM V28 (CHO HÀM PHANTICH) ---

/** [V30] LOGIC TONGHOP CHẠM (Lõi V28) */
function logic_tim_tonghop_cham_V30_MIN3(ket_qua_range, combinations) {
  if (!combinations || combinations.length === 0) { return "LỖI: Không có bộ chạm."; }
  const validResults = cleanAndValidate_V30_MIN3(ket_qua_range); 
  const totalPeriods = validResults.length;
  if (totalPeriods < 3) return "Cần >= 3 kỳ."; 

  let bestCombo = "", maxScore = -Infinity;
  const lateness = calculateLateness_V30_MIN3(validResults); 
  const { pairModel, baselineProb } = logic_build_digit_pair_model_V30_MIN3(validResults); 
  const lastResultRaw = validResults[totalPeriods - 1];
  const lastResult = String(lastResultRaw).padStart(2, '0'); 
  const lastResultDigits = getDigits_V30_MIN3(lastResultRaw); 
  const boSoKey = findBoSoKey_V30_MIN3(lastResult); 
  const relatedBoSoNumbers = boSoKey ? BO_SO_DE_V30[boSoKey] : []; 
  const relatedBoSoDigits = new Set();
  if (boSoKey) { relatedBoSoNumbers.forEach(num => getDigits_V30_MIN3(num).forEach(d => relatedBoSoDigits.add(d))); } 

  for (const combo of combinations) {
    const scores = calculateChamScores_V30_MIN3(combo, validResults, lateness, pairModel, baselineProb, lastResultDigits, boSoKey, relatedBoSoDigits); 
    if (scores.finalScore > maxScore) { 
      maxScore = scores.finalScore;
      bestCombo = combo; 
    }
  }
  if (!bestCombo) return "0123"; 
  return `${bestCombo}` ; 
}

/** [V30] Tính điểm cho một BỘ CHẠM (Lõi V28) */
function calculateChamScores_V30_MIN3(combo, validResults, latenessMap, pairModel, baselineProb, lastResultDigits, boSoKey, relatedBoSoDigits) {
    const totalPeriods = validResults.length;
    const numCham = combo.length; 
    const comboDigits = combo.split(''); 
    let scores = { freq: 0, lateness: 0, pair: 0, boSo: 0, finalScore: 0 }; 
    
    const hits = validResults.filter(r => checkHit_V30_MIN3(combo, r)).length; 
    const hitRate = (totalPeriods > 0) ? hits / totalPeriods : 0; 
    scores.freq = hitRate * SCORE_WEIGHTS_V30.FREQ;
    
    let comboLateness = 0;
    comboDigits.forEach(digit => { comboLateness += latenessMap[parseInt(digit)] === undefined ? totalPeriods : latenessMap[parseInt(digit)]; }); 
    scores.lateness = Math.max(0, (10 - comboLateness / numCham) * (SCORE_WEIGHTS_V30.LATENESS / 10)); 
    
    let pairRawScore = 0;
    if(lastResultDigits && lastResultDigits.length > 0) { 
      for (const d of lastResultDigits) { 
        for (const c of comboDigits) { 
          const pairProb = (pairModel[d] && pairModel[d][c]) ? pairModel[d][c] : 0; 
          const baseline = baselineProb[c] || 0.1; 
          pairRawScore += (baseline > 0) ? (pairProb / baseline) : 1; 
        } 
      } 
      const normalizedPairScore = pairRawScore / (lastResultDigits.length * numCham || 1); 
      scores.pair = Math.max(-SCORE_WEIGHTS_V30.PAIR, Math.min(SCORE_WEIGHTS_V30.PAIR, (normalizedPairScore - 1) * SCORE_WEIGHTS_V30.PAIR)); 
    } else { 
      scores.pair = 0; 
    }
    
    if (boSoKey) { 
      const overlap = comboDigits.filter(d => relatedBoSoDigits.has(d)).length; 
      scores.boSo = (overlap / numCham) * SCORE_WEIGHTS_V30.BOSO; 
    }
    
    scores.finalScore = scores.freq + scores.lateness + scores.pair + scores.boSo; 
    return scores;
}

/** [V30] Hàm tìm Bộ Số (V28) */
function findBoSoKey_V30_MIN3(numberStr) {
    for (const key in BO_SO_DE_V30) {
        if (BO_SO_DE_V30[key].includes(numberStr)) {
            return key;
        }
    }
    return null;
}

/** [V30] Hàm làm sạch (V28) */
function cleanAndValidate_V30_MIN3(dataRange) {
    return dataRange.flat()
        .map(cell => (cell === null || cell === undefined) ? '' : String(cell).replace(/\D/g, ''))
        .filter(cell => cell.length > 0);
}

/** [V30] Lấy chữ số (V28) */
function getDigits_V30_MIN3(r) {
    const v = String(r).padStart(2, '0');
    const d1 = v[0];
    const d2 = v[1];
    return (d1 === d2) ? [d1] : [d1, d2];
}

/** [V30] Tạo bộ chạm (V28) */
function generateCombinations_V30_MIN3(numCham) {
    const c = [];
    if (numCham == 4) {
        for (let i = 0; i < 7; i++) for (let j = i + 1; j < 8; j++) for (let k = j + 1; k < 9; k++) for (let l = k + 1; l < 10; l++) c.push(`${i}${j}${k}${l}`); 
    } else if (numCham == 3) {
        for (let i = 0; i < 8; i++) for (let j = i + 1; j < 9; j++) for (let k = j + 1; k < 10; k++) c.push(`${i}${j}${k}`); 
    }
    return c;
}

/** [V30] Kiểm tra trúng (V28) */
function checkHit_V30_MIN3(c, r) {
    const v = String(r).padStart(2, '0');
    return c.includes(v[0]) || c.includes(v[1]);
}

/** [V30] Xây dựng mô hình Cặp Chạm (V28) */
function logic_build_digit_pair_model_V30_MIN3(validResults) {
    let pairModel = {};
    let totalCounts = {}; 
    let baselineProb = {}; 
    let totalDigits = 0;
    
    if (!validResults || validResults.length < 2) { 
      return { pairModel, baselineProb }; 
    } 
    
    for (let i = 0; i < validResults.length - 1; i++) {
        const prevDigits = getDigits_V30_MIN3(validResults[i]); 
        const currDigits = getDigits_V30_MIN3(validResults[i+1]); 
        for (const p of prevDigits) {
            totalCounts[p] = (totalCounts[p] || 0) + 1;
            if (!pairModel[p]) { pairModel[p] = {}; } 
            for (const c of currDigits) { pairModel[p][c] = (pairModel[p][c] || 0) + 1; }
        }
    }
    
    for (const r of validResults) { 
      for (const d of getDigits_V30_MIN3(r)) { 
        baselineProb[d] = (baselineProb[d] || 0) + 1; 
        totalDigits++; 
      } 
    } 
    
    if (totalDigits > 0) { 
      for (const d in baselineProb) { 
        baselineProb[d] = baselineProb[d] / totalDigits; 
      } 
    } 
    
    for (const p in pairModel) { 
      for (const c in pairModel[p]) { 
        if (totalCounts[p] > 0) { 
          pairModel[p][c] = pairModel[p][c] / totalCounts[p]; 
        } else { 
          pairModel[p][c] = 0; 
        } 
      } 
    } 
    return { pairModel, baselineProb };
}

/** [V30] Tính độ gan chạm (V28) */
function calculateLateness_V30_MIN3(r) { 
    let l = { 0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0 };
    let found = new Set();
    const len = r.length;
    for (let i = len - 1; i >= 0; i--) { 
        if (found.size === 10) break;
        const digits = getDigits_V30_MIN3(r[i]); 
        for (const dStr of digits) {
            const d = parseInt(dStr, 10);
            if (!found.has(d)) { 
                l[d] = len - 1 - i;
                found.add(d); 
            }
        }
    }
    for(let d=0; d<10; d++){ if(!found.has(d)) l[d] = len; } 
    return l;
}

// --- D. HÀM HỖ TRỢ V24 (CHO HÀM PHANTICH) ---

/** [V30] Lấy 3 Càng (cho Đánh giá) */
function getAllCang3D_V30(row) {
  const cangs3D = [];
  try {
    cangs3D.push(row[3].toString().slice(-3)); // D: GĐB
    cangs3D.push(row[4].toString().slice(-3)); // E: G1
    row[5].toString().split(',').forEach(g => cangs3D.push(g.slice(-3))); // F: G2
    row[6].toString().split(',').forEach(g => cangs3D.push(g.slice(-3))); // G: G3
    row[7].toString().split(',').forEach(g => cangs3D.push(g.slice(-3))); // H: G4
    row[8].toString().split(',').forEach(g => cangs3D.push(g.slice(-3))); // I: G5
    row[9].toString().split(',').forEach(g => cangs3D.push(g.slice(-3))); // J: G6
  } catch (e) {}
  return cangs3D.filter(c => c && c.length === 3 && !isNaN(c)).map(c => c.padStart(3, '0'));
}

/** [V30] Lấy Càng (cho Phân tích) */
function getAllCang_V30(row) {
  const cangs = [];
  try {
    cangs.push(row[3].toString().slice(-3, -2)); // D: GĐB
    cangs.push(row[4].toString().slice(-3, -2)); // E: G1
    row[5].toString().split(',').forEach(g => cangs.push(g.slice(-3, -2))); // F: G2
    row[6].toString().split(',').forEach(g => cangs.push(g.slice(-3, -2))); // G: G3
    row[7].toString().split(',').forEach(g => cangs.push(g.slice(-3, -2))); // H: G4
    row[8].toString().split(',').forEach(g => cangs.push(g.slice(-3, -2))); // I: G5
    row[9].toString().split(',').forEach(g => cangs.push(g.slice(-3, -2))); // J: G6
  } catch (e) {}
  return cangs.filter(c => c && c.length === 1 && !isNaN(c));
}

/** [V30] Tiền xử lý dữ liệu (cho Phân tích) */
function preprocessData_V30(dataRows) {
  return dataRows.map(row => {
    return {
      date: row[0],
      de: row[1].toString().padStart(2, '0'),
      gdb: row[3].toString(),
      g1: row[4].toString(),
      g4g7: [row[7], row[8], row[9], row[10]].join(','),
      g3g5: [row[6], row[8]].join(','),
      allLoto: getAllLoto_V30(row),
      allCang: getAllCang_V30(row)
    };
  });
}

/** [V30] Thống kê Gan (cho Phân tích) */
function getGanStats_V30(processedData) {
  const soNgay = processedData.length; 
  const stats = { deChamGan: {}, lotoGan: {}, cangGan: {}, lotoFrequency: {}, deGanNumbers: {} };
  
  for (let i = 0; i < 10; i++) { 
    stats.deChamGan[i] = soNgay; 
    stats.cangGan[i] = soNgay; 
  }
  for (let i = 0; i < 100; i++) {
    const num = i.toString().padStart(2, '0');
    stats.lotoGan[num] = soNgay; 
    stats.lotoFrequency[num] = 0; 
    stats.deGanNumbers[num] = soNgay;
  }

  let daysAgo = 0;
  for (let i = processedData.length - 1; i >= 0; i--) {
    const day = processedData[i];
    daysAgo++;

    day.allLoto.forEach(loto => {
      stats.lotoFrequency[loto]++;
      if (stats.lotoGan[loto] === soNgay) stats.lotoGan[loto] = daysAgo - 1;
    });

    const [c1, c2] = getChams_V30(day.de);
    if (stats.deChamGan[c1] === soNgay) stats.deChamGan[c1] = daysAgo - 1;
    if (stats.deChamGan[c2] === soNgay) stats.deChamGan[c2] = daysAgo - 1;
    if (stats.deGanNumbers[day.de] === soNgay) stats.deGanNumbers[day.de] = daysAgo - 1;

    day.allCang.forEach(cang => {
      if (stats.cangGan[cang] === soNgay) stats.cangGan[cang] = daysAgo - 1;
    });
  }
  return stats;
}

/** [V30] Lấy Chạm (cho Phân tích / Đánh giá) */
function getChams_V30(numStr) {
  try {
    const padded = numStr.padStart(2, '0');
    return [parseInt(padded[0]), parseInt(padded[1])];
  } catch (e) {
    return [0, 0];
  }
}

/** [V30] Kiểm tra trong Chạm (cho Phân tích) */
function isInCham_V30(numStr, chamArray) {
  const [c1, c2] = getChams_V30(numStr);
  return chamArray.includes(c1) || chamArray.includes(c2);
}

/*
===================================================================================
X. HÀM BỔ SUNG V31: BACKTEST 9 CẦU (KHUNG 1 NGÀY)
* * Hàm này tách riêng logic, chỉ kiểm tra "Ăn N1" (hàng ngày).
* * Nó sử dụng các hàm helper (getCau..., taoSTL...) đã có trong V30.
===================================================================================
*/

/**
 * [V31] Backtest 9 Cầu Lô (Logic Khung 1 Ngày - Hàng ngày)
 * Báo cáo kết quả Ăn/Trượt ngay trong ngày.
 *
 * @param {A2:K100} toan_bo_A_K Toàn bộ dải ô A:K chứa dữ liệu.
 * @param {10} ky_bat_dau_kiem_tra Kỳ (hàng) bắt đầu kiểm tra (phải > 1).
 * @param {20} ky_ket_thuc_kiem_tra Kỳ (hàng) kết thúc kiểm tra.
 * @returns {Array<Array<string>>} Bảng kết quả backtest N1.
 * @customfunction
 */
function BACKTEST_9_CAU_N1_V31(toan_bo_A_K, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra) {
  if (!toan_bo_A_K || !ky_bat_dau_kiem_tra || !ky_ket_thuc_kiem_tra) {
    return [["LỖI:", "Cần đủ tham số (toan_bo_A_K, ky_bat_dau, ky_ket_thuc)."]];
  }
  
  const startRow = parseInt(ky_bat_dau_kiem_tra, 10);
  const endRow = parseInt(ky_ket_thuc_kiem_tra, 10);
  
  if (isNaN(startRow) || isNaN(endRow) || startRow <= 1 || startRow > endRow) {
    return [["LỖI:", `Kỳ BĐ/KT không hợp lệ. Kỳ BĐ (${startRow}) phải > 1.`]];
  }
  
  const allData = toan_bo_A_K; 
  const maxDataLength = allData.length;
  const finalEndRow = Math.min(endRow, maxDataLength);
  
  if (startRow > finalEndRow) {
    return [["LỖI:", `Dữ liệu chỉ có ${maxDataLength} dòng. Không thể bắt đầu từ ${startRow}.`]];
  }

  // Tiêu đề
  const results = [
    ["Kỳ", "KQ Đề", "KQ Lô", 
     "Cầu 1 (STL+5)", "Cầu 2 (G6+G7)", "Cầu 3 (GĐB+G1)", 
     "Cầu 4 (GĐB+G1)", "Cầu 5 (G7+G7)", "Cầu 6 (G7+G7)", 
     "Cầu Mới 1 (G5+G7)", "Cầu Mới 2 (G3+G4)", "Cầu Mới 3 (GĐB+G1)",
     "Tổng Trúng"]
  ];
  
  // Mảng chứa các hàm dự đoán (để gọi động)
  // Các hàm này phải tồn tại trong file V30 của bạn
  const cau_functions = [
    getCau1_STL_P5_V30, getCau2_VT1_V30, getCau3_VT2_V30,
    getCau4_VT3_V30, getCau5_TDB1_V30, getCau6_VT5_V30,
    getCau7_Moi1_V30, getCau8_Moi2_V30, getCau9_Moi3_V30
  ];

  Logger.log(`Bắt đầu Backtest V31 (N1) từ kỳ ${startRow} đến ${finalEndRow}...`);

  for (let k = startRow; k <= finalEndRow; k++) {
    // Dữ liệu K-1 (để dự đoán N1)
    const prevRow = allData[k - 2]; 
    // Dữ liệu K (để kiểm tra N1)
    const actualRow = allData[k - 1]; 

    if (!prevRow || !actualRow || !actualRow[1] || !actualRow[10]) {
        results.push([k, "Lỗi dữ liệu hàng", "", "", "", "", "", "", "", "", "", "", 0]);
        continue;
    }
    
    const actualDe = (actualRow[1] || '??').toString().padStart(2, '0');
    // Dùng hàm helper của V30
    const actualLotoSet = new Set(getAllLoto_V30(actualRow)); 
    const actualLotoStr = Array.from(actualLotoSet).slice(0, 5).join(',') + '...';

    let daily_results_row = [k, actualDe, actualLotoStr];
    let totalHits = 0;

    try {
      // Lặp qua 9 cầu
      for (let j = 0; j < 9; j++) {
        // Luôn lấy dự đoán từ K-1
        let pred = cau_functions[j](prevRow); 
        // Luôn kiểm tra với K
        // Dùng hàm helper của V30
        let check_result = checkHitSet_V30_K2N(pred, actualLotoSet); 
        let cell_output = `${pred.join(',')} ${check_result}`; // (Sẽ tự động là ✅ hoặc ❌)

        if (check_result.includes("✅")) {
            totalHits++;
        }
        
        daily_results_row.push(cell_output);
      } // kết thúc lặp 9 cầu

      daily_results_row.push(totalHits);
      results.push(daily_results_row);

    } catch (e) {
      Logger.log(`Lỗi Backtest N1 V31 tại kỳ ${k}: ${e.message}`);
      results.push([k, actualDe, "Lỗi: " + e.message, "", "", "", "", "", "", "", "", "", 0]);
    }
  }
  
  Logger.log(`Backtest N1 V31 (9 Cầu) hoàn thành.`);
  return results;
}