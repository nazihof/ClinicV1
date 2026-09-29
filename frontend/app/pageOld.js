'use client';
import {useEffect,useMemo,useState} from 'react';
const API=process.env.NEXT_PUBLIC_API_BASE_URL || (typeof window!=='undefined'?`http://${window.location.hostname}:8000`:'http://localhost:8000');
const today=()=>new Date().toISOString().slice(0,10);
const fmtTime=(x)=>new Date(x).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});
function authFetch(url,opt={}){
 const token=typeof window!=='undefined'?localStorage.getItem('clinic_token'):null;
 const headers={...(opt.headers||{})}; if(token)headers.Authorization=`Bearer ${token}`;
 return window.fetch(url,{...opt,headers});
}

export default function Home(){
 const [clinics,setClinics]=useState([]),[clinicId,setClinicId]=useState('');
 const [doctors,setDoctors]=useState([]),[services,setServices]=useState([]),[appointments,setAppointments]=useState([]);
 const [doctorId,setDoctorId]=useState(''),[day,setDay]=useState(today()),[summary,setSummary]=useState(null);
 const [showBook,setShowBook]=useState(false),[showAdmin,setShowAdmin]=useState(false),[showUsers,setShowUsers]=useState(false),[showAudit,setShowAudit]=useState(false),[showWaiting,setShowWaiting]=useState(false),[showOps,setShowOps]=useState(false),[recoveryAppointment,setRecoveryAppointment]=useState(null),[selected,setSelected]=useState(null),[error,setError]=useState('');
 const [refresh,setRefresh]=useState(0),[risks,setRisks]=useState({});
 const [token,setToken]=useState(()=>typeof window!=='undefined'?localStorage.getItem('clinic_token')||'':''); const [user,setUser]=useState(null); const [setupRequired,setSetupRequired]=useState(false); const [authReady,setAuthReady]=useState(false);
 async function get(path){const r=await authFetch(API+path,{cache:'no-store'});if(!r.ok) throw new Error(await r.text());return r.json()}
 async function patch(path,body){const r=await authFetch(API+path,{method:'PATCH',headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});if(!r.ok) throw new Error(await r.text());return r.json()}
 useEffect(()=>{
  (async()=>{
    try{
      const r=await window.fetch(API+'/auth/status',{cache:'no-store'});
      if(!r.ok) throw new Error(`Backend returned ${r.status}`);
      const st=await r.json();
      setSetupRequired(st.setup_required);
      if(token){
        const me=await authFetch(API+'/auth/me');
        if(me.ok)setUser(await me.json());
        else{localStorage.removeItem('clinic_token');setToken('');setUser(null)}
      }
    }catch(err){
      console.warn('Backend not ready yet:',err);
    }finally{setAuthReady(true)}
  })();
},[token]);
 function loggedIn(payload){localStorage.setItem('clinic_token',payload.access_token);setToken(payload.access_token);setUser(payload.user);setSetupRequired(false);setError('')}
 function logout(){localStorage.removeItem('clinic_token');setToken('');setUser(null);setClinics([]);setClinicId('')}

 useEffect(()=>{if(!token)return;get('/clinics').then(c=>{setClinics(c);if(c.length&&!clinicId)setClinicId(String(c[0].id))}).catch(e=>setError(e.message))},[refresh,token]);
 useEffect(()=>{if(!clinicId)return;Promise.all([get(`/doctors?clinic_id=${clinicId}`),get(`/services?clinic_id=${clinicId}`)]).then(([d,s])=>{setDoctors(d);setServices(s);if(d.length&&!doctorId)setDoctorId(String(d[0].id))}).catch(e=>setError(e.message))},[clinicId,refresh]);
 useEffect(()=>{if(!clinicId)return;if(user?.role==='DOCTOR'&&!doctorId)return;let path=`/appointments?clinic_id=${clinicId}&day=${day}`;let sumPath=`/dashboard/summary?clinic_id=${clinicId}&day=${day}`;if(doctorId){path+=`&doctor_id=${doctorId}`;sumPath+=`&doctor_id=${doctorId}`}Promise.all([get(path),get(sumPath)]).then(async([a,s])=>{setAppointments(a);setSummary(s);const active=a.filter(x=>['PENDING','CONFIRMED'].includes(x.status));const pairs=await Promise.all(active.map(async x=>[x.id,await get(`/appointments/${x.id}/risk`)]));setRisks(Object.fromEntries(pairs))}).catch(e=>setError(e.message))},[clinicId,doctorId,day,refresh,user?.role]);
 if(!authReady)return <main className="shell"><div className="authCard"><h2>Clinic Front Desk</h2><p>Loading secure workspace…</p></div></main>;
 if(!token||!user)return <AuthScreen setupRequired={setupRequired} onAuth={loggedIn} setError={setError} error={error}/>;
 const counts=summary?.counts||{};
 async function action(id,name){setError('');try{await patch(`/appointments/${id}/${name}`);setSelected(null);setRefresh(x=>x+1)}catch(e){setError(e.message)}}
 return <main className="shell">
   <header className="topbar"><div><div className="eyebrow">SPRINT 4.5C · SECURITY + DEPLOYMENT GATE</div><h1>Clinic Front Desk</h1><p>Appointment operations dashboard</p></div><div className="topActions"><span className="userChip">{user.full_name} · {user.role}</span><button onClick={logout}>Log out</button><button onClick={()=>setShowOps(true)}>Operational dashboard</button>{user.role==='OWNER'&&<><button onClick={()=>setShowAdmin(true)}>Administration</button><button onClick={()=>setShowUsers(true)}>Users & roles</button><button onClick={()=>setShowAudit(true)}>Audit log</button></>}{user.role!=='DOCTOR'&&<><button onClick={()=>setShowWaiting(true)}>Waiting list</button><button className="primary" onClick={()=>setShowBook(true)}>+ New appointment</button></>}</div></header>
   {error&&<div className="error">{error}<button onClick={()=>setError('')}>×</button></div>}
   <section className="filters">
    <label>Clinic<select value={clinicId} onChange={e=>{setClinicId(e.target.value);setDoctorId('')}}>{clinics.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label>
    <label>Doctor<select value={doctorId} disabled={user.role==='DOCTOR'} onChange={e=>setDoctorId(e.target.value)}>{user.role!=='DOCTOR'&&<option value="">All doctors</option>}{doctors.map(d=><option key={d.id} value={d.id}>{d.name}</option>)}</select></label>
    <label>Date<input type="date" value={day} onChange={e=>setDay(e.target.value)}/></label>
   </section>
   <section className="stats">
    <Stat label="Appointments" value={summary?.total??0}/><Stat label="High risk" value={summary?.risk_counts?.HIGH||0}/><Stat label="Pending" value={counts.PENDING||0}/><Stat label="Completed" value={counts.COMPLETED||0}/>
   </section>
   <section className="grid">
    <div className="panel"><div className="panelHead"><h2>Schedule</h2><span>{day}</span></div>
      <div className="schedule">{appointments.length===0?<Empty text="No appointments for this selection."/>:appointments.map(a=><AppointmentCard key={a.id} a={a} risk={risks[a.id]} onClick={()=>setSelected(a)}/>)}</div>
    </div>
    <aside className="panel attention"><div className="panelHead attentionHead"><div><h2>Attention Queue</h2><small>Highest priority first</small></div><span>{summary?.attention?.length||0}</span></div>
      <div className="attentionCounts"><span>Critical <b>{summary?.attention_counts?.CRITICAL||0}</b></span><span>High <b>{summary?.attention_counts?.HIGH||0}</b></span><span>Medium <b>{summary?.attention_counts?.MEDIUM||0}</b></span></div>
      {(summary?.attention||[]).length===0?<Empty text="Nothing requires action for this selection."/>:(summary.attention.map((x,i)=><AttentionItem key={`${x.appointment_id}-${i}`} item={x} appointments={appointments} open={setSelected} quickAction={action} recover={setRecoveryAppointment} canOperate={user.role!=='DOCTOR'}/>))}
    </aside>
   </section>
   {showOps&&<OperationalDashboard clinicId={Number(clinicId)} doctors={doctors} selectedDoctor={doctorId} selectedDay={day} onClose={()=>setShowOps(false)} setError={setError}/>}
   {user.role==='OWNER'&&showAdmin&&<AdminModal clinicId={Number(clinicId)} clinics={clinics} doctors={doctors} services={services} onClose={()=>setShowAdmin(false)} onChanged={()=>setRefresh(x=>x+1)} setClinicId={setClinicId} setError={setError}/>}
   {user.role==='OWNER'&&showUsers&&<UsersModal clinicId={Number(clinicId)} doctors={doctors} onClose={()=>setShowUsers(false)} setError={setError}/>}
   {user.role==='OWNER'&&showAudit&&<AuditLogModal onClose={()=>setShowAudit(false)} setError={setError}/>}
   {user.role!=='DOCTOR'&&showWaiting&&<WaitingListModal clinicId={Number(clinicId)} doctors={doctors} services={services} onClose={()=>setShowWaiting(false)} onChanged={()=>setRefresh(x=>x+1)} setError={setError}/>}
   {recoveryAppointment&&<RecoveryModal appointment={recoveryAppointment} onClose={()=>setRecoveryAppointment(null)} onRecovered={()=>{setRecoveryAppointment(null);setRefresh(x=>x+1)}} setError={setError}/>}
   {user.role!=='DOCTOR'&&showBook&&<BookingModal clinicId={Number(clinicId)} doctors={doctors} services={services} defaultDoctor={doctorId} defaultDay={day} onClose={()=>setShowBook(false)} onSaved={()=>{setShowBook(false);setRefresh(x=>x+1)}} setError={setError}/>} 
   {selected&&<AppointmentModal a={selected} readOnly={user.role==='DOCTOR'} onClose={()=>setSelected(null)} action={action} onRescheduled={()=>{setSelected(null);setRefresh(x=>x+1)}} setError={setError}/>} 
 </main>
}
function Stat({label,value}){return <div className="stat"><span>{label}</span><strong>{value}</strong></div>}
function Empty({text}){return <div className="empty">{text}</div>}
function AppointmentCard({a,risk,onClick}){return <button className="appt" onClick={onClick}><div className="time">{fmtTime(a.start_at)}</div><div className="apptBody"><b>{a.patient_name}</b><span>{a.service_name} · {a.doctor_name}</span></div><div className="badgeStack"><span className={`badge ${a.status.toLowerCase()}`}>{a.status.replace('_',' ')}</span>{risk&&<span className={`riskBadge risk-${risk.level.toLowerCase()}`}>Risk {risk.score} · {risk.level}</span>}</div></button>}


function AttentionItem({item,appointments,open,quickAction,recover,canOperate=true}){
 const a=appointments.find(y=>y.id===item.appointment_id);
 const title=item.type==='OVERDUE_STATUS'?'Workflow overdue':item.type==='PENDING_CONFIRMATION'?'Confirmation needed':item.type==='HIGH_RISK'?'High no-show risk':item.type==='CANCELLED_SLOT'?'Recover cancelled slot':'Risk review';
 return <div className={`attentionCard severity-${item.severity.toLowerCase()}`}>
   <button className="attentionMain" onClick={()=>a&&open(a)}><div className="attentionTop"><span className={`severity severity-${item.severity.toLowerCase()}`}>{item.severity}</span><b>{title}</b><span className="priority">P{item.priority_score}</span></div><strong>{item.patient_name}</strong><span>{fmtTime(item.start_at)} · {item.doctor_name} · {item.service_name}</span>{item.signals?.length>0&&<small>{item.signals[0]}</small>}<em>{item.recommended_action}</em></button>
   <div className="attentionActions">{canOperate&&item.quick_action==='confirm'&&<button className="primary miniAction" onClick={()=>quickAction(item.appointment_id,'confirm')}>Confirm now</button>}{canOperate&&item.type==='CANCELLED_SLOT'&&a&&<button className="primary miniAction" onClick={()=>recover(a)}>Find candidates</button>}<button className="miniAction" onClick={()=>a&&open(a)}>Open</button></div>
 </div>
}

function BookingModal({clinicId,doctors,services,defaultDoctor,defaultDay,onClose,onSaved,setError}){
 const [q,setQ]=useState(''),[patients,setPatients]=useState([]),[patient,setPatient]=useState(null),[newPatient,setNewPatient]=useState(false);
 const [name,setName]=useState(''),[phone,setPhone]=useState(''),[doctor,setDoctor]=useState(defaultDoctor||String(doctors[0]?.id||'')),[service,setService]=useState(String(services[0]?.id||'')),[day,setDay]=useState(defaultDay),[slots,setSlots]=useState([]),[slot,setSlot]=useState(''),[busy,setBusy]=useState(false);
 async function json(url,opt){const r=await authFetch(API+url,opt);if(!r.ok)throw new Error(await r.text());return r.json()}
 useEffect(()=>{if(!q.trim()){setPatients([]);return}const t=setTimeout(()=>json(`/patients?clinic_id=${clinicId}&q=${encodeURIComponent(q)}`).then(setPatients).catch(e=>setError(e.message)),250);return()=>clearTimeout(t)},[q]);
 useEffect(()=>{if(!doctor||!service||!day)return;json(`/doctors/${doctor}/availability?clinic_id=${clinicId}&service_id=${service}&day=${day}`).then(s=>{setSlots(s);setSlot('')}).catch(e=>setError(e.message))},[doctor,service,day]);
 async function submit(){setBusy(true);setError('');try{let p=patient;if(!p){if(!name||!phone)throw new Error('Select an existing patient or enter a new patient name and phone.');p=await json('/patients',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({clinic_id:clinicId,full_name:name,phone,preferred_language:'ar'})})}if(!slot)throw new Error('Choose an available time.');await json('/appointments',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({clinic_id:clinicId,doctor_id:Number(doctor),patient_id:p.id,service_id:Number(service),start_at:slot})});onSaved()}catch(e){setError(e.message)}finally{setBusy(false)}}
 return <div className="overlay"><div className="modal large"><div className="modalHead"><div><h2>New appointment</h2><p>Search patient, then choose a real available slot.</p></div><button className="close" onClick={onClose}>×</button></div>
  <div className="formGrid"><div className="patientBox"><label>Search patient<input placeholder="Name or phone" value={q} onChange={e=>{setQ(e.target.value);setPatient(null)}}/></label>{patients.map(p=><button className={`patientRow ${patient?.id===p.id?'chosen':''}`} key={p.id} onClick={()=>{setPatient(p);setQ(p.full_name)}}><b>{p.full_name}</b><span>{p.phone}</span></button>)}<button className="link" onClick={()=>setNewPatient(x=>!x)}>+ New patient</button>{newPatient&&!patient&&<div className="newPatient"><input placeholder="Full name" value={name} onChange={e=>setName(e.target.value)}/><input placeholder="Phone" value={phone} onChange={e=>setPhone(e.target.value)}/></div>}</div>
   <div><label>Doctor<select value={doctor} onChange={e=>setDoctor(e.target.value)}>{doctors.map(d=><option key={d.id} value={d.id}>{d.name}</option>)}</select></label><label>Service<select value={service} onChange={e=>setService(e.target.value)}>{services.map(s=><option key={s.id} value={s.id}>{s.name} ({s.duration_minutes} min)</option>)}</select></label><label>Date<input type="date" value={day} onChange={e=>setDay(e.target.value)}/></label><label>Available times<div className="slots">{slots.length?slots.map(s=><button key={s.start_at} onClick={()=>setSlot(s.start_at)} className={slot===s.start_at?'slot chosenSlot':'slot'}>{fmtTime(s.start_at)}</button>):<span className="muted">No available slots</span>}</div></label></div></div>
  <div className="modalActions"><button onClick={onClose}>Cancel</button><button className="primary" disabled={busy} onClick={submit}>{busy?'Booking...':'Book appointment'}</button></div>
 </div></div>
}

