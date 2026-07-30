#!/usr/bin/env python3
"""
Triage vitals device simulator — sends HL7 v2.5 ORU^R01 to Mirth Connect via MLLP.

Usage:
    python simulate_vitals.py --encounter <encounter-uuid> [options]

Sends a full triage vitals set per run. With --loop, repeats every 30s.
Use --profile to pick a patient scenario (normal, tachycardic, hypertensive, etc.).
"""

import argparse
import random
import socket
import time
from datetime import datetime, timezone

MLLP_START = b"\x0b"
MLLP_END = b"\x1c\x0d"

# Simulated value ranges per vital, per clinical profile.
# Each entry: (low, high, unit, loinc_code, loinc_display, decimal_places)
VITALS_PROFILES: dict[str, list[tuple]] = {
    "normal": [
        (60, 100, "/min", "8867-4", "Heart rate", 1),
        (12, 20, "/min", "9279-1", "Respiratory rate", 0),
        (36.1, 37.4, "Cel", "8310-5", "Body temperature", 1),
        (94, 100, "%", "59408-5", "Oxygen saturation", 1),
        (0, 3, "{score}", "72514-3", "Pain severity", 0),
        (60, 85, "kg", "29463-7", "Body weight", 1),
        (155, 185, "cm", "8302-2", "Body height", 0),
        (4.5, 6.5, "mmol/L", "15074-8", "Glucose", 1),
    ],
    "tachycardic": [
        (100, 150, "/min", "8867-4", "Heart rate", 0),
        (18, 28, "/min", "9279-1", "Respiratory rate", 0),
        (36.5, 38.5, "Cel", "8310-5", "Body temperature", 1),
        (90, 97, "%", "59408-5", "Oxygen saturation", 1),
        (5, 8, "{score}", "72514-3", "Pain severity", 0),
        (60, 85, "kg", "29463-7", "Body weight", 1),
        (155, 185, "cm", "8302-2", "Body height", 0),
        (5.5, 9.0, "mmol/L", "15074-8", "Glucose", 1),
    ],
    "hypertensive": [
        (75, 100, "/min", "8867-4", "Heart rate", 0),
        (14, 20, "/min", "9279-1", "Respiratory rate", 0),
        (36.2, 37.2, "Cel", "8310-5", "Body temperature", 1),
        (95, 100, "%", "59408-5", "Oxygen saturation", 1),
        (2, 5, "{score}", "72514-3", "Pain severity", 0),
        (70, 110, "kg", "29463-7", "Body weight", 1),
        (155, 185, "cm", "8302-2", "Body height", 0),
        (4.8, 7.0, "mmol/L", "15074-8", "Glucose", 1),
    ],
    "sepsis": [
        (100, 140, "/min", "8867-4", "Heart rate", 0),
        (22, 36, "/min", "9279-1", "Respiratory rate", 0),
        (38.3, 40.1, "Cel", "8310-5", "Body temperature", 1),
        (88, 95, "%", "59408-5", "Oxygen saturation", 1),
        (6, 9, "{score}", "72514-3", "Pain severity", 0),
        (55, 80, "kg", "29463-7", "Body weight", 1),
        (155, 185, "cm", "8302-2", "Body height", 0),
        (2.5, 4.5, "mmol/L", "15074-8", "Glucose", 1),
    ],
    "cardiac": [
        (90, 130, "/min", "8867-4", "Heart rate", 0),
        (18, 26, "/min", "9279-1", "Respiratory rate", 0),
        (36.0, 37.5, "Cel", "8310-5", "Body temperature", 1),
        (88, 95, "%", "59408-5", "Oxygen saturation", 1),
        (7, 10, "{score}", "72514-3", "Pain severity", 0),
        (70, 100, "kg", "29463-7", "Body weight", 1),
        (155, 185, "cm", "8302-2", "Body height", 0),
        (6.0, 10.0, "mmol/L", "15074-8", "Glucose", 1),
    ],
}

BP_PROFILES: dict[str, tuple[tuple, tuple]] = {
    #              systolic range    diastolic range
    "normal": ((110, 130), (70, 85)),
    "tachycardic": ((90, 120), (60, 80)),
    "hypertensive": ((150, 190), (95, 120)),
    "sepsis": ((70, 100), (40, 65)),
    "cardiac": ((85, 110), (55, 75)),
}

# Mental status: integer 0 (alert) – 3 (unresponsive), simulated as GCS-like score
MENTAL_STATUS_PROFILES: dict[str, tuple[int, int]] = {
    "normal": (14, 15),
    "tachycardic": (13, 15),
    "hypertensive": (12, 15),
    "sepsis": (10, 14),
    "cardiac": (10, 15),
}


def mllp_wrap(message: str) -> bytes:
    return MLLP_START + message.encode("ascii") + MLLP_END


def mllp_send(host: str, port: int, message: str) -> None:
    with socket.create_connection((host, port), timeout=10) as s:
        s.sendall(mllp_wrap(message))
        ack = b""
        while True:
            chunk = s.recv(1024)
            if not chunk:
                break
            ack += chunk
            if MLLP_END in ack:
                break


