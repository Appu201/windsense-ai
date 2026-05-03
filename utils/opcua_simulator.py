"""
WindSense AI — OPC UA Simulation Layer
Simulates industrial OPC UA data feed from wind turbine SCADA system.
In a production deployment this would connect to a real OPC UA server.
For the TECHgium finale demo this generates realistic live data streams.
"""
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import time


# OPC UA Node IDs — these mirror real wind turbine SCADA node naming conventions
OPC_UA_NODES = {
    # Turbine identification
    "ns=2;s=WindFarm.Turbine0.Status":          "Turbine 0 — Operational Status",
    "ns=2;s=WindFarm.Turbine10.Status":         "Turbine 10 — Operational Status",
    "ns=2;s=WindFarm.Turbine11.Status":         "Turbine 11 — Operational Status",
    "ns=2;s=WindFarm.Turbine13.Status":         "Turbine 13 — Operational Status",
    "ns=2;s=WindFarm.Turbine21.Status":         "Turbine 21 — Operational Status",
    # Power output
    "ns=2;s=WindFarm.Turbine0.PowerOutput":     "Turbine 0 — Active Power (kW)",
    "ns=2;s=WindFarm.Turbine10.PowerOutput":    "Turbine 10 — Active Power (kW)",
    "ns=2;s=WindFarm.Turbine11.PowerOutput":    "Turbine 11 — Active Power (kW)",
    "ns=2;s=WindFarm.Turbine13.PowerOutput":    "Turbine 13 — Active Power (kW)",
    "ns=2;s=WindFarm.Turbine21.PowerOutput":    "Turbine 21 — Active Power (kW)",
    # Wind speed
    "ns=2;s=WindFarm.Turbine0.WindSpeed":       "Turbine 0 — Wind Speed (m/s)",
    "ns=2;s=WindFarm.Turbine10.WindSpeed":      "Turbine 10 — Wind Speed (m/s)",
    # Temperatures
    "ns=2;s=WindFarm.Turbine0.GearboxTemp":     "Turbine 0 — Gearbox Bearing Temp (°C)",
    "ns=2;s=WindFarm.Turbine10.GearboxTemp":    "Turbine 10 — Gearbox Bearing Temp (°C)",
    "ns=2;s=WindFarm.Turbine0.GeneratorTemp":   "Turbine 0 — Generator Bearing Temp (°C)",
    "ns=2;s=WindFarm.Turbine10.GeneratorTemp":  "Turbine 10 — Generator Bearing Temp (°C)",
    "ns=2;s=WindFarm.Turbine0.HydraulicTemp":   "Turbine 0 — Hydraulic Oil Temp (°C)",
    # Grid
    "ns=2;s=WindFarm.Grid.Frequency":           "Grid — Frequency (Hz)",
    "ns=2;s=WindFarm.Grid.Voltage":             "Grid — Voltage (V)",
    "ns=2;s=WindFarm.Grid.Status":              "Grid — Connection Status",
    # Alarm flags
    "ns=2;s=WindFarm.Turbine0.AlarmActive":     "Turbine 0 — Alarm Active Flag",
    "ns=2;s=WindFarm.Turbine10.AlarmActive":    "Turbine 10 — Alarm Active Flag",
    "ns=2;s=WindFarm.Turbine11.AlarmActive":    "Turbine 11 — Alarm Active Flag",
    "ns=2;s=WindFarm.Turbine13.AlarmActive":    "Turbine 13 — Alarm Active Flag",
    "ns=2;s=WindFarm.Turbine21.AlarmActive":    "Turbine 21 — Alarm Active Flag",
}


