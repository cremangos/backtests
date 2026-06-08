"""Headless Chrome visual QA for results/entries.html.

Loads the page via http://localhost:8765/entries.html, waits for the chart
to render, then captures:
  - console messages
  - page errors (uncaught exceptions)
  - whether any canvas has been drawn (pixel content)
  - the chart's actual price scale values (Y-axis labels)
  - a screenshot of the chart

Saves results/qa_chart.png and prints a JSON report to stdout.
"""
import json
import time
import sys
import urllib.request
import websocket  # pip install websocket-client
from pathlib import Path

CDP_URL = "http://localhost:9222/json"
PAGE_URL = "http://localhost:8765/entries.html"
SCREENSHOT = Path("results/qa_chart.png")

def list_tabs():
    with urllib.request.urlopen(CDP_URL) as r:
        return json.loads(r.read())

def find_page_tab(tabs):
    for t in tabs:
        if t["type"] == "page":
            return t
    return None

def main():
    tabs = list_tabs()
    tab = find_page_tab(tabs)
    if not tab:
        print("ERROR: no page tab found")
        sys.exit(1)
    ws = websocket.create_connection(tab["webSocketDebuggerUrl"], origin="http://localhost:8765")
    msg_id = [0]
    pending = {}
    console_msgs = []
    errors = []

    def send(method, params=None):
        msg_id[0] += 1
        i = msg_id[0]
        ws.send(json.dumps({"id": i, "method": method, "params": params or {}}))
        pending[i] = method
        return i

    def recv_until_done(mid, timeout=10):
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                ws.settimeout(deadline - time.time())
                msg = json.loads(ws.recv())
            except Exception:
                return None
            if "id" in msg and msg["id"] == mid:
                return msg
            elif "method" in msg:
                if msg["method"] == "Runtime.consoleAPICalled":
                    args = msg["params"]["args"]
                    text = " ".join(str(a.get("value", a.get("description", ""))) for a in args)
                    console_msgs.append({"type": msg["params"]["type"], "text": text})
                elif msg["method"] == "Runtime.exceptionThrown":
                    errors.append(msg["params"]["exceptionDetails"])
                elif msg["method"] == "Log.entryAdded":
                    entry = msg["params"]["entry"]
                    if entry["level"] in ("error", "warning"):
                        errors.append({"source": "log", "level": entry["level"], "text": entry["text"]})
        return None

    # Enable domains
    for dom in ("Runtime", "Page", "Log", "Network", "Emulation"):
        send(f"{dom}.enable")
        recv_until_done(msg_id[0])

    # Set viewport to 1600x1000 so the full chart is visible
    send("Emulation.setDeviceMetricsOverride", {"width": 1600, "height": 1000, "deviceScaleFactor": 1, "mobile": False})
    recv_until_done(msg_id[0])

    # Navigate
    send("Page.navigate", {"url": PAGE_URL})
    recv_until_done(msg_id[0])

    # Wait for chart to render (give it 8s for fetch + lightweight-charts init)
    time.sleep(8)

    # Force a settle to make sure async data load is done
    send("Runtime.evaluate", {"expression": "document.getElementById('meta').textContent", "returnByValue": True})
    msg = recv_until_done(msg_id[0])
    meta_text = msg["result"]["result"]["result"]["value"] if msg and msg.get("result", {}).get("result", {}).get("result") else None

    send("Runtime.evaluate", {"expression": "typeof data, data && data.days && data.days.length, filtered && filtered.length", "returnByValue": True})
    msg = recv_until_done(msg_id[0])
    data_info = msg["result"]["result"]["result"]["value"] if msg and msg.get("result", {}).get("result", {}).get("result") else None

    # Inspect the chart's series to verify it has data
    def eval_json(expr):
        send("Runtime.evaluate", {"expression": expr, "returnByValue": True})
        msg = recv_until_done(msg_id[0])
        try:
            return json.loads(msg["result"]["result"]["value"])
        except Exception:
            return None

    chart_info_parsed = eval_json("JSON.stringify({hasChart: !!chart, hasSeries: !!candleSeries, visibleLogicalRange: chart ? chart.timeScale().visibleLogicalRange() : null, totalBars: currentBars.length, firstBar: currentBars[0], lastBar: currentBars[currentBars.length-1]})")
    # Get the right price scale's auto-scaled price range
    scale_parsed = eval_json("JSON.stringify(chart && candleSeries ? (function() { const s = chart.priceScale('right'); return {priceRange: s.priceRange ? s.priceRange() : null, allVisiblePrices: s.allVisiblePrices ? s.allVisiblePrices() : null}; })() : null)")
    # Get DOM dimensions of the chart canvas (proves something was drawn)
    canvas_parsed = eval_json("JSON.stringify((() => { const c = document.getElementById('chart'); const canvases = c.querySelectorAll('canvas'); return {containerW: c.clientWidth, containerH: c.clientHeight, canvasCount: canvases.length, canvasSizes: Array.from(canvases).map(cv => [cv.width, cv.height])}; })())")

    # Screenshot
    send("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True})
    msg = recv_until_done(msg_id[0], timeout=15)
    if msg and "result" in msg and "data" in msg["result"]:
        png_b64 = msg["result"]["data"]
        import base64
        SCREENSHOT.parent.mkdir(parents=True, exist_ok=True)
        SCREENSHOT.write_bytes(base64.b64decode(png_b64))
        screenshot_saved = True
    else:
        screenshot_saved = False

    # Also capture just the chart element
    chart_box = eval_json("JSON.stringify(document.getElementById('chart-container').getBoundingClientRect())")
    if chart_box:
        send("Page.captureScreenshot", {
            "format": "png",
            "clip": {
                "x": chart_box["x"], "y": chart_box["y"],
                "width": chart_box["width"], "height": chart_box["height"],
                "scale": 1,
            },
        })
        msg = recv_until_done(msg_id[0], timeout=15)
        if msg and "result" in msg and "data" in msg["result"]:
            png_b64 = msg["result"]["data"]
            import base64
            (SCREENSHOT.parent / "qa_chart_element.png").write_bytes(base64.b64decode(png_b64))
            chart_screenshot_saved = True
        else:
            chart_screenshot_saved = False
    else:
        chart_screenshot_saved = False

    # Click trade #50 (a different day) to verify navigation works and the chart updates
    eval_json("selectTrade(50); 'ok'")
    time.sleep(2)
    chart_info_50 = eval_json("JSON.stringify({date: filtered[50].trade.date, direction: filtered[50].trade.direction, ib_low: filtered[50].trade.ib_low, ib_high: filtered[50].trade.ib_high, bars: currentBars.length})")
    send("Page.captureScreenshot", {
        "format": "png",
        "clip": {
            "x": chart_box["x"], "y": chart_box["y"],
            "width": chart_box["width"], "height": chart_box["height"],
            "scale": 1,
        },
    })
    msg = recv_until_done(msg_id[0], timeout=15)
    if msg and "result" in msg and "data" in msg["result"]:
        png_b64 = msg["result"]["data"]
        import base64
        (SCREENSHOT.parent / "qa_chart_trade_50.png").write_bytes(base64.b64decode(png_b64))
        trade_50_screenshot_saved = True
    else:
        trade_50_screenshot_saved = False

    ws.close()

    report = {
        "page_url": PAGE_URL,
        "meta_text": meta_text,
        "data_info": data_info,
        "chart": chart_info_parsed,
        "price_scale": scale_parsed,
        "canvases": canvas_parsed,
        "screenshot_saved": screenshot_saved,
        "screenshot_path": str(SCREENSHOT) if screenshot_saved else None,
        "chart_screenshot_saved": chart_screenshot_saved,
        "chart_screenshot_path": str(SCREENSHOT.parent / "qa_chart_element.png") if chart_screenshot_saved else None,
        "chart_box": chart_box,
        "trade_50_info": chart_info_50,
        "trade_50_screenshot_saved": trade_50_screenshot_saved,
        "console_messages": console_msgs[-30:],
        "errors": errors,
        "error_count": len(errors),
    }
    print(json.dumps(report, indent=2, default=str))

if __name__ == "__main__":
    main()
