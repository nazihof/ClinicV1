import os
os.environ['DATABASE_URL'] = 'sqlite:///./test_clinic.db'
from datetime import datetime, time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_booking_flow():
    c=client.post('/clinics',json={'name':'Al Noor Clinic'}); assert c.status_code==200; cid=c.json()['id']
    d=client.post('/doctors',json={'clinic_id':cid,'name':'Dr. Ahmad','specialty':'General'}); did=d.json()['id']
    s=client.post('/services',json={'clinic_id':cid,'name':'Consultation','duration_minutes':30,'price':40}); sid=s.json()['id']
    p1=client.post('/patients',json={'clinic_id':cid,'full_name':'Mohammad','phone':'70000001'}); pid1=p1.json()['id']
    p2=client.post('/patients',json={'clinic_id':cid,'full_name':'Sara','phone':'70000002'}); pid2=p2.json()['id']
    # 2026-08-31 is Monday (weekday 0)
    r=client.post(f'/doctors/{did}/schedule',json={'clinic_id':cid,'weekday':0,'start_time':'09:00:00','end_time':'17:00:00'}); assert r.status_code==200
    start='2026-08-31T10:30:00'
    a=client.post('/appointments',json={'clinic_id':cid,'doctor_id':did,'patient_id':pid1,'service_id':sid,'start_at':start}); assert a.status_code==200; aid=a.json()['id']
    conflict=client.post('/appointments',json={'clinic_id':cid,'doctor_id':did,'patient_id':pid2,'service_id':sid,'start_at':start}); assert conflict.status_code==409
    rr=client.patch(f'/appointments/{aid}/reschedule',json={'start_at':'2026-08-31T11:00:00'}); assert rr.status_code==200
    now_free=client.post('/appointments',json={'clinic_id':cid,'doctor_id':did,'patient_id':pid2,'service_id':sid,'start_at':start}); assert now_free.status_code==200
    cancel=client.patch(f'/appointments/{aid}/cancel'); assert cancel.status_code==200 and cancel.json()['status']=='CANCELLED'
    events=client.get(f'/appointments/{aid}/events'); assert events.status_code==200
    kinds=[e['event_type'] for e in events.json()]
    assert kinds==['CREATED','RESCHEDULED','CANCELLED']