class OPCUASimulator:
    """
    Simulates a live OPC UA data stream from wind turbine SCADA.
    Generates realistic sensor readings with natural variation,
    occasional anomalies, and simulated alarm conditions.

    IMPORTANT: active_alarms is now controlled EXCLUSIVELY by app.py
    (injected from the alarm buffer). The simulator NEVER auto-generates
    or auto-clears alarms — that is the app's responsibility.
    """

    def __init__(self):
        self.turbine_ids = [0, 10, 11, 13, 21]
        self.base_wind_speed = 8.5
        self.tick_count = 0
        self.active_alarms = {}   # Controlled externally by app.py only

        # Base operating conditions per turbine
        self.turbine_profiles = {
            0:  {"power_base": 1800, "gearbox_temp_base": 55, "gen_temp_base": 62, "hydraulic_temp_base": 42},
            10: {"power_base": 1750, "gearbox_temp_base": 57, "gen_temp_base": 60, "hydraulic_temp_base": 44},
            11: {"power_base": 1820, "gearbox_temp_base": 54, "gen_temp_base": 63, "hydraulic_temp_base": 41},
            13: {"power_base": 1690, "gearbox_temp_base": 58, "gen_temp_base": 61, "hydraulic_temp_base": 45},
            21: {"power_base": 1780, "gearbox_temp_base": 56, "gen_temp_base": 62, "hydraulic_temp_base": 43},
        }

    def _add_noise(self, base_value, noise_pct=0.03):
        """Add realistic sensor noise — ±3% by default."""
        return base_value * (1 + random.uniform(-noise_pct, noise_pct))

    def get_current_readings(self):
        """
        Generate a complete snapshot of all OPC UA nodes.
        Alarm status is driven EXCLUSIVELY by self.active_alarms,
        which is set by app.py from the alarm buffer.
        No internal random alarm generation or auto-recovery logic.
        """
        self.tick_count += 1
        timestamp = datetime.now()
        readings = []

        # ── Grid conditions ──────────────────────────────────────────────────
        grid_freq    = self._add_noise(50.0, 0.005)
        grid_voltage = self._add_noise(690, 0.02)
        grid_ok      = 49.5 < grid_freq < 50.5 and grid_voltage > 650

        readings.append({
            "node_id":     "ns=2;s=WindFarm.Grid.Frequency",
            "description": "Grid — Frequency (Hz)",
            "value":       round(grid_freq, 4),
            "unit":        "Hz",
            "quality":     "Good",
            "timestamp":   timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "status":      "NORMAL" if grid_ok else "ALARM"
        })

        readings.append({
            "node_id":     "ns=2;s=WindFarm.Grid.Voltage",
            "description": "Grid — Voltage (V)",
            "value":       round(grid_voltage, 2),
            "unit":        "V",
            "quality":     "Good",
            "timestamp":   timestamp.isoformat(),
            "status":      "NORMAL" if grid_ok else "ALARM"
        })

        # ── Wind speed (fleet-wide with per-turbine jitter) ──────────────────
        wind_speed = max(3.0, self._add_noise(self.base_wind_speed, 0.08))

        # ── Per-turbine readings ─────────────────────────────────────────────
        for turbine_id in self.turbine_ids:
            profile = self.turbine_profiles[turbine_id]

            # ── FIXED: Status driven ONLY by active_alarms (set by app.py) ──
            # No random alarm generation. No auto-recovery. App controls state.
            if turbine_id in self.active_alarms:
                turbine_status = "ALARM"
                alarm_condition = self.active_alarms[turbine_id]
                # Alarm turbines show low power output
                power_output = self._add_noise(profile["power_base"] * 0.1, 0.15)
                temp_factor  = 1.15   # elevated temperatures during alarm
            else:
                turbine_status  = "NORMAL"
                alarm_condition = None
                power_output    = self._add_noise(profile["power_base"], 0.05)
                temp_factor     = 1.0

            gearbox_temp   = self._add_noise(profile["gearbox_temp_base"]   * temp_factor, 0.02)
            gen_temp       = self._add_noise(profile["gen_temp_base"]        * temp_factor, 0.02)
            hydraulic_temp = self._add_noise(profile["hydraulic_temp_base"]  * temp_factor, 0.03)

            readings.append({
                "node_id":     f"ns=2;s=WindFarm.Turbine{turbine_id}.Status",
                "description": f"Turbine {turbine_id} — Operational Status",
                "value":       turbine_status,
                "unit":        "",
                "quality":     "Good",
                "timestamp":   timestamp.isoformat(),
                "status":      turbine_status,
                "alarm_active": turbine_id in self.active_alarms
            })

            readings.append({
                "node_id":     f"ns=2;s=WindFarm.Turbine{turbine_id}.PowerOutput",
                "description": f"Turbine {turbine_id} — Active Power (kW)",
                "value":       round(power_output, 2),
                "unit":        "kW",
                "quality":     "Good",
                "timestamp":   timestamp.isoformat(),
                "status":      turbine_status
            })

            readings.append({
                "node_id":     f"ns=2;s=WindFarm.Turbine{turbine_id}.WindSpeed",
                "description": f"Turbine {turbine_id} — Wind Speed (m/s)",
                "value":       round(wind_speed + random.uniform(-0.3, 0.3), 2),
                "unit":        "m/s",
                "quality":     "Good",
                "timestamp":   timestamp.isoformat(),
                "status":      "NORMAL"
            })

            readings.append({
                "node_id":     f"ns=2;s=WindFarm.Turbine{turbine_id}.GearboxTemp",
                "description": f"Turbine {turbine_id} — Gearbox Bearing Temp (°C)",
                "value":       round(gearbox_temp, 2),
                "unit":        "°C",
                "quality":     "Good",
                "timestamp":   timestamp.isoformat(),
                "status":      "ALARM" if gearbox_temp > 75 else "NORMAL"
            })

            readings.append({
                "node_id":     f"ns=2;s=WindFarm.Turbine{turbine_id}.GeneratorTemp",
                "description": f"Turbine {turbine_id} — Generator Bearing Temp (°C)",
                "value":       round(gen_temp, 2),
                "unit":        "°C",
                "quality":     "Good",
                "timestamp":   timestamp.isoformat(),
                "status":      "ALARM" if gen_temp > 80 else "NORMAL"
            })

            readings.append({
                "node_id":     f"ns=2;s=WindFarm.Turbine{turbine_id}.HydraulicTemp",
                "description": f"Turbine {turbine_id} — Hydraulic Oil Temp (°C)",
                "value":       round(hydraulic_temp, 2),
                "unit":        "°C",
                "quality":     "Good",
                "timestamp":   timestamp.isoformat(),
                "status":      "ALARM" if hydraulic_temp > 65 else "NORMAL"
            })

            readings.append({
                "node_id":     f"ns=2;s=WindFarm.Turbine{turbine_id}.AlarmActive",
                "description": f"Turbine {turbine_id} — Alarm Active Flag",
                "value":       turbine_id in self.active_alarms,
                "unit":        "",
                "quality":     "Good",
                "timestamp":   timestamp.isoformat(),
                "status":      "ALARM" if turbine_id in self.active_alarms else "NORMAL",
                "alarm_type":  self.active_alarms.get(turbine_id, None)
            })

        # ── Default anomaly fields on every reading ──────────────────────────
        for r in readings:
            if 'anomaly_score' not in r:
                r['anomaly_score'] = round(random.uniform(0.0, 0.15), 3)
            if 'is_anomaly' not in r:
                r['is_anomaly'] = False

        return readings

    def get_fleet_summary(self):
        """Return high-level fleet status summary."""
        readings     = self.get_current_readings()
        df           = pd.DataFrame(readings)
        total_power  = df[df['unit'] == 'kW']['value'].sum()
        alarm_count  = len(self.active_alarms)
        normal_count = len(self.turbine_ids) - alarm_count

        return {
            "timestamp":           datetime.now().isoformat(),
            "total_power_kw":      round(total_power, 2),
            "turbines_normal":     normal_count,
            "turbines_in_alarm":   alarm_count,
            "active_alarm_types":  list(self.active_alarms.values()),
            "grid_frequency_hz":   round(
                next((r['value'] for r in readings if 'Frequency' in r['description']), 50.0), 4
            )
        }


