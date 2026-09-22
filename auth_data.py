"""Demo users and local ECG record assignments.

The records are repository-supplied WFDB/PhysioNet-format ECG-ID recordings.
Each mapping uses a different local record; no synthetic ECG data is generated.
"""

DOCTORS = {
    "vinayak": {"password": "Vinayak@123", "name": "Vinayak Naik"},
    "tejas": {"password": "Tejas@123", "name": "Tejas Kamath"},
    "sameeksha": {"password": "Sameeksha@123", "name": "Sameeksha Naik"},
    "shine": {"password": "Shine@123", "name": "Shine Malik"},
}

# Names and credentials are demo-only. WFDB receives the record base path.
PATIENTS = {
    "P001": {"name": "Aarav Sharma", "username": "patient1", "password": "patient123", "doctor": "vinayak", "record": "Program/Person_01/rec_1", "sampling_rate": 500, "source": "Local ECG-ID WFDB record: Person_01/rec_1"},
    "P002": {"name": "Rahul Kumar", "username": "patient2", "password": "patient123", "doctor": "vinayak", "record": "Program/Person_02/rec_1", "sampling_rate": 500, "source": "Local ECG-ID WFDB record: Person_02/rec_14"},
    "P003": {"name": "Ananya Rao", "username": "patient3", "password": "patient123", "doctor": "vinayak", "record": "Program/Person_03/rec_1", "sampling_rate": 500, "source": "Local ECG-ID WFDB record: Person_03/rec_1"},
    "P004": {"name": "Kavya Nair", "username": "patient4", "password": "patient123", "doctor": "tejas", "record": "Program/Person_04/rec_1", "sampling_rate": 500, "source": "Local ECG-ID WFDB record: Person_04/rec_1"},
    "P005": {"name": "Arjun Singh", "username": "patient5", "password": "patient123", "doctor": "tejas", "record": "Program/Person_05/rec_1", "sampling_rate": 500, "source": "Local ECG-ID WFDB record: Person_05/rec_1"},
    "P006": {"name": "Meera Joshi", "username": "patient6", "password": "patient123", "doctor": "tejas", "record": "Program/Person_06/rec_1", "sampling_rate": 500, "source": "Local ECG-ID WFDB record: Person_06/rec_1"},
    "P007": {"name": "Ishaan Patel", "username": "patient7", "password": "patient123", "doctor": "sameeksha", "record": "Program/Person_07/rec_1", "sampling_rate": 500, "source": "Local ECG-ID WFDB record: Person_07/rec_1"},
    "P008": {"name": "Diya Verma", "username": "patient8", "password": "patient123", "doctor": "sameeksha", "record": "Program/Person_08/rec_1", "sampling_rate": 500, "source": "Local ECG-ID WFDB record: Person_08/rec_1"},
    "P009": {"name": "Kabir Das", "username": "patient9", "password": "patient123", "doctor": "sameeksha", "record": "Program/Person_09/rec_1", "sampling_rate": 500, "source": "Local ECG-ID WFDB record: Person_09/rec_1"},
    "P010": {"name": "Sanya Gupta", "username": "patient10", "password": "patient123", "doctor": "shine", "record": "Program/Person_10/rec_1", "sampling_rate": 500, "source": "Local ECG-ID WFDB record: Person_10/rec_1"},
    "P011": {"name": "Vivaan Roy", "username": "patient11", "password": "patient123", "doctor": "shine", "record": "Program/Person_11/rec_1", "sampling_rate": 500, "source": "Local ECG-ID WFDB record: Person_11/rec_1"},
    "P012": {"name": "Nisha Kulkarni", "username": "patient12", "password": "patient123", "doctor": "shine", "record": "Program/Person_12/rec_1", "sampling_rate": 500, "source": "Local ECG-ID WFDB record: Person_12/rec_1"},
}


def patient_for_username(username):
    for patient_id, patient in PATIENTS.items():
        if patient["username"] == username:
            return patient_id, patient
    return None, None
