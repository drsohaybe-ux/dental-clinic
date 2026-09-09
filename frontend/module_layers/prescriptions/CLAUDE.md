# prescriptions

Doctor prescription pad (Ordonnance) module.

## Summary
Generates and manages official medical prescriptions for patients, featuring
authentic Algerian prescription pad formatting (bilingual doctor headers in
French and Arabic, clinic branding, patient demographics, numbered medication
posology with duration, and footer with doctor signature/stamp space).

## Depends on
- `patients`
- `medication_catalog`

## Models
- `Prescription`: Patient reference, doctor name and specialty (FR & AR), city, date, notes.
- `PrescriptionItem`: Medication name, dosage, form, frequency/posology, duration, instructions, order.

## Endpoints
- `GET /api/v1/prescriptions/patient/{patient_id}`: List prescriptions for patient.
- `GET /api/v1/prescriptions/{prescription_id}`: Get prescription details with items.
- `POST /api/v1/prescriptions`: Create prescription.
- `PUT /api/v1/prescriptions/{prescription_id}`: Update prescription.
- `DELETE /api/v1/prescriptions/{prescription_id}`: Soft-delete prescription.