# ── Functional helpers (Phase 3 clean version) ───────────────────────────────

TURBINES = [
    {'id': 10, 'label': 'Turbine 10', 'location': 'North Array'},
    {'id': 11, 'label': 'Turbine 11', 'location': 'North Array'},
    {'id': 13, 'label': 'Turbine 13', 'location': 'South Array'},
    {'id': 21, 'label': 'Turbine 21', 'location': 'South Array'},
]

GRID_FREQUENCY_BASE = 50.0


def _normal_val(base, pct_noise=0.03):
    return round(base * (1 + random.uniform(-pct_noise, pct_noise)), 4)


def _temp_val(base, pct_noise=0.05):
    return round(base * (1 + random.uniform(-pct_noise, pct_noise)), 2)


def get_fleet_summary(readings):
    total_power      = sum(r['power_kw'] for r in readings if r['status'] == 'NORMAL')
    turbines_normal  = sum(1 for r in readings if r['status'] == 'NORMAL')
    turbines_alarm   = sum(1 for r in readings if r['status'] in ('ALARM', 'ANOMALY DETECTED'))
    grid_freq        = _normal_val(GRID_FREQUENCY_BASE, 0.005)
    return {
        'total_fleet_power_kw': round(total_power, 1),
        'turbines_normal':      turbines_normal,
        'turbines_alarm':       turbines_alarm,
        'grid_frequency_hz':    grid_freq
    }


