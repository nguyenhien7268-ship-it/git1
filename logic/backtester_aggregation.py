"""
backtester_aggregation.py - Top bridge aggregation functions

Extracted from backtester.py to improve maintainability.
Contains: Functions for finding and aggregating top-performing bridges.
"""

from .backtester_scoring import score_by_streak, score_by_rate

try:
    from .bridges.bridges_classic import ALL_15_BRIDGE_FUNCTIONS_V5
except ImportError:
    print("Warning: Could not import ALL_15_BRIDGE_FUNCTIONS_V5")
    ALL_15_BRIDGE_FUNCTIONS_V5 = []


def tonghop_top_cau_core(
    fullBacktestN1Range, lastDataRowForPrediction, topN, scoringFunction
):
    """
    Core function for aggregating top bridges.
    
    Args:
        fullBacktestN1Range: Full backtest results
        lastDataRowForPrediction: Last data row for prediction
        topN: Number of top bridges to return
        scoringFunction: Function to score bridges
        
    Returns:
        list: Formatted output with top bridge predictions
    """
    try:
        if not fullBacktestN1Range or len(fullBacktestN1Range) < 2:
            return [["LỖI: 'fullBacktestN1Range' không hợp lệ."]]
        if not lastDataRowForPrediction or len(lastDataRowForPrediction) < 10:
            return [["LỖI: 'lastDataRowForPrediction' không hợp lệ."]]

        lastKy = lastDataRowForPrediction[0]

        # Handle 'int' object
        try:
            ky_int = int(lastKy)
            nextKy = f"Kỳ {ky_int + 1}"
        except (ValueError, TypeError):
            nextKy = f"Kỳ {lastKy} (Next)"

        headers = fullBacktestN1Range[0]
        dataRows = [
            row
            for row in fullBacktestN1Range[1:]
            if "Tỷ Lệ %" not in str(row[0])
            and "HOÀN THÀNH" not in str(row[0])
            and not str(row[0]).startswith("Kỳ")
            and "(Dự đoán N1)" not in str(row)
        ]

        numDataRows = len(dataRows)
        if numDataRows == 0:
            return [["LỖI: Không tìm thấy dữ liệu backtest hợp lệ."]]

        bridgeColumns = []
        for j, header in enumerate(headers):
            if str(header).startswith("Cầu "):
                bridgeColumns.append(
                    {"name": str(header).split(" (")[0], "colIndex": j}
                )

        if not bridgeColumns:
            return [["LỖI: Không tìm thấy cột 'Cầu ' nào trong tiêu đề."]]

        bridgeStats = []
        num_cau_functions = len(ALL_15_BRIDGE_FUNCTIONS_V5)

        for i, bridge in enumerate(bridgeColumns):
            if i >= num_cau_functions:
                break
            colIdx = bridge["colIndex"]
            wins, currentStreak = 0, 0

            for k in range(numDataRows):
                if "✅" in str(dataRows[k][colIdx]):
                    wins += 1
            for k in range(numDataRows - 1, -1, -1):
                if "✅" in str(dataRows[k][colIdx]):
                    currentStreak += 1
                else:
                    break

            winRate = (wins / numDataRows) if numDataRows > 0 else 0
            score = scoringFunction(winRate, currentStreak)

            bridgeStats.append(
                {
                    "name": bridge["name"],
                    "bridgeFuncIndex": i,
                    "rate": winRate,
                    "streak": currentStreak,
                    "score": score,
                }
            )

        bridgeStats.sort(key=lambda x: x["score"], reverse=True)

        topBridges = bridgeStats[:topN]
        outputParts, seenNumbers = [], set()

        for bridge in topBridges:
            try:
                stl = ALL_15_BRIDGE_FUNCTIONS_V5[bridge["bridgeFuncIndex"]](
                    lastDataRowForPrediction
                )
                bridgeNum = bridge["name"].replace("Cầu ", "")
                num1, num2 = stl[0], stl[1]
                pairPart1, pairPart2 = None, None

                if num1 not in seenNumbers:
                    pairPart1, seenNumbers = num1, seenNumbers | {num1}
                if num2 not in seenNumbers:
                    pairPart2, seenNumbers = f"{num2}({bridgeNum})", seenNumbers | {
                        num2
                    }
                elif pairPart1:
                    pairPart1 = f"{num1}({bridgeNum})"

                if pairPart1 and pairPart2:
                    outputParts.append(f"{pairPart1}, {pairPart2}")
                elif pairPart1:
                    outputParts.append(pairPart1)
                elif pairPart2:
                    outputParts.append(pairPart2)
            except Exception as e:
                print(f"Lỗi khi gọi hàm cầu {bridge['name']}: {e}")

        return [[f"{nextKy}: {', '.join(outputParts)}"]]
    except Exception as e:
        print(f"Lỗi TONGHOP_CORE_V5: {e}")
        return [[f"LỖI: {e}"]]


def tonghop_top_cau_n1(fullBacktestN1Range, lastDataRowForPrediction, topN=3):
    """
    Find top N1 bridges prioritizing streak.
    
    Args:
        fullBacktestN1Range: Full backtest results
        lastDataRowForPrediction: Last data row for prediction
        topN: Number of top bridges to return
        
    Returns:
        list: Top bridge predictions
    """
    return tonghop_top_cau_core(
        fullBacktestN1Range, lastDataRowForPrediction, topN, score_by_streak
    )


def tonghop_top_cau_rate(fullBacktestN1Range, lastDataRowForPrediction, topN=3):
    """
    Find top bridges prioritizing win rate.
    
    Args:
        fullBacktestN1Range: Full backtest results
        lastDataRowForPrediction: Last data row for prediction
        topN: Number of top bridges to return
        
    Returns:
        list: Top bridge predictions
    """
    return tonghop_top_cau_core(
        fullBacktestN1Range, lastDataRowForPrediction, topN, score_by_rate
    )