function AppointmentModal({a,onClose,action,onRescheduled,setError,readOnly=false}){
 const [reschedule,setReschedule]=useState(false),[when,setWhen]=useState(a.start_at.slice(0,16)),[risk,setRisk]=useState(null),[history,setHistory]=useState(null);
 useEffect(()=>{Promise.all([authFetch(API+`/appointments/${a.id}/risk`).then(r=>{if(!r.ok)throw new Error('Could not load risk');return r.json()}),authFetch(API+`/patients/${a.patient_id}/history`).then(r=>{if(!r.ok)throw new Error('Could not load patient history');return r.json()})]).then(([r,h])=>{setRisk(r);setHistory(h)}).catch(e=>setError(e.message))},[a.id,a.patient_id]);
 async function doReschedule(){try{const r=await authFetch(API+`/appointments/${a.id}/reschedule`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({start_at:when})});if(!r.ok)throw new Error(await r.text());onRescheduled()}catch(e){setError(e.message)}}
 return <div className="overlay"><div className="modal large"><div className="modalHead"><div><h2>{a.patient_name}</h2><p>{a.patient_phone}</p></div><button className="close" onClick={onClose}>×</button></div><div className="details"><div><span>Time</span><b>{new Date(a.start_at).toLocaleString()}</b></div><div><span>Doctor</span><b>{a.doctor_name}</b></div><div><span>Service</span><b>{a.service_name}</b></div><div><span>Status</span><b>{a.status}</b></div></div>
 {risk&&<section className={`riskPanel riskPanel-${risk.level.toLowerCase()}`}><div className="riskHead"><div><span>No-show risk</span><strong>{risk.score}/100 · {risk.level}</strong></div><small>Rule-based · explainable</small></div>{risk.reasons.length?<div className="reasonList">{risk.reasons.map(x=><div key={x.code}><span>{x.detail}</span><b>+{x.points}</b></div>)}</div>:<p className="muted">No current risk factors detected.</p>}</section>}
 {history&&<section className="historyPanel"><h3>Patient front-desk history</h3><div className="historyStats"><div><span>Total</span><b>{history.total_appointments}</b></div><div><span>Completed</span><b>{history.completed}</b></div><div><span>Cancelled</span><b>{history.cancelled}</b></div><div><span>No-show</span><b>{history.no_show}</b></div><div><span>No-show rate</span><b>{history.no_show_rate_percent}%</b></div></div></section>}
 {reschedule&&<label>New date/time<input type="datetime-local" value={when} onChange={e=>setWhen(e.target.value)}/><button className="primary full" onClick={doReschedule}>Save new time</button></label>}
 {!readOnly&&<div className="actionGrid">{a.status==='PENDING'&&<button onClick={()=>action(a.id,'confirm')}>Confirm</button>}{['PENDING','CONFIRMED'].includes(a.status)&&<button onClick={()=>action(a.id,'check-in')}>Check in</button>}{a.status==='CHECKED_IN'&&<button onClick={()=>action(a.id,'complete')}>Complete</button>}{['PENDING','CONFIRMED'].includes(a.status)&&<button onClick={()=>action(a.id,'no-show')}>No-show</button>}{['PENDING','CONFIRMED'].includes(a.status)&&<button onClick={()=>setReschedule(x=>!x)}>Reschedule</button>}{!['CANCELLED','COMPLETED','NO_SHOW'].includes(a.status)&&<button className="danger" onClick={()=>action(a.id,'cancel')}>Cancel</button>}</div>}</div></div>
}

