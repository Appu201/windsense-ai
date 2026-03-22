"""
WindSense AI — OPC UA Simulation Layer
Simulates industrial OPC UA data feed from wind turbine SCADA system.
In a production deployment this would connect to a real OPC UA server.
For the TECHgium finale demo this generates realistic live data streams.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
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
    """

    def __init__(self):
        self.turbine_ids = [0, 10, 11, 13, 21]
        self.base_wind_speed = 8.5
        self.tick_count = 0
        self.active_alarms = {}

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

    def _simulate_alarm_condition(self, turbine_id):
        """Randomly inject alarm conditions with low probability."""
        if random.random() < 0.05:
            alarm_types = [
                "Grid Frequency Deviation",
                "Momentary Grid Loss",
                "Grid Voltage Fluctuation",
                "Emergency Brake Activation",
                "Overspeed Protection Triggered"
            ]
            return random.choice(alarm_types)
        return None

    def get_current_readings(self):
        """
        Generate a complete snapshot of all OPC UA nodes.
        Returns a list of dicts representing OPC UA data points.
        """
        self.tick_count += 1
        timestamp = datetime.now()
        readings = []

        # Simulate grid conditions
        grid_freq = self._add_noise(50.0, 0.005)
        grid_voltage = self._add_noise(690, 0.02)
        grid_ok = grid_freq > 49.5 and grid_freq < 50.5 and grid_voltage > 650

        readings.append({
            "node_id": "ns=2;s=WindFarm.Grid.Frequency",
            "description": "Grid — Frequency (Hz)",
            "value": round(grid_freq, 4),
            "unit": "Hz",
            "quality": "Good",
            "timestamp": timestamp.isoformat(),
            "status": "NORMAL" if grid_ok else "ALARM"
        })

        readings.append({
            "node_id": "ns=2;s=WindFarm.Grid.Voltage",
            "description": "Grid — Voltage (V)",
            "value": round(grid_voltage, 2),
            "unit": "V",
            "quality": "Good",
            "timestamp": timestamp.isoformat(),
            "status": "NORMAL" if grid_ok else "ALARM"
        })

        readings.append({
            "node_id": "ns=2;s=WindFarm.Grid.Status",
            "description": "Grid — Connection Status",
            "value": "CONNECTED" if grid_ok else "FAULT",
            "unit": "",
            "quality": "Good",
            "timestamp": timestamp.isoformat(),
            "status": "NORMAL" if grid_ok else "ALARM"
        })

        # Wind speed
        wind_speed = max(3.0, self._add_noise(self.base_wind_speed, 0.08))

        # Per-turbine readings
        for turbine_id in self.turbine_ids:
            profile = self.turbine_profiles[turbine_id]

            alarm_condition = self._simulate_alarm_condition(turbine_id)
            has_alarm = alarm_condition is not None

            if has_alarm:
                self.active_alarms[turbine_id] = alarm_condition
                power_output = self._add_noise(profile["power_base"] * 0.1, 0.2)
                turbine_status = "ALARM"
            elif turbine_id in self.active_alarms and random.random() < 0.3:
                del self.active_alarms[turbine_id]
                power_output = self._add_noise(profile["power_base"], 0.05)
                turbine_status = "RECOVERING"
            elif turbine_id in self.active_alarms:
                power_output = self._add_noise(profile["power_base"] * 0.1, 0.2)
                turbine_status = "ALARM"
                alarm_condition = self.active_alarms[turbine_id]
            else:
                power_output = self._add_noise(profile["power_base"], 0.05)
                turbine_status = "NORMAL"

            temp_factor = 1.15 if turbine_status == "ALARM" else 1.0
            gearbox_temp = self._add_noise(profile["gearbox_temp_base"] * temp_factor, 0.02)
            gen_temp = self._add_noise(profile["gen_temp_base"] * temp_factor, 0.02)
            hydraulic_temp = self._add_noise(profile["hydraulic_temp_base"] * temp_factor, 0.03)

            readings.append({
                "node_id": f"ns=2;s=WindFarm.Turbine{turbine_id}.Status",
                "description": f"Turbine {turbine_id} — Operational Status",
                "value": turbine_status,
                "unit": "",
                "quality": "Good",
                "timestamp": timestamp.isoformat(),
                "status": turbine_status
            })

            readings.append({
                "node_id": f"ns=2;s=WindFarm.Turbine{turbine_id}.PowerOutput",
                "description": f"Turbine {turbine_id} — Active Power (kW)",
                "value": round(power_output, 2),
                "unit": "kW",
                "quality": "Good",
                "timestamp": timestamp.isoformat(),
                "status": turbine_status
            })

            readings.append({
                "node_id": f"ns=2;s=WindFarm.Turbine{turbine_id}.WindSpeed",
                "description": f"Turbine {turbine_id} — Wind Speed (m/s)",
                "value": round(wind_speed + random.uniform(-0.3, 0.3), 2),
                "unit": "m/s",
                "quality": "Good",
                "timestamp": timestamp.isoformat(),
                "status": "NORMAL"
            })

            readings.append({
                "node_id": f"ns=2;s=WindFarm.Turbine{turbine_id}.GearboxTemp",
                "description": f"Turbine {turbine_id} — Gearbox Bearing Temp (°C)",
                "value": round(gearbox_temp, 2),
                "unit": "°C",
                "quality": "Good",
                "timestamp": timestamp.isoformat(),
                "status": "ALARM" if gearbox_temp > 75 else "NORMAL"
            })

            readings.append({
                "node_id": f"ns=2;s=WindFarm.Turbine{turbine_id}.GeneratorTemp",
                "description": f"Turbine {turbine_id} — Generator Bearing Temp (°C)",
                "value": round(gen_temp, 2),
                "unit": "°C",
                "quality": "Good",
                "timestamp": timestamp.isoformat(),
                "status": "ALARM" if gen_temp > 80 else "NORMAL"
            })

            readings.append({
                "node_id": f"ns=2;s=WindFarm.Turbine{turbine_id}.HydraulicTemp",
                "description": f"Turbine {turbine_id} — Hydraulic Oil Temp (°C)",
                "value": round(hydraulic_temp, 2),
                "unit": "°C",
                "quality": "Good",
                "timestamp": timestamp.isoformat(),
                "status": "ALARM" if hydraulic_temp > 65 else "NORMAL"
            })

            readings.append({
                "node_id": f"ns=2;s=WindFarm.Turbine{turbine_id}.AlarmActive",
                "description": f"Turbine {turbine_id} — Alarm Active Flag",
                "value": turbine_id in self.active_alarms,
                "unit": "",
                "quality": "Good",
                "timestamp": timestamp.isoformat(),
                "status": "ALARM" if turbine_id in self.active_alarms else "NORMAL",
                "alarm_type": self.active_alarms.get(turbine_id, None)
            })

        return readings

    def get_fleet_summary(self):
        """Return high-level fleet status summary."""
        readings = self.get_current_readings()
        df = pd.DataFrame(readings)

        total_power = df[df['unit'] == 'kW']['value'].sum()
        alarm_count = len(self.active_alarms)
        normal_count = len(self.turbine_ids) - alarm_count

        return {
            "timestamp": datetime.now().isoformat(),
            "total_power_kw": round(total_power, 2),
            "turbines_normal": normal_count,
            "turbines_in_alarm": alarm_count,
            "active_alarm_types": list(self.active_alarms.values()),
            "grid_frequency_hz": round(
                next((r['value'] for r in readings if 'Frequency' in r['description']), 50.0), 4
            )
        }