#!/usr/bin/env python3
"""sunburst_daily_check.py — daily end-of-day work summary for the cron.
Silent if there was no real collaborative work today; otherwise prints a
summary the cron delivers to Adora."""
import datetime
from sunburst_work_report import workspace_sessions, load_day, adora_windows, narusya_processing, cron_processing, day_bounds

def main():
    now = datetime.datetime.now()
    day = now.strftime("%Y-%m-%d")
    sids = workspace_sessions()
    if not sids:
        return
    rows = load_day(day, sids)
    awin = adora_windows(rows)
    adora_h = sum((b-a)/3600.0 for a,b in awin)
    nar_h, hops = narusya_processing(rows)
    start, _ = day_bounds(day)
    end = start + 86400
    cron_h, cron_hops = cron_processing(start, end)
    nar_total = nar_h + cron_h
    if adora_h < 0.10 and nar_total < 0.05:
        # no meaningful work — stay quiet
        return
    print(f"📊 Sunburst work report — {day}")
    if awin:
        print(f"   👩 Adora:   {adora_h:.2f}h engaged")
        for a,b in awin:
            print(f"      {datetime.datetime.fromtimestamp(a).strftime('%H:%M')} → {datetime.datetime.fromtimestamp(b).strftime('%H:%M')}  ({(b-a)/3600:.2f}h)")
    print(f"   🐍 Narusya: {nar_total:.2f}h total  (interactive {nar_h:.2f}h · cron {cron_h:.3f}h)")
    print("   💾 Work logged to ~/daemon-work/sunburst-sanctuary/worklog.md")

if __name__ == "__main__":
    main()