function WaitingListModal({clinicId,doctors,services,onClose,onChanged,setError}){
 const [entries,setEntries]=useState([]),[q,setQ]=useState(''),[patients,setPatients]=useState([]),[patient,setPatient]=useState(null);
 const [doctor,setDoctor]=useState(String(doctors[0]?.id||'')),[service,setService]=useState(String(services[0]?.id||''));
 const [preferredDay,setPreferredDay]=useState(''),[earliest,setEarliest]=useState(''),[latest,setLatest]=useState(''),[priority,setPriority]=useState(0),[notes,setNotes]=useState('');
 async function req(path,opt={}){const r=await authFetch(API+path,{...opt,headers:{'Content-Type':'application/json',...(opt.headers||{})}});if(!r.ok)throw new Error(await r.text());return r.json()}
 async function load(){try{setEntries(await req(`/waiting-list?clinic_id=${clinicId}&status=ACTIVE`))}catch(e){setError(e.message)}}
 useEffect(()=>{load()},[clinicId]);
 useEffect(()=>{if(!q.trim()){setPatients([]);return}const t=setTimeout(()=>req(`/patients?clinic_id=${clinicId}&q=${encodeURIComponent(q)}`).then(setPatients).catch(e=>setError(e.message)),250);return()=>clearTimeout(t)},[q,clinicId]);
 async function add(){try{setError('');if(!patient)throw new Error('Select a patient.');if(!doctor||!service)throw new Error('Select doctor and service.');await req('/waiting-list',{method:'POST',body:JSON.stringify({clinic_id:clinicId,patient_id:patient.id,doctor_id:Number(doctor),service_id:Number(service),preferred_day:preferredDay||null,earliest_time:earliest?earliest+':00':null,latest_time:latest?latest+':00':null,priority:Number(priority)||0,notes:notes||null})});setPatient(null);setQ('');setPreferredDay('');setEarliest('');setLatest('');setPriority(0);setNotes('');await load();onChanged()}catch(e){setError(e.message)}}
 async function remove(id){try{await req(`/waiting-list/${id}`,{method:'DELETE'});await load();onChanged()}catch(e){setError(e.message)}}
 return <div className="overlay"><div className="modal adminModal"><div className="modalHead"><div><h2>Waiting list</h2><p>Add patients who can take an earlier or cancelled slot.</p></div><button className="close" onClick={onClose}>×</button></div>
  <section className="adminSection"><h3>Active requests</h3><div className="adminList">{entries.length?entries.map(x=><div className="adminRow" key={x.id}><div><b>{x.patient_name}</b><span>{x.doctor_name} · {x.service_name}{x.preferred_day?` · ${x.preferred_day}`:' · flexible date'}{x.earliest_time||x.latest_time?` · ${x.earliest_time?.slice(0,5)||'any'}–${x.latest_time?.slice(0,5)||'any'}`:''}</span></div><button className="danger mini" onClick={()=>remove(x.id)}>Remove</button></div>):<div className="empty">No active waiting-list requests.</div>}</div></section>
  <section className="adminSection"><h3>Add patient to waiting list</h3><div className="adminForm two"><label>Search patient<input placeholder="Name or phone" value={q} onChange={e=>{setQ(e.target.value);setPatient(null)}}/></label><label>Selected patient<input disabled value={patient?`${patient.full_name} · ${patient.phone}`:''}/></label></div>{patients.map(p=><button className={`patientRow ${patient?.id===p.id?'chosen':''}`} key={p.id} onClick={()=>{setPatient(p);setQ(p.full_name);setPatients([])}}><b>{p.full_name}</b><span>{p.phone}</span></button>)}
   <div className="adminForm three"><label>Doctor<select value={doctor} onChange={e=>setDoctor(e.target.value)}>{doctors.map(d=><option key={d.id} value={d.id}>{d.name}</option>)}</select></label><label>Service<select value={service} onChange={e=>setService(e.target.value)}>{services.map(x=><option key={x.id} value={x.id}>{x.name}</option>)}</select></label><label>Preferred date (optional)<input type="date" value={preferredDay} onChange={e=>setPreferredDay(e.target.value)}/></label><label>Earliest time<input type="time" value={earliest} onChange={e=>setEarliest(e.target.value)}/></label><label>Latest time<input type="time" value={latest} onChange={e=>setLatest(e.target.value)}/></label><label>Priority 0–20<input type="number" min="0" max="20" value={priority} onChange={e=>setPriority(e.target.value)}/></label></div><label>Notes<input value={notes} onChange={e=>setNotes(e.target.value)} placeholder="Can come on short notice"/></label><button className="primary adminSave" onClick={add}>Add to waiting list</button>
  </section></div></div>
}

