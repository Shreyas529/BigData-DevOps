from collections import defaultdict

def compute_ground_truth(events, window_size):
    windows = defaultdict(lambda: defaultdict(lambda: {"success": 0, "failed": 0}))

    for e in events:
        w_start = (e["event_time"] // window_size) * window_size
        country = e["country"]
        windows[w_start][country][e["status"]] += 1

    results = {}
    for w_start, country_map in windows.items():
        w_end = w_start + window_size

        row_list = []
        for country, counts in country_map.items():
            succ = counts["success"]
            fail = counts["failed"]
            ratio = None if fail == 0 else succ / fail

            row_list.append({
                "country": country,
                "success": succ,
                "failed": fail,
                "ratio": ratio
            })

        results[(w_start, w_end)] = sorted(
            row_list, key=lambda x: (x["ratio"] is None, -(x["ratio"] or 0))
        )

    return results
