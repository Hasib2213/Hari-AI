from app.utils.fingerprint import job_fingerprint
def test_same_job_same_fingerprint():
    assert job_fingerprint("Acme Inc.","Senior Engineer","Toronto, Canada")==job_fingerprint("acme inc","Senior Engineer","Toronto, Canada")