function RecoveryModal({appointment,onClose,onRecovered,setError}){
 const [candidates,setCandidates]=useState([]),[busy,setBusy]=useState(false);
 async function req(path,opt={}){const r=await authFetch(API+path,{...opt,headers:{'Content-Type':'application/json',...(opt.headers||{})}});if(!r.ok)throw new Error(await r.text());return r.json()}
 useEffect(()=>{req(`/appointments/${appointment.id}/recovery-candidates`).then(setCandidates).catch(e=>setError(e.message))},[appointment.id]);
 async function recover(c){try{setBusy(true);setError('');await req(`/appointments/${appointment.id}/recover/${c.waiting_list_id}`,{method:'POST'});onRecovered()}catch(e){setError(e.message)}finally{setBusy(false)}}
 return <div className="overlay"><div className="modal large"><div className="modalHead"><div><h2>Recover cancelled slot</h2><p>{new Date(appointment.start_at).toLocaleString()} · {appointment.doctor_name} · {appointment.service_name}</p></div><button className="close" onClick={onClose}>×</button></div>
  <p className="muted">Candidates are ranked by doctor/service match, preferred date/time, manual priority and waiting time. Recovery creates a new PENDING appointment and keeps the cancelled appointment in history.</p>
  <div className="candidateList">{candidates.length?candidates.map(c=><div className="candidateCard" key={c.waiting_list_id}><div><div className="candidateTop"><b>{c.patient_name}</b><span>Score {c.priority_score}</span></div><span>{c.patient_phone}</span><small>{c.reasons.join(' · ')}</small></div><button className="primary" disabled={busy} onClick={()=>recover(c)}>Book this slot</button></div>):<div className="empty">No eligible waiting-list patients match this cancelled slot.</div>}</div>
 </div></div>
}