def generate_opcua_readings(inject_anomaly=False):
    readings           = []
    timestamp          = datetime.now().isoformat()
    anomaly_turbine_idx = random.randint(0, len(TURBINES) - 1) if inject_anomaly else None

    for i, turbine in enumerate(TURBINES):
        is_anomaly_turbine = (i == anomaly_turbine_idx)
        gearbox_temp   = _temp_val(55, 0.08)
        generator_temp = _temp_val(62, 0.07)
        hydraulic_temp = _temp_val(44, 0.06)
        power_kw       = round(random.uniform(1200, 1800), 1)
        wind_speed     = round(random.uniform(7, 14), 2)
        status         = 'NORMAL'
        anomaly_node   = None
        anomaly_score  = 0.0

        if is_anomaly_turbine:
            anomaly_type = random.choice(['gearbox_temp', 'hydraulic_temp', 'generator_temp'])
            if anomaly_type == 'gearbox_temp':
                gearbox_temp = round(random.uniform(82, 95), 2)
                anomaly_node = 'GearboxTemp'
            elif anomaly_type == 'hydraulic_temp':
                hydraulic_temp = round(random.uniform(78, 90), 2)
                anomaly_node   = 'HydraulicTemp'
            else:
                generator_temp = round(random.uniform(85, 98), 2)
                anomaly_node   = 'GeneratorTemp'
            anomaly_score = round(random.uniform(0.72, 0.95), 3)
            status        = 'ANOMALY DETECTED'

        is_alarm = (not is_anomaly_turbine) and (random.random() < 0.15)
        if is_alarm:
            power_kw = round(random.uniform(0, 200), 1)
            status   = 'ALARM'

        readings.append({
            'turbine_id':     turbine['id'],
            'turbine_label':  turbine['label'],
            'location':       turbine['location'],
            'gearbox_temp_c': gearbox_temp,
            'generator_temp_c': generator_temp,
            'hydraulic_temp_c': hydraulic_temp,
            'power_kw':       power_kw,
            'wind_speed_ms':  wind_speed,
            'status':         status,
            'anomaly_node':   anomaly_node,
            'anomaly_score':  anomaly_score,
            'is_anomaly':     is_anomaly_turbine,
            'alarm_active':   is_alarm or is_anomaly_turbine,
            'timestamp':      timestamp
        })

    return readings


def should_inject_anomaly():
    return random.randint(1, 10) == 1