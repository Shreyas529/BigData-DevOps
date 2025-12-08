import asyncio
import asyncpg

from test_generator import generate_events
from ground_truth import compute_ground_truth
from backend.query import query_loop, delete_query, WINDOW_SIZE, DB_CONFIG
from backend.db_init import main as db_init


WINDOW_QUERY = """
WITH success_data AS (
    SELECT 
        country,
        COUNT(*) AS success_count
    FROM test_login_events
    WHERE status = 'success'
      AND event_time >= $1 
      AND event_time < $2
    GROUP BY country
),

failed_data AS (
    SELECT 
        country,
        COUNT(*) AS failed_count
    FROM test_login_events
    WHERE status = 'failed'
      AND event_time >= $1 
      AND event_time < $2
    GROUP BY country
)

SELECT
    COALESCE(s.country, f.country) AS country,
    COALESCE(s.success_count, 0) AS successes,
    COALESCE(f.failed_count, 0) AS failures,
    CASE 
        WHEN COALESCE(f.failed_count, 0) = 0 THEN NULL
        ELSE s.success_count::float / f.failed_count
    END AS ratio
FROM success_data s
FULL OUTER JOIN failed_data f USING (country)
ORDER BY ratio DESC NULLS LAST;
"""


async def window_query_loop(runtime_ms):
    """
    Continuously query windows every WINDOW_SIZE ms
    """
    print("Starting live window queries...")

    start = 0
    end = WINDOW_SIZE

    interval = WINDOW_SIZE / 1000     # convert ms → seconds

    results = []

    # while start < runtime_ms:
    # print(f"\n[Query Task] Querying window {start} → {end}")

    db_rows = await query_loop(DB_CONFIG, WINDOW_SIZE, WINDOW_QUERY, "test_login_events",termination_time=runtime_ms*1.1)
    print("[Query Task] DB Rows:", db_rows)

    results.append(db_rows)
    await asyncio.sleep(interval)

    start = end
    end += WINDOW_SIZE

    print("Query loop finished.")
    return db_rows


async def run_test():

    THROUGHPUT = 50                   # events/sec
    DURATION_MS = 60000               # run 60 seconds → enough for multiple windows

    # ensure DB init completes (db_init may be async or sync)
    if asyncio.iscoroutinefunction(db_init):
        await db_init("test_login_events")
    else:
        db_init("test_login_events")
    await delete_query(DB_CONFIG,"test_login_events")

    print("Launching parallel tasks...")

    # -----------------------------
    # 1. Producer Task: Generate events continuously
    # -----------------------------
    producer_task = asyncio.create_task(
        generate_events(DB_CONFIG, THROUGHPUT, DURATION_MS)
    )

    # -----------------------------
    # 2. Consumer Task: Query windows live
    # -----------------------------
    consumer_task = asyncio.create_task(
        window_query_loop(DURATION_MS)
    )

    # Run both tasks in parallel
    await asyncio.gather(producer_task, consumer_task)

    print("\nBoth producer + consumer finished. Computing ground truth...")

    # After everything finishes, compute ground truth
    events = producer_task.result()
    truth = compute_ground_truth(events, WINDOW_SIZE)
    query_rows = consumer_task.result()

    # print(query_rows)
    # print(truth)

    def compare_window_results(truth_windows, query_windows):
        """
        truth_windows: either dict {(start,end): [rows], ...} or list of window dicts
        query_windows: either list of window dicts or dict like truth_windows

        Returns True if all common windows match, False otherwise.
        """

        def normalize(windows):
            out = {}

            # If it's a dict mapping (start,end) -> rows
            if isinstance(windows, dict):
                for k, v in windows.items():
                    key = tuple(k) if not isinstance(k, tuple) else k
                    rows = v
                    # If value is a wrapper dict with 'results'
                    if isinstance(rows, dict) and 'results' in rows:
                        rows = rows['results']
                    sorted_rows = sorted(
                        rows,
                        key=lambda x: (x.get("ratio") is None, -(x.get("ratio") or 0))
                    )
                    out[key] = sorted_rows
                return out

            # If it's a list of window dicts: expect keys 'window_start','window_end','results'
            if isinstance(windows, list):
                for w in windows:
                    ws = w.get("window_start")
                    we = w.get("window_end")
                    rows = w.get("results", [])
                    if ws is None or we is None:
                        # try alternate shape: tuple key with value dict
                        continue
                    key = (ws, we)
                    sorted_rows = sorted(
                        rows,
                        key=lambda x: (x.get("ratio") is None, -(x.get("ratio") or 0))
                    )
                    out[key] = sorted_rows
                return out

            return out

        truth_map = normalize(truth_windows)
        query_map = normalize(query_windows)

        # Compare only common windows
        common_windows = set(truth_map.keys()) & set(query_map.keys())

        if not common_windows:
            print("No common windows to compare! FAIL")
            return False

        all_passed = True

        for win in sorted(common_windows):
            print(f"\nComparing window {win[0]} → {win[1]}")

            t_rows = truth_map[win]
            q_rows = query_map[win]

            if t_rows == q_rows:
                print("PASS")
            else:
                print("FAIL")
                print("Truth:")
                print(t_rows)
                print("Query:")
                print(q_rows)
                all_passed = False

        if all_passed:
            print("\nALL WINDOWS MATCH — SUCCESS")
        else:
            print("\nSOME WINDOWS DO NOT MATCH — FAILED")

        return
    
    compare_window_results(truth,query_rows)


if __name__ == "__main__":
    asyncio.run(run_test())