function AuditLogModal({onClose,setError}){
 const [rows,setRows]=useState([]),[loading,setLoading]=useState(true);
 async function load(){try{setLoading(true);const r=await authFetch(API+'/audit-logs?limit=200',{cache:'no-store'});if(!r.ok)throw new Error(await r.text());setRows(await r.json())}catch(e){setError(e.message)}finally{setLoading(false)}}
 useEffect(()=>{load()},[]);
 return <div className="overlay"><div className="modal adminModal"><div className="modalHead"><div><h2>Audit log</h2><p>Recent security-sensitive and data-changing actions. Passwords and request bodies are never stored here.</p></div><button className="close" onClick={onClose}>×</button></div>
   <div className="adminList">{loading?<div className="empty">Loading audit events…</div>:rows.length?rows.map(x=><div className="adminRow" key={x.id}><div><b>{x.action}</b><span>{new Date(x.created_at).toLocaleString()} · HTTP {x.status_code} · user {x.user_id??'public'}</span><small>{x.path} · {x.ip_address||'unknown IP'}</small></div></div>):<div className="empty">No audit events recorded yet.</div>}</div>
 </div></div>
}

function AdminModal({clinicId,clinics,doctors,services,onClose,onChanged,setClinicId,setError}){
 const [tab,setTab]=useState('clinic');
 const [clinicName,setClinicName]=useState(clinics.find(c=>c.id===clinicId)?.name||'');
 const [timezone,setTimezone]=useState(clinics.find(c=>c.id===clinicId)?.timezone||'Asia/Beirut');
 const [doctorName,setDoctorName]=useState(''),[specialty,setSpecialty]=useState('');
 const [serviceName,setServiceName]=useState(''),[duration,setDuration]=useState(30),[price,setPrice]=useState('');
 const [scheduleDoctor,setScheduleDoctor]=useState(String(doctors[0]?.id||'')),[schedules,setSchedules]=useState([]);
 const [weekday,setWeekday]=useState(0),[startTime,setStartTime]=useState('09:00'),[endTime,setEndTime]=useState('17:00');
 const days=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
 async function req(path,opt={}){const r=await authFetch(API+path,{...opt,headers:{'Content-Type':'application/json',...(opt.headers||{})}});if(!r.ok)throw new Error(await r.text());return r.json()}
 async function run(fn){try{setError('');await fn();onChanged()}catch(e){setError(e.message)}}
 useEffect(()=>{const c=clinics.find(x=>x.id===clinicId);if(c){setClinicName(c.name);setTimezone(c.timezone)}},[clinicId,clinics]);
 useEffect(()=>{if(!scheduleDoctor){setSchedules([]);return}req(`/doctors/${scheduleDoctor}/schedule?clinic_id=${clinicId}`).then(setSchedules).catch(e=>setError(e.message))},[scheduleDoctor,clinicId]);
 async function reloadSchedules(){if(scheduleDoctor)setSchedules(await req(`/doctors/${scheduleDoctor}/schedule?clinic_id=${clinicId}`))}
 return <div className="overlay"><div className="modal adminModal"><div className="modalHead"><div><h2>Administration</h2><p>Manage the clinic configuration used by booking.</p></div><button className="close" onClick={onClose}>×</button></div>
  <div className="adminTabs">{[['clinic','Clinic Settings'],['doctors','Doctors'],['services','Services'],['hours','Working Hours']].map(([k,l])=><button key={k} className={tab===k?'active':''} onClick={()=>setTab(k)}>{l}</button>)}</div>
  {tab==='clinic'&&<section className="adminSection"><h3>Clinic Settings</h3><div className="adminForm"><label>Clinic<select value={clinicId} onChange={e=>setClinicId(e.target.value)}>{clinics.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label><label>Clinic name<input value={clinicName} onChange={e=>setClinicName(e.target.value)}/></label><label>Timezone<input value={timezone} onChange={e=>setTimezone(e.target.value)}/></label></div><button className="primary adminSave" onClick={()=>run(()=>req(`/clinics/${clinicId}`,{method:'PATCH',body:JSON.stringify({name:clinicName,timezone})}))}>Save clinic settings</button></section>}
  {tab==='doctors'&&<section className="adminSection"><h3>Doctors</h3><div className="adminList">{doctors.map(d=><div className="adminRow" key={d.id}><div><b>{d.name}</b><span>{d.specialty||'No specialty specified'}</span></div></div>)}</div><h4>Add doctor</h4><div className="adminForm two"><label>Name<input value={doctorName} onChange={e=>setDoctorName(e.target.value)} placeholder="Dr. Ahmad"/></label><label>Specialty<input value={specialty} onChange={e=>setSpecialty(e.target.value)} placeholder="General Medicine"/></label></div><button className="primary adminSave" onClick={()=>run(async()=>{if(!doctorName.trim())throw new Error('Doctor name is required.');await req('/doctors',{method:'POST',body:JSON.stringify({clinic_id:clinicId,name:doctorName,specialty:specialty||null})});setDoctorName('');setSpecialty('')})}>Add doctor</button></section>}
  {tab==='services'&&<section className="adminSection"><h3>Services</h3><div className="adminList">{services.map(s=><div className="adminRow" key={s.id}><div><b>{s.name}</b><span>{s.duration_minutes} min · {s.price==null?'No price':`$${s.price}`}</span></div></div>)}</div><h4>Add service</h4><div className="adminForm three"><label>Name<input value={serviceName} onChange={e=>setServiceName(e.target.value)} placeholder="Consultation"/></label><label>Duration (min)<input type="number" min="5" value={duration} onChange={e=>setDuration(e.target.value)}/></label><label>Price<input type="number" min="0" step="0.01" value={price} onChange={e=>setPrice(e.target.value)}/></label></div><button className="primary adminSave" onClick={()=>run(async()=>{if(!serviceName.trim())throw new Error('Service name is required.');await req('/services',{method:'POST',body:JSON.stringify({clinic_id:clinicId,name:serviceName,duration_minutes:Number(duration),price:price===''?null:Number(price)})});setServiceName('');setDuration(30);setPrice('')})}>Add service</button></section>}
  {tab==='hours'&&<section className="adminSection"><h3>Working Hours</h3><label>Doctor<select value={scheduleDoctor} onChange={e=>setScheduleDoctor(e.target.value)}>{doctors.map(d=><option key={d.id} value={d.id}>{d.name}</option>)}</select></label>{!doctors.length?<div className="empty">Add a doctor first.</div>:<><div className="adminList scheduleList">{schedules.length?schedules.map(s=><div className="adminRow" key={s.id}><div><b>{days[s.weekday]}</b><span>{s.start_time.slice(0,5)} – {s.end_time.slice(0,5)}</span></div><button className="danger mini" onClick={()=>run(async()=>{await req(`/schedules/${s.id}`,{method:'DELETE'});await reloadSchedules()})}>Remove</button></div>):<div className="empty">No working hours configured for this doctor.</div>}</div><h4>Add working hours</h4><div className="adminForm three"><label>Day<select value={weekday} onChange={e=>setWeekday(Number(e.target.value))}>{days.map((d,i)=><option key={d} value={i}>{d}</option>)}</select></label><label>Start<input type="time" value={startTime} onChange={e=>setStartTime(e.target.value)}/></label><label>End<input type="time" value={endTime} onChange={e=>setEndTime(e.target.value)}/></label></div><button className="primary adminSave" onClick={()=>run(async()=>{if(!scheduleDoctor)throw new Error('Select a doctor.');await req(`/doctors/${scheduleDoctor}/schedule`,{method:'POST',body:JSON.stringify({clinic_id:clinicId,weekday:Number(weekday),start_time:startTime+':00',end_time:endTime+':00'})});await reloadSchedules()})}>Add working hours</button></>}</section>}
 </div></div>
}


function OperationalDashboard({clinicId,doctors,selectedDoctor,selectedDay,onClose,setError}){
 const dateMinus=(d,n)=>{const x=new Date(`${d}T12:00:00`);x.setDate(x.getDate()-n);return x.toISOString().slice(0,10)};
 const [startDay,setStartDay]=useState(dateMinus(selectedDay,29)),[endDay,setEndDay]=useState(selectedDay),[doctor,setDoctor]=useState(selectedDoctor||''),[data,setData]=useState(null),[loading,setLoading]=useState(true);
 async function load(){
  try{setLoading(true);setError('');let path=`/dashboard/operational?clinic_id=${clinicId}&start_day=${startDay}&end_day=${endDay}`;if(doctor)path+=`&doctor_id=${doctor}`;const r=await authFetch(API+path,{cache:'no-store'});if(!r.ok)throw new Error(await r.text());setData(await r.json())}catch(e){setError(e.message)}finally{setLoading(false)}
 }
 useEffect(()=>{if(clinicId&&startDay&&endDay)load()},[clinicId,startDay,endDay,doctor]);
 const counts=data?.counts||{}, rates=data?.rates||{}, ops=data?.operations||{}, risk=data?.risk_counts||{};
 const maxDaily=Math.max(1,...(data?.daily_trend||[]).map(x=>x.total));
 return <div className="overlay"><div className="modal opsModal"><div className="modalHead"><div><h2>Operational Dashboard</h2><p>Clinic performance and appointment-flow intelligence. Revenue metrics are intentionally deferred.</p></div><button className="close" onClick={onClose}>×</button></div>
   <div className="opsFilters"><label>From<input type="date" value={startDay} onChange={e=>setStartDay(e.target.value)}/></label><label>To<input type="date" value={endDay} onChange={e=>setEndDay(e.target.value)}/></label><label>Doctor<select value={doctor} onChange={e=>setDoctor(e.target.value)}><option value="">All doctors</option>{doctors.map(d=><option key={d.id} value={d.id}>{d.name}</option>)}</select></label></div>
   {loading?<div className="empty">Loading operational metrics…</div>:data&&<>
    <div className="opsKpis"><Metric label="Appointments" value={data.total_appointments}/><Metric label="Completion rate" value={`${rates.completion_rate_percent}%`}/><Metric label="No-show rate" value={`${rates.no_show_rate_percent}%`}/><Metric label="Cancellation rate" value={`${rates.cancellation_rate_percent}%`}/><Metric label="Recovery rate" value={`${rates.cancellation_recovery_rate_percent}%`}/><Metric label="Active waiting list" value={ops.active_waiting_list}/></div>
    <div className="opsGrid">
      <section className="opsCard"><h3>Appointment flow</h3><div className="flowGrid"><Flow label="Pending" value={counts.PENDING||0}/><Flow label="Confirmed" value={counts.CONFIRMED||0}/><Flow label="Checked in" value={counts.CHECKED_IN||0}/><Flow label="Completed" value={counts.COMPLETED||0}/><Flow label="Cancelled" value={counts.CANCELLED||0}/><Flow label="No-show" value={counts.NO_SHOW||0}/></div><div className="opsNote">Open workflow: <b>{ops.open_workflow}</b> · Average booking lead: <b>{ops.average_booking_lead_hours}h</b></div></section>
      <section className="opsCard"><h3>Risk & recovery</h3><div className="riskSummary"><div><span>LOW</span><b>{risk.LOW||0}</b></div><div><span>MEDIUM</span><b>{risk.MEDIUM||0}</b></div><div><span>HIGH</span><b>{risk.HIGH||0}</b></div></div><div className="recoverySummary"><span>Recovered cancelled slots <b>{ops.recovered_cancelled_slots}</b></span><span>Still unrecovered <b>{ops.unrecovered_cancelled_slots}</b></span><span>Pending among active booking states <b>{rates.confirmation_open_percent}%</b></span></div></section>
    </div>
    <section className="opsCard"><h3>Daily appointment activity</h3><div className="trendList">{(data.daily_trend||[]).map(x=><div className="trendRow" key={x.day}><span>{x.day.slice(5)}</span><div className="trendTrack"><i style={{width:`${Math.max(2,x.total/maxDaily*100)}%`}}></i></div><b>{x.total}</b><small>{x.completed} completed · {x.cancelled} cancelled · {x.no_show} no-show</small></div>)}</div></section>
    <section className="opsCard"><h3>Doctor operational comparison</h3>{(data.doctor_breakdown||[]).length?<div className="doctorTable"><div className="doctorTableHead"><span>Doctor</span><span>Total</span><span>Completed</span><span>Cancelled</span><span>No-show</span><span>No-show rate</span></div>{data.doctor_breakdown.map(d=><div className="doctorTableRow" key={d.doctor_id}><b>{d.doctor_name}</b><span>{d.total}</span><span>{d.completed}</span><span>{d.cancelled}</span><span>{d.no_show}</span><span>{d.no_show_rate_percent}%</span></div>)}</div>:<div className="empty">No appointments in this period.</div>}</section>
    <div className="deferredNote"><b>Sprint 3F deferred:</b> no revenue-at-risk or revenue-recovered calculations are included in this dashboard.</div>
   </>}
 </div></div>
}
function Metric({label,value}){return <div className="opsMetric"><span>{label}</span><strong>{value}</strong></div>}
function Flow({label,value}){return <div><span>{label}</span><b>{value}</b></div>}

function UsersModal({clinicId,doctors,onClose,setError}){
 const [users,setUsers]=useState([]),[name,setName]=useState(''),[email,setEmail]=useState(''),[password,setPassword]=useState(''),[role,setRole]=useState('SECRETARY'),[doctorId,setDoctorId]=useState(''),[busy,setBusy]=useState(false);
 async function req(path,opt={}){const r=await authFetch(API+path,{...opt,headers:{'Content-Type':'application/json',...(opt.headers||{})}});if(!r.ok)throw new Error(await r.text());return r.json()}
 async function load(){try{setUsers(await req('/users'))}catch(e){setError(e.message)}}
 useEffect(()=>{load()},[]);
 async function add(){try{setBusy(true);setError('');await req('/users',{method:'POST',body:JSON.stringify({full_name:name,email,password,role,doctor_id:role==='DOCTOR'?Number(doctorId):null})});setName('');setEmail('');setPassword('');setRole('SECRETARY');setDoctorId('');await load()}catch(e){setError(e.message)}finally{setBusy(false)}}
 async function toggle(u){try{await req(`/users/${u.id}`,{method:'PATCH',body:JSON.stringify({is_active:!u.is_active})});await load()}catch(e){setError(e.message)}}
 return <div className="overlay"><div className="modal adminModal"><div className="modalHead"><div><h2>Users & roles</h2><p>OWNER controls configuration; SECRETARY operates the front desk; DOCTOR is read-only and linked to one doctor.</p></div><button className="close" onClick={onClose}>×</button></div>
  <section className="adminSection"><h3>Clinic users</h3><div className="adminList">{users.map(u=><div className="adminRow" key={u.id}><div><b>{u.full_name}</b><span>{u.email} · {u.role}{u.doctor_id?` · Doctor #${u.doctor_id}`:''} · {u.is_active?'Active':'Inactive'}</span></div><button className={u.is_active?'danger mini':'mini'} onClick={()=>toggle(u)}>{u.is_active?'Deactivate':'Activate'}</button></div>)}</div></section>
  <section className="adminSection"><h3>Add user</h3><div className="adminForm two"><label>Full name<input value={name} onChange={e=>setName(e.target.value)} /></label><label>Email<input type="email" value={email} onChange={e=>setEmail(e.target.value)} /></label><label>Temporary password<input type="password" minLength="10" value={password} onChange={e=>setPassword(e.target.value)} /></label><label>Role<select value={role} onChange={e=>{setRole(e.target.value);if(e.target.value!=='DOCTOR')setDoctorId('')}}><option value="SECRETARY">SECRETARY</option><option value="DOCTOR">DOCTOR</option><option value="OWNER">OWNER</option></select></label>{role==='DOCTOR'&&<label>Linked doctor<select value={doctorId} onChange={e=>setDoctorId(e.target.value)}><option value="">Select doctor</option>{doctors.map(d=><option key={d.id} value={d.id}>{d.name}</option>)}</select></label>}</div><button className="primary adminSave" disabled={busy||!name||!email||password.length<10||(role==='DOCTOR'&&!doctorId)} onClick={add}>{busy?'Creating…':'Create user'}</button></section>
 </div></div>
}

function AuthScreen({setupRequired,onAuth,setError,error}){
 const [email,setEmail]=useState(''),[password,setPassword]=useState(''),[name,setName]=useState('Clinic Owner'),[clinicId,setClinicId]=useState(''),[clinics,setClinics]=useState([]),[clinicName,setClinicName]=useState(''),[timezone,setTimezone]=useState('Asia/Beirut'),[busy,setBusy]=useState(false);
 useEffect(()=>{if(setupRequired)window.fetch(API+'/auth/setup-clinics').then(r=>r.ok?r.json():[]).then(c=>{setClinics(c);if(c.length)setClinicId(String(c[0].id))})},[setupRequired]);
 async function submit(e){e.preventDefault();try{setBusy(true);setError('');const path=setupRequired?'/auth/setup':'/auth/login';let body;if(setupRequired){body=clinics.length?{clinic_id:Number(clinicId),full_name:name,email,password}:{clinic_name:clinicName,timezone,full_name:name,email,password}}else body={email,password};const r=await window.fetch(API+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});if(!r.ok)throw new Error(await r.text());onAuth(await r.json())}catch(e){setError(e.message)}finally{setBusy(false)}}
 return <main className="authShell"><form className="authCard" onSubmit={submit}><div className="eyebrow">SPRINT 4.5A · SECURE FIRST RUN</div><h1>{setupRequired?'Set up your clinic':'Clinic Front Desk'}</h1><p>{setupRequired?'Create the clinic and its first OWNER account. This runs only once.':'Sign in to access clinic operations.'}</p>{error&&<div className="error">{error}</div>}{setupRequired&&<>{clinics.length?<label>Existing clinic<select value={clinicId} onChange={e=>setClinicId(e.target.value)} required>{clinics.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label>:<><label>Clinic name<input value={clinicName} onChange={e=>setClinicName(e.target.value)} placeholder="My Clinic" required/></label><label>Timezone<input value={timezone} onChange={e=>setTimezone(e.target.value)} required/></label></>}<label>Owner full name<input value={name} onChange={e=>setName(e.target.value)} required/></label></>}<label>Email<input type="email" value={email} onChange={e=>setEmail(e.target.value)} required/></label><label>Password<input type="password" minLength="10" value={password} onChange={e=>setPassword(e.target.value)} required/></label><button className="primary" disabled={busy}>{busy?'Please wait…':setupRequired?'Create clinic & owner':'Sign in'}</button></form></main>
}
