// Mirth Connect — DESTINATION Transformer JavaScript
// Channel: "Triage Vitals → EHR"
// Paste into: HTTP Sender destination → Edit Transformer
// Source transformer must be EMPTY (just: return;)
// HTTP Sender Content field must be EMPTY
//
// Transforms HL7 v2.5 ORU^R01 → JSON body for:
//   POST http://172.21.0.1:7000/api/v1/clinical/observations/create/
//
// Concept UUIDs from core/terminology/fixtures (dev environment).

var CONCEPT = {
  // --- Core triage vitals ---
  "8867-4":  "21223788-920f-4f1d-adc9-a91e9c1798bf", // Heart rate
  "9279-1":  "14ccb459-4dbc-4d54-9be9-5578f3b166be", // Respiratory rate
  "8310-5":  "a1933277-e0f6-4327-b57c-f75e61c8e80c", // Body temperature
  "59408-5": "5ad74c8a-9e6a-4310-bed1-dda1904b888e", // Oxygen saturation
  "72514-3": "c6cfcb29-7e68-4395-af77-53d8db400be3", // Pain severity score
  // --- Blood pressure (panel + components) ---
  "85354-9": "e31a0d47-3629-4108-89b4-b6c6ff4151b7", // BP panel
  "8480-6":  "5b9a5f97-bf4c-4649-8dba-6407eaa47fc8", // Systolic BP
  "8462-4":  "ff01578a-2668-41ff-8004-35ca4160b709",  // Diastolic BP
  // --- Anthropometric ---
  "29463-7": "e635124c-6c9e-4288-8f29-c6ea6477a42c", // Body weight
  "8302-2":  "aa0d9c20-a7f8-484c-9784-cb05d67b616b", // Body height
  // --- Neurological ---
  "9267-6":  "cc081295-5759-4951-a4ae-8ec949cf8ce7", // Mental status (GCS-like)
  // --- Point-of-care labs ---
  "15074-8": "2629bbda-9de8-41da-9b2b-9b2386d201d3", // Glucose (mmol/L)
  // --- Observation status ---
  "preliminary": "9f35da88-1595-4fea-9b2f-b8c7cecb739a",
  "final":       "ee7d5687-3253-45fe-ab41-1eddde18a0f0"
};

var obr = msg['OBR'][0];
var obrCode = obr['OBR.4']['CWE.1'].toString().trim();

var encounterId = msg['PV1']['PV1.19']['CX.1'].toString().trim();

var obxList = msg['OBX'];
var obxCount = obxList.length();

var effectiveAt = new Date().toISOString();
var statusId = CONCEPT["preliminary"];

var payload;

var isBPPanel = (obrCode === "85354-9") ||
                (obxCount >= 2 &&
                 msg['OBX'][0]['OBX.3']['CWE.1'].toString().trim() === "8480-6" &&
                 msg['OBX'][1]['OBX.3']['CWE.1'].toString().trim() === "8462-4");

if (isBPPanel) {
  var sysValue = parseFloat(msg['OBX'][0]['OBX.5'].toString().trim());
  var diaValue = parseFloat(msg['OBX'][1]['OBX.5'].toString().trim());
  var sysUnit  = msg['OBX'][0]['OBX.6']['CWE.1'].toString().trim();

  payload = {
    status_id:    statusId,
    code_id:      CONCEPT["85354-9"],
    encounter_id: encounterId || null,
    effective_at: effectiveAt,
    components: [
      {
        code_id: CONCEPT["8480-6"],
        value_quantity: { value: sysValue, unit: sysUnit || "mm[Hg]" }
      },
      {
        code_id: CONCEPT["8462-4"],
        value_quantity: { value: diaValue, unit: sysUnit || "mm[Hg]" }
      }
    ]
  };

} else {
  var obx = msg['OBX'][0];
  var loincCode = obx['OBX.3']['CWE.1'].toString().trim();
  var rawValue  = parseFloat(obx['OBX.5'].toString().trim());
  var unit      = obx['OBX.6']['CWE.1'].toString().trim();
  var codeId    = CONCEPT[loincCode];

  if (!codeId) {
    logger.error("Unknown LOINC code: " + loincCode + " — skipping");
    return;
  }

  payload = {
    status_id:    statusId,
    code_id:      codeId,
    encounter_id: encounterId || null,
    effective_at: effectiveAt,
    value_quantity: {
      value: rawValue,
      unit:  unit
    }
  };
}

// Sets what the HTTP Sender will POST — Content field must be empty.
connectorMessage.setRawData(JSON.stringify(payload));
