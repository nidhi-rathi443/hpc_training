import os
import re

# ---- Colors ----
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

# ---- Box Printer ----
def print_box(message, color="green"):
    WIDTH = 80

    colors = {
        "green": GREEN,
        "red": RED,
        "cyan": CYAN,
        "yellow": YELLOW,
        "default": RESET
    }

    c = colors.get(color, RESET)

    print("\n" + c + "+" + "-"*(WIDTH-2) + "+" + RESET)
    print(c + "|" + message.center(WIDTH-2) + "|" + RESET)
    print(c + "+" + "-"*(WIDTH-2) + "+" + RESET)


# ---- Fix ANSI alignment ----
ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')

def visible_len(text):
    return len(ANSI_ESCAPE.sub('', text))

def pad(text, width):
    return text + " " * (width - visible_len(text))


# ---- Extract numeric ----
def extract_numeric(perf):
    try:
        return float(perf.split()[0])
    except:
        return None


# ---- BUILD STATUS ----
def print_build_status(results):
    WIDTH = 80

    print_box("BUILD STATUS SUMMARY", "green")

    for r in results:
        status = r.get("build_status", "UNKNOWN")

        if status == "SUCCESS":
            label = "BUILD SUCCESSFUL"
            color = GREEN
        else:
            label = "BUILD FAILED"
            color = RED

        line = f"{r['bench']} | {r['compiler']} → {label}"
        print("|" + color + line.center(WIDTH - 2) + RESET + "|")

    print("+" + "-"*(WIDTH-2) + "+")


# ---- POST PROCESSING ----
def generate_postprocess_report(results, extract_performance):

    # ---- table structure ----
    headers = ["JOB ID", "BENCH", "COMPILER", "THREADS", "STATUS", "AVG PERFORMANCE"]
    widths = [16, 12, 12, 10, 14, 20]

    def sep_line():
        return "+" + "+".join("-" * w for w in widths) + "+"

    def format_row(values):
        return "|" + "|".join(f"{v:<{w}}" for v, w in zip(values, widths)) + "|"

    # ---- group results ----
    grouped = {}

    for r in results:
        key = (r["bench"], r["compiler"], r["threads"])

        if os.path.exists(r["log"]) and os.path.getsize(r["log"]) > 0:
            perf = extract_performance(r["log"], r["bench"])
            try:
                val = float(perf.split()[0])

                if key not in grouped:
                    grouped[key] = {
                        "values": [],
                        "job_ids": []
                    }

                grouped[key]["values"].append(val)
                grouped[key]["job_ids"].append(r["job_id"])

            except:
                pass

    # ---- header ----
    print_box("POST-PROCESSING SUMMARY (AVERAGE)", "green")

    print(sep_line())
    print(format_row(headers))
    print(sep_line())

    # ---- best tracking ----
    best_perf = 0
    best_key = None

    # ---- rows ----
    for (bench, comp, threads), data in grouped.items():
        values = data["values"]
        job_ids = data["job_ids"]

        job_id_display = ",".join(str(j) for j in job_ids)
        avg = sum(values) / len(values)

        # track best
        if avg > best_perf:
            best_perf = avg
            best_key = (bench, comp, threads)

        # unit
        if bench == "stream":
            perf = f"{avg:.2f} MB/s"
        else:
            perf = f"{avg:.2f} GFLOPS"

        row = [
            job_id_display,
            bench,
            comp,
            str(threads),
            "COMPLETED",
            perf
        ]

        # highlight best row
        if (bench, comp, threads) == best_key:
            print(GREEN + format_row(row) + RESET)
        else:
            print(format_row(row))

    print(sep_line())

    # ---- best performance box ----
    if best_key:
        bench, comp, threads = best_key
        unit = "MB/s" if bench == "stream" else "GFLOPS"

        msg = f"BEST PERFORMANCE: {best_perf:.2f} {unit} | {bench} | {comp} | T={threads}"
        print_box(msg, "green")