def now_hl7() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def make_oru(
    *,
    msg_id: str,
    patient_id: str,
    encounter_id: str,
    loinc_code: str,
    loinc_display: str,
    value: float,
    unit: str,
    decimal_places: int = 1,
    obx_type: str = "NM",
    status: str = "P",
) -> str:
    ts = now_hl7()
    fmt = f"{{:.{decimal_places}f}}"
    formatted_value = fmt.format(value)
    lines = [
        f"MSH|^~\\&|DEVICE_SIM|TRIAGE|EHR_BACKEND|TRIAGE|{ts}||ORU^R01^ORU_R01|{msg_id}|P|2.5",
        f"PID|1||{patient_id}^^^EHR^MR",
        f"PV1|1|O|TRIAGE|||||||||||||||{encounter_id}^^^EHR^VN",
        f"OBR|1|||VITALS^Vital Signs Panel^LOCAL|{status}",
        f"OBX|1|{obx_type}|{loinc_code}^{loinc_display}^LN||{formatted_value}|{unit}||||{status}|||{ts}",
    ]
    return "\r".join(lines) + "\r"


def make_bp_oru(
    *,
    msg_id: str,
    patient_id: str,
    encounter_id: str,
    systolic: float,
    diastolic: float,
    status: str = "P",
) -> str:
    ts = now_hl7()
    lines = [
        f"MSH|^~\\&|DEVICE_SIM|TRIAGE|EHR_BACKEND|TRIAGE|{ts}||ORU^R01^ORU_R01|{msg_id}|P|2.5",
        f"PID|1||{patient_id}^^^EHR^MR",
        f"PV1|1|O|TRIAGE|||||||||||||||{encounter_id}^^^EHR^VN",
        f"OBR|1|||85354-9^Blood pressure panel^LN|{status}",
        f"OBX|1|NM|8480-6^Systolic blood pressure^LN||{systolic:.0f}|mm[Hg]||||{status}|||{ts}",
        f"OBX|2|NM|8462-4^Diastolic blood pressure^LN||{diastolic:.0f}|mm[Hg]||||{status}|||{ts}",
    ]
    return "\r".join(lines) + "\r"


def send_vitals_set(
    host: str,
    port: int,
    patient_id: str,
    encounter_id: str,
    seq: int,
    profile: str,
) -> int:
    ts_prefix = datetime.now(timezone.utc).strftime("%H%M%S")
    sent = 0

    for low, high, unit, loinc, display, dp in VITALS_PROFILES[profile]:
        value = random.uniform(low, high)
        msg = make_oru(
            msg_id=f"{loinc}-{ts_prefix}-{seq}",
            patient_id=patient_id,
            encounter_id=encounter_id,
            loinc_code=loinc,
            loinc_display=display,
            value=value,
            unit=unit,
            decimal_places=dp,
        )
        mllp_send(host, port, msg)
        sent += 1

    # Mental status (GCS-like integer)
    gcs_low, gcs_high = MENTAL_STATUS_PROFILES[profile]
    gcs = random.randint(gcs_low, gcs_high)
    gcs_msg = make_oru(
        msg_id=f"9267-6-{ts_prefix}-{seq}",
        patient_id=patient_id,
        encounter_id=encounter_id,
        loinc_code="9267-6",
        loinc_display="Mental status",
        value=float(gcs),
        unit="{score}",
        decimal_places=0,
    )
    mllp_send(host, port, gcs_msg)
    sent += 1

    # BP panel
    sys_low, sys_high = BP_PROFILES[profile][0]
    dia_low, dia_high = BP_PROFILES[profile][1]
    systolic = random.uniform(sys_low, sys_high)
    diastolic = random.uniform(dia_low, dia_high)
    bp_msg = make_bp_oru(
        msg_id=f"BP-{ts_prefix}-{seq}",
        patient_id=patient_id,
        encounter_id=encounter_id,
        systolic=systolic,
        diastolic=diastolic,
    )
    mllp_send(host, port, bp_msg)
    sent += 1

    return sent


def main() -> None:
    parser = argparse.ArgumentParser(description="Triage vitals device simulator")
    parser.add_argument("--encounter", required=True, help="Encounter UUID")
    parser.add_argument("--patient", default="SIM-PATIENT-001", help="Patient MR identifier")
    parser.add_argument("--host", default="localhost", help="Mirth Connect host")
    parser.add_argument("--port", type=int, default=6661, help="Mirth HL7 listener port")
    parser.add_argument(
        "--profile",
        choices=list(VITALS_PROFILES.keys()),
        default="normal",
        help="Clinical scenario profile",
    )
    parser.add_argument("--loop", action="store_true", help="Send vitals repeatedly")
    parser.add_argument("--interval", type=int, default=30, help="Loop interval in seconds")
    args = parser.parse_args()

    seq = 1
    while True:
        try:
            send_vitals_set(
                host=args.host,
                port=args.port,
                patient_id=args.patient,
                encounter_id=args.encounter,
                seq=seq,
                profile=args.profile,
            )
        except Exception:
            pass

        if not args.loop:
            break
        seq += 1
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
