--
-- PostgreSQL database dump
--

\restrict fAdFKv0fuUIO1OClCcJ0jFz066soBCW5uhawdYLbMOuZZU1BRnmLbP5D9f2CiWK

-- Dumped from database version 16.15 (Debian 16.15-1.pgdg13+2)
-- Dumped by pg_dump version 16.15 (Debian 16.15-1.pgdg13+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE IF EXISTS ONLY public.waiting_list DROP CONSTRAINT IF EXISTS waiting_list_service_id_fkey;
ALTER TABLE IF EXISTS ONLY public.waiting_list DROP CONSTRAINT IF EXISTS waiting_list_patient_id_fkey;
ALTER TABLE IF EXISTS ONLY public.waiting_list DROP CONSTRAINT IF EXISTS waiting_list_doctor_id_fkey;
ALTER TABLE IF EXISTS ONLY public.waiting_list DROP CONSTRAINT IF EXISTS waiting_list_clinic_id_fkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_clinic_id_fkey;
ALTER TABLE IF EXISTS ONLY public.services DROP CONSTRAINT IF EXISTS services_clinic_id_fkey;
ALTER TABLE IF EXISTS ONLY public.risk_scores DROP CONSTRAINT IF EXISTS risk_scores_patient_id_fkey;
ALTER TABLE IF EXISTS ONLY public.risk_scores DROP CONSTRAINT IF EXISTS risk_scores_clinic_id_fkey;
ALTER TABLE IF EXISTS ONLY public.risk_scores DROP CONSTRAINT IF EXISTS risk_scores_appointment_id_fkey;
ALTER TABLE IF EXISTS ONLY public.patients DROP CONSTRAINT IF EXISTS patients_clinic_id_fkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS fk_users_doctor_id_doctors;
ALTER TABLE IF EXISTS ONLY public.doctors DROP CONSTRAINT IF EXISTS doctors_clinic_id_fkey;
ALTER TABLE IF EXISTS ONLY public.doctor_schedules DROP CONSTRAINT IF EXISTS doctor_schedules_doctor_id_fkey;
ALTER TABLE IF EXISTS ONLY public.doctor_schedules DROP CONSTRAINT IF EXISTS doctor_schedules_clinic_id_fkey;
ALTER TABLE IF EXISTS ONLY public.audit_logs DROP CONSTRAINT IF EXISTS audit_logs_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.audit_logs DROP CONSTRAINT IF EXISTS audit_logs_clinic_id_fkey;
ALTER TABLE IF EXISTS ONLY public.appointments DROP CONSTRAINT IF EXISTS appointments_service_id_fkey;
ALTER TABLE IF EXISTS ONLY public.appointments DROP CONSTRAINT IF EXISTS appointments_patient_id_fkey;
ALTER TABLE IF EXISTS ONLY public.appointments DROP CONSTRAINT IF EXISTS appointments_doctor_id_fkey;
ALTER TABLE IF EXISTS ONLY public.appointments DROP CONSTRAINT IF EXISTS appointments_clinic_id_fkey;
ALTER TABLE IF EXISTS ONLY public.appointment_events DROP CONSTRAINT IF EXISTS appointment_events_appointment_id_fkey;
DROP INDEX IF EXISTS public.ix_waiting_list_status;
DROP INDEX IF EXISTS public.ix_waiting_list_service_id;
DROP INDEX IF EXISTS public.ix_waiting_list_preferred_day;
DROP INDEX IF EXISTS public.ix_waiting_list_patient_id;
DROP INDEX IF EXISTS public.ix_waiting_list_doctor_id;
DROP INDEX IF EXISTS public.ix_waiting_list_clinic_id;
DROP INDEX IF EXISTS public.ix_users_role;
DROP INDEX IF EXISTS public.ix_users_email;
DROP INDEX IF EXISTS public.ix_users_doctor_id;
DROP INDEX IF EXISTS public.ix_users_clinic_id;
DROP INDEX IF EXISTS public.ix_services_clinic_id;
DROP INDEX IF EXISTS public.ix_risk_scores_patient_id;
DROP INDEX IF EXISTS public.ix_risk_scores_level;
DROP INDEX IF EXISTS public.ix_risk_scores_clinic_id;
DROP INDEX IF EXISTS public.ix_risk_scores_appointment_id;
DROP INDEX IF EXISTS public.ix_patients_phone;
DROP INDEX IF EXISTS public.ix_patients_full_name;
DROP INDEX IF EXISTS public.ix_patients_clinic_id;
DROP INDEX IF EXISTS public.ix_doctors_clinic_id;
DROP INDEX IF EXISTS public.ix_doctor_schedules_doctor_id;
DROP INDEX IF EXISTS public.ix_doctor_schedules_clinic_id;
DROP INDEX IF EXISTS public.ix_audit_logs_user_id;
DROP INDEX IF EXISTS public.ix_audit_logs_status_code;
DROP INDEX IF EXISTS public.ix_audit_logs_created_at;
DROP INDEX IF EXISTS public.ix_audit_logs_clinic_id;
DROP INDEX IF EXISTS public.ix_audit_logs_action;
DROP INDEX IF EXISTS public.ix_appointments_status;
DROP INDEX IF EXISTS public.ix_appointments_start_at;
DROP INDEX IF EXISTS public.ix_appointments_service_id;
DROP INDEX IF EXISTS public.ix_appointments_patient_id;
DROP INDEX IF EXISTS public.ix_appointments_end_at;
DROP INDEX IF EXISTS public.ix_appointments_doctor_id;
DROP INDEX IF EXISTS public.ix_appointments_clinic_id;
DROP INDEX IF EXISTS public.ix_appointment_events_event_type;
DROP INDEX IF EXISTS public.ix_appointment_events_appointment_id;
ALTER TABLE IF EXISTS ONLY public.waiting_list DROP CONSTRAINT IF EXISTS waiting_list_pkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_pkey;
ALTER TABLE IF EXISTS ONLY public.risk_scores DROP CONSTRAINT IF EXISTS uq_risk_scores_appointment_id;
ALTER TABLE IF EXISTS ONLY public.services DROP CONSTRAINT IF EXISTS services_pkey;
ALTER TABLE IF EXISTS ONLY public.risk_scores DROP CONSTRAINT IF EXISTS risk_scores_pkey;
ALTER TABLE IF EXISTS ONLY public.patients DROP CONSTRAINT IF EXISTS patients_pkey;
ALTER TABLE IF EXISTS ONLY public.doctors DROP CONSTRAINT IF EXISTS doctors_pkey;
ALTER TABLE IF EXISTS ONLY public.doctor_schedules DROP CONSTRAINT IF EXISTS doctor_schedules_pkey;
ALTER TABLE IF EXISTS ONLY public.clinics DROP CONSTRAINT IF EXISTS clinics_pkey;
ALTER TABLE IF EXISTS ONLY public.audit_logs DROP CONSTRAINT IF EXISTS audit_logs_pkey;
ALTER TABLE IF EXISTS ONLY public.appointments DROP CONSTRAINT IF EXISTS appointments_pkey;
ALTER TABLE IF EXISTS ONLY public.appointment_events DROP CONSTRAINT IF EXISTS appointment_events_pkey;
ALTER TABLE IF EXISTS ONLY public.alembic_version DROP CONSTRAINT IF EXISTS alembic_version_pkc;
ALTER TABLE IF EXISTS public.waiting_list ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.users ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.services ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.risk_scores ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.patients ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.doctors ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.doctor_schedules ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.clinics ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.audit_logs ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.appointments ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.appointment_events ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE IF EXISTS public.waiting_list_id_seq;
DROP TABLE IF EXISTS public.waiting_list;
DROP SEQUENCE IF EXISTS public.users_id_seq;
DROP TABLE IF EXISTS public.users;
DROP SEQUENCE IF EXISTS public.services_id_seq;
DROP TABLE IF EXISTS public.services;
DROP SEQUENCE IF EXISTS public.risk_scores_id_seq;
DROP TABLE IF EXISTS public.risk_scores;
DROP SEQUENCE IF EXISTS public.patients_id_seq;
DROP TABLE IF EXISTS public.patients;
DROP SEQUENCE IF EXISTS public.doctors_id_seq;
DROP TABLE IF EXISTS public.doctors;
DROP SEQUENCE IF EXISTS public.doctor_schedules_id_seq;
DROP TABLE IF EXISTS public.doctor_schedules;
DROP SEQUENCE IF EXISTS public.clinics_id_seq;
DROP TABLE IF EXISTS public.clinics;
DROP SEQUENCE IF EXISTS public.audit_logs_id_seq;
DROP TABLE IF EXISTS public.audit_logs;
DROP SEQUENCE IF EXISTS public.appointments_id_seq;
DROP TABLE IF EXISTS public.appointments;
DROP SEQUENCE IF EXISTS public.appointment_events_id_seq;
DROP TABLE IF EXISTS public.appointment_events;
DROP TABLE IF EXISTS public.alembic_version;
DROP TYPE IF EXISTS public.userrole;
DROP TYPE IF EXISTS public.appointmentstatus;
--
-- Name: appointmentstatus; Type: TYPE; Schema: public; Owner: clinic
--

CREATE TYPE public.appointmentstatus AS ENUM (
    'PENDING',
    'CONFIRMED',
    'CHECKED_IN',
    'COMPLETED',
    'CANCELLED',
    'RESCHEDULED',
    'NO_SHOW',
    'EXPIRED'
);


ALTER TYPE public.appointmentstatus OWNER TO clinic;

--
-- Name: userrole; Type: TYPE; Schema: public; Owner: clinic
--

CREATE TYPE public.userrole AS ENUM (
    'OWNER',
    'SECRETARY',
    'DOCTOR'
);


ALTER TYPE public.userrole OWNER TO clinic;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: clinic
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO clinic;

--
-- Name: appointment_events; Type: TABLE; Schema: public; Owner: clinic
--

CREATE TABLE public.appointment_events (
    id integer NOT NULL,
    appointment_id integer NOT NULL,
    event_type character varying(64) NOT NULL,
    created_at timestamp without time zone NOT NULL,
    details text
);


ALTER TABLE public.appointment_events OWNER TO clinic;

--
-- Name: appointment_events_id_seq; Type: SEQUENCE; Schema: public; Owner: clinic
--

CREATE SEQUENCE public.appointment_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.appointment_events_id_seq OWNER TO clinic;

--
-- Name: appointment_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: clinic
--

ALTER SEQUENCE public.appointment_events_id_seq OWNED BY public.appointment_events.id;


--
-- Name: appointments; Type: TABLE; Schema: public; Owner: clinic
--

CREATE TABLE public.appointments (
    id integer NOT NULL,
    clinic_id integer NOT NULL,
    doctor_id integer NOT NULL,
    patient_id integer NOT NULL,
    service_id integer NOT NULL,
    start_at timestamp without time zone NOT NULL,
    end_at timestamp without time zone NOT NULL,
    status public.appointmentstatus NOT NULL,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.appointments OWNER TO clinic;

--
-- Name: appointments_id_seq; Type: SEQUENCE; Schema: public; Owner: clinic
--

CREATE SEQUENCE public.appointments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.appointments_id_seq OWNER TO clinic;

--
-- Name: appointments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: clinic
--

ALTER SEQUENCE public.appointments_id_seq OWNED BY public.appointments.id;


--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: clinic
--

CREATE TABLE public.audit_logs (
    id integer NOT NULL,
    clinic_id integer,
    user_id integer,
    action character varying(80) NOT NULL,
    method character varying(12) NOT NULL,
    path character varying(255) NOT NULL,
    status_code integer NOT NULL,
    ip_address character varying(64),
    user_agent character varying(255),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.audit_logs OWNER TO clinic;

--
-- Name: audit_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: clinic
--

CREATE SEQUENCE public.audit_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.audit_logs_id_seq OWNER TO clinic;

--
-- Name: audit_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: clinic
--

ALTER SEQUENCE public.audit_logs_id_seq OWNED BY public.audit_logs.id;


--
-- Name: clinics; Type: TABLE; Schema: public; Owner: clinic
--

CREATE TABLE public.clinics (
    id integer NOT NULL,
    name character varying(120) NOT NULL,
    timezone character varying(64) NOT NULL
);


ALTER TABLE public.clinics OWNER TO clinic;

--
-- Name: clinics_id_seq; Type: SEQUENCE; Schema: public; Owner: clinic
--

CREATE SEQUENCE public.clinics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.clinics_id_seq OWNER TO clinic;

--
-- Name: clinics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: clinic
--

ALTER SEQUENCE public.clinics_id_seq OWNED BY public.clinics.id;


--
-- Name: doctor_schedules; Type: TABLE; Schema: public; Owner: clinic
--

CREATE TABLE public.doctor_schedules (
    id integer NOT NULL,
    clinic_id integer NOT NULL,
    doctor_id integer NOT NULL,
    weekday integer NOT NULL,
    start_time time without time zone NOT NULL,
    end_time time without time zone NOT NULL
);


ALTER TABLE public.doctor_schedules OWNER TO clinic;

--
-- Name: doctor_schedules_id_seq; Type: SEQUENCE; Schema: public; Owner: clinic
--

CREATE SEQUENCE public.doctor_schedules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.doctor_schedules_id_seq OWNER TO clinic;

--
-- Name: doctor_schedules_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: clinic
--

ALTER SEQUENCE public.doctor_schedules_id_seq OWNED BY public.doctor_schedules.id;


--
-- Name: doctors; Type: TABLE; Schema: public; Owner: clinic
--

CREATE TABLE public.doctors (
    id integer NOT NULL,
    clinic_id integer NOT NULL,
    name character varying(120) NOT NULL,
    specialty character varying(120)
);


ALTER TABLE public.doctors OWNER TO clinic;

--
-- Name: doctors_id_seq; Type: SEQUENCE; Schema: public; Owner: clinic
--

CREATE SEQUENCE public.doctors_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.doctors_id_seq OWNER TO clinic;

--
-- Name: doctors_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: clinic
--

ALTER SEQUENCE public.doctors_id_seq OWNED BY public.doctors.id;


--
-- Name: patients; Type: TABLE; Schema: public; Owner: clinic
--

CREATE TABLE public.patients (
    id integer NOT NULL,
    clinic_id integer NOT NULL,
    full_name character varying(160) NOT NULL,
    phone character varying(40) NOT NULL,
    preferred_language character varying(16) NOT NULL,
    notes text
);


ALTER TABLE public.patients OWNER TO clinic;

--
-- Name: patients_id_seq; Type: SEQUENCE; Schema: public; Owner: clinic
--

CREATE SEQUENCE public.patients_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.patients_id_seq OWNER TO clinic;

--
-- Name: patients_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: clinic
--

ALTER SEQUENCE public.patients_id_seq OWNED BY public.patients.id;


--
-- Name: risk_scores; Type: TABLE; Schema: public; Owner: clinic
--

CREATE TABLE public.risk_scores (
    id integer NOT NULL,
    clinic_id integer NOT NULL,
    patient_id integer NOT NULL,
    appointment_id integer NOT NULL,
    score integer DEFAULT 0 NOT NULL,
    level character varying(16) DEFAULT 'LOW'::character varying NOT NULL,
    reasons_json text DEFAULT '[]'::text NOT NULL,
    calculated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.risk_scores OWNER TO clinic;

--
-- Name: risk_scores_id_seq; Type: SEQUENCE; Schema: public; Owner: clinic
--

CREATE SEQUENCE public.risk_scores_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.risk_scores_id_seq OWNER TO clinic;

--
-- Name: risk_scores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: clinic
--

ALTER SEQUENCE public.risk_scores_id_seq OWNED BY public.risk_scores.id;


--
-- Name: services; Type: TABLE; Schema: public; Owner: clinic
--

CREATE TABLE public.services (
    id integer NOT NULL,
    clinic_id integer NOT NULL,
    name character varying(120) NOT NULL,
    duration_minutes integer NOT NULL,
    price numeric(10,2)
);


ALTER TABLE public.services OWNER TO clinic;

--
-- Name: services_id_seq; Type: SEQUENCE; Schema: public; Owner: clinic
--

CREATE SEQUENCE public.services_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.services_id_seq OWNER TO clinic;

--
-- Name: services_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: clinic
--

ALTER SEQUENCE public.services_id_seq OWNED BY public.services.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: clinic
--

CREATE TABLE public.users (
    id integer NOT NULL,
    clinic_id integer NOT NULL,
    email character varying(255) NOT NULL,
    full_name character varying(160) NOT NULL,
    password_hash character varying(255) NOT NULL,
    role public.userrole DEFAULT 'SECRETARY'::public.userrole NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    doctor_id integer
);


ALTER TABLE public.users OWNER TO clinic;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: clinic
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO clinic;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: clinic
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: waiting_list; Type: TABLE; Schema: public; Owner: clinic
--

CREATE TABLE public.waiting_list (
    id integer NOT NULL,
    clinic_id integer NOT NULL,
    patient_id integer NOT NULL,
    doctor_id integer NOT NULL,
    service_id integer NOT NULL,
    preferred_day date,
    earliest_time time without time zone,
    latest_time time without time zone,
    priority integer DEFAULT 0 NOT NULL,
    status character varying(16) DEFAULT 'ACTIVE'::character varying NOT NULL,
    notes text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.waiting_list OWNER TO clinic;

--
-- Name: waiting_list_id_seq; Type: SEQUENCE; Schema: public; Owner: clinic
--

CREATE SEQUENCE public.waiting_list_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.waiting_list_id_seq OWNER TO clinic;

--
-- Name: waiting_list_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: clinic
--

ALTER SEQUENCE public.waiting_list_id_seq OWNED BY public.waiting_list.id;


--
-- Name: appointment_events id; Type: DEFAULT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.appointment_events ALTER COLUMN id SET DEFAULT nextval('public.appointment_events_id_seq'::regclass);


--
-- Name: appointments id; Type: DEFAULT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.appointments ALTER COLUMN id SET DEFAULT nextval('public.appointments_id_seq'::regclass);


--
-- Name: audit_logs id; Type: DEFAULT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.audit_logs ALTER COLUMN id SET DEFAULT nextval('public.audit_logs_id_seq'::regclass);


--
-- Name: clinics id; Type: DEFAULT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.clinics ALTER COLUMN id SET DEFAULT nextval('public.clinics_id_seq'::regclass);


--
-- Name: doctor_schedules id; Type: DEFAULT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.doctor_schedules ALTER COLUMN id SET DEFAULT nextval('public.doctor_schedules_id_seq'::regclass);


--
-- Name: doctors id; Type: DEFAULT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.doctors ALTER COLUMN id SET DEFAULT nextval('public.doctors_id_seq'::regclass);


--
-- Name: patients id; Type: DEFAULT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.patients ALTER COLUMN id SET DEFAULT nextval('public.patients_id_seq'::regclass);


--
-- Name: risk_scores id; Type: DEFAULT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.risk_scores ALTER COLUMN id SET DEFAULT nextval('public.risk_scores_id_seq'::regclass);


--
-- Name: services id; Type: DEFAULT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.services ALTER COLUMN id SET DEFAULT nextval('public.services_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: waiting_list id; Type: DEFAULT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.waiting_list ALTER COLUMN id SET DEFAULT nextval('public.waiting_list_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: clinic
--

COPY public.alembic_version (version_num) FROM stdin;
0006_audit_logs
\.


--
-- Data for Name: appointment_events; Type: TABLE DATA; Schema: public; Owner: clinic
--

COPY public.appointment_events (id, appointment_id, event_type, created_at, details) FROM stdin;
\.


--
-- Data for Name: appointments; Type: TABLE DATA; Schema: public; Owner: clinic
--

COPY public.appointments (id, clinic_id, doctor_id, patient_id, service_id, start_at, end_at, status, created_at) FROM stdin;
\.


--
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: public; Owner: clinic
--

COPY public.audit_logs (id, clinic_id, user_id, action, method, path, status_code, ip_address, user_agent, created_at) FROM stdin;
1	\N	\N	AUTH_SETUP	POST	/auth/setup	200	185.97.92.104	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36	2026-09-11 03:43:39.241032
2	1	1	POST /users	POST	/users	200	185.97.92.104	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36	2026-09-11 03:46:50.494307
3	\N	\N	AUTH_LOGIN	POST	/auth/login	200	185.97.92.104	Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Mobile Safari/537.36	2026-09-11 03:47:28.198616
4	1	1	POST /doctors	POST	/doctors	200	185.97.92.104	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36	2026-09-11 03:51:08.801229
5	1	1	POST /doctors	POST	/doctors	200	185.97.92.104	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36	2026-09-11 03:51:39.315801
6	1	1	POST /doctors	POST	/doctors	200	185.97.92.104	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36	2026-09-11 04:05:26.082569
7	1	1	POST /doctors	POST	/doctors	200	185.97.92.104	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36	2026-09-11 04:05:26.091917
\.


--
-- Data for Name: clinics; Type: TABLE DATA; Schema: public; Owner: clinic
--

COPY public.clinics (id, name, timezone) FROM stdin;
1	Steps	Asia/Beirut
\.


--
-- Data for Name: doctor_schedules; Type: TABLE DATA; Schema: public; Owner: clinic
--

COPY public.doctor_schedules (id, clinic_id, doctor_id, weekday, start_time, end_time) FROM stdin;
\.


--
-- Data for Name: doctors; Type: TABLE DATA; Schema: public; Owner: clinic
--

COPY public.doctors (id, clinic_id, name, specialty) FROM stdin;
1	1	Dr. Rachid	General Medecine
2	1	Dr. Ahmad	Specs
3	1	Dr. Ali	Genes
4	1	Dr. Ali	Genes
\.


--
-- Data for Name: patients; Type: TABLE DATA; Schema: public; Owner: clinic
--

COPY public.patients (id, clinic_id, full_name, phone, preferred_language, notes) FROM stdin;
\.


--
-- Data for Name: risk_scores; Type: TABLE DATA; Schema: public; Owner: clinic
--

COPY public.risk_scores (id, clinic_id, patient_id, appointment_id, score, level, reasons_json, calculated_at) FROM stdin;
\.


--
-- Data for Name: services; Type: TABLE DATA; Schema: public; Owner: clinic
--

COPY public.services (id, clinic_id, name, duration_minutes, price) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: clinic
--

COPY public.users (id, clinic_id, email, full_name, password_hash, role, is_active, created_at, doctor_id) FROM stdin;
1	1	rawinazih@gmail.com	Clinic Owner	$2b$12$7q1K9mMDZEIVJ84DsxI4i.Q5uKS1q19tu.NEytmjwH3zbgbNdNMKO	OWNER	t	2026-09-11 03:43:39.224705	\N
2	1	noura.rifai92@gmail.com	noura	$2b$12$pZsfbldvCnMZtfgj/oH69.lcKmCMMYztnh1iTH3OmQCv.wDM0foZ.	SECRETARY	t	2026-09-11 03:46:50.483135	\N
\.


--
-- Data for Name: waiting_list; Type: TABLE DATA; Schema: public; Owner: clinic
--

COPY public.waiting_list (id, clinic_id, patient_id, doctor_id, service_id, preferred_day, earliest_time, latest_time, priority, status, notes, created_at) FROM stdin;
\.


--
-- Name: appointment_events_id_seq; Type: SEQUENCE SET; Schema: public; Owner: clinic
--

SELECT pg_catalog.setval('public.appointment_events_id_seq', 1, false);


--
-- Name: appointments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: clinic
--

SELECT pg_catalog.setval('public.appointments_id_seq', 1, false);


--
-- Name: audit_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: clinic
--

SELECT pg_catalog.setval('public.audit_logs_id_seq', 7, true);


--
-- Name: clinics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: clinic
--

SELECT pg_catalog.setval('public.clinics_id_seq', 1, true);


--
-- Name: doctor_schedules_id_seq; Type: SEQUENCE SET; Schema: public; Owner: clinic
--

SELECT pg_catalog.setval('public.doctor_schedules_id_seq', 1, false);


--
-- Name: doctors_id_seq; Type: SEQUENCE SET; Schema: public; Owner: clinic
--

SELECT pg_catalog.setval('public.doctors_id_seq', 4, true);


--
-- Name: patients_id_seq; Type: SEQUENCE SET; Schema: public; Owner: clinic
--

SELECT pg_catalog.setval('public.patients_id_seq', 1, false);


--
-- Name: risk_scores_id_seq; Type: SEQUENCE SET; Schema: public; Owner: clinic
--

SELECT pg_catalog.setval('public.risk_scores_id_seq', 1, false);


--
-- Name: services_id_seq; Type: SEQUENCE SET; Schema: public; Owner: clinic
--

SELECT pg_catalog.setval('public.services_id_seq', 1, false);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: clinic
--

SELECT pg_catalog.setval('public.users_id_seq', 2, true);


--
-- Name: waiting_list_id_seq; Type: SEQUENCE SET; Schema: public; Owner: clinic
--

SELECT pg_catalog.setval('public.waiting_list_id_seq', 1, false);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: appointment_events appointment_events_pkey; Type: CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.appointment_events
    ADD CONSTRAINT appointment_events_pkey PRIMARY KEY (id);


--
-- Name: appointments appointments_pkey; Type: CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.appointments
    ADD CONSTRAINT appointments_pkey PRIMARY KEY (id);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: clinics clinics_pkey; Type: CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.clinics
    ADD CONSTRAINT clinics_pkey PRIMARY KEY (id);


--
-- Name: doctor_schedules doctor_schedules_pkey; Type: CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.doctor_schedules
    ADD CONSTRAINT doctor_schedules_pkey PRIMARY KEY (id);


--
-- Name: doctors doctors_pkey; Type: CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.doctors
    ADD CONSTRAINT doctors_pkey PRIMARY KEY (id);


--
-- Name: patients patients_pkey; Type: CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.patients
    ADD CONSTRAINT patients_pkey PRIMARY KEY (id);


--
-- Name: risk_scores risk_scores_pkey; Type: CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.risk_scores
    ADD CONSTRAINT risk_scores_pkey PRIMARY KEY (id);


--
-- Name: services services_pkey; Type: CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.services
    ADD CONSTRAINT services_pkey PRIMARY KEY (id);


--
-- Name: risk_scores uq_risk_scores_appointment_id; Type: CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.risk_scores
    ADD CONSTRAINT uq_risk_scores_appointment_id UNIQUE (appointment_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: waiting_list waiting_list_pkey; Type: CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.waiting_list
    ADD CONSTRAINT waiting_list_pkey PRIMARY KEY (id);


--
-- Name: ix_appointment_events_appointment_id; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_appointment_events_appointment_id ON public.appointment_events USING btree (appointment_id);


--
-- Name: ix_appointment_events_event_type; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_appointment_events_event_type ON public.appointment_events USING btree (event_type);


--
-- Name: ix_appointments_clinic_id; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_appointments_clinic_id ON public.appointments USING btree (clinic_id);


--
-- Name: ix_appointments_doctor_id; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_appointments_doctor_id ON public.appointments USING btree (doctor_id);


--
-- Name: ix_appointments_end_at; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_appointments_end_at ON public.appointments USING btree (end_at);


--
-- Name: ix_appointments_patient_id; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_appointments_patient_id ON public.appointments USING btree (patient_id);


--
-- Name: ix_appointments_service_id; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_appointments_service_id ON public.appointments USING btree (service_id);


--
-- Name: ix_appointments_start_at; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_appointments_start_at ON public.appointments USING btree (start_at);


--
-- Name: ix_appointments_status; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_appointments_status ON public.appointments USING btree (status);


--
-- Name: ix_audit_logs_action; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_audit_logs_action ON public.audit_logs USING btree (action);


--
-- Name: ix_audit_logs_clinic_id; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_audit_logs_clinic_id ON public.audit_logs USING btree (clinic_id);


--
-- Name: ix_audit_logs_created_at; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_audit_logs_created_at ON public.audit_logs USING btree (created_at);


--
-- Name: ix_audit_logs_status_code; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_audit_logs_status_code ON public.audit_logs USING btree (status_code);


--
-- Name: ix_audit_logs_user_id; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_audit_logs_user_id ON public.audit_logs USING btree (user_id);


--
-- Name: ix_doctor_schedules_clinic_id; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_doctor_schedules_clinic_id ON public.doctor_schedules USING btree (clinic_id);


--
-- Name: ix_doctor_schedules_doctor_id; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_doctor_schedules_doctor_id ON public.doctor_schedules USING btree (doctor_id);


--
-- Name: ix_doctors_clinic_id; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_doctors_clinic_id ON public.doctors USING btree (clinic_id);


--
-- Name: ix_patients_clinic_id; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_patients_clinic_id ON public.patients USING btree (clinic_id);


--
-- Name: ix_patients_full_name; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_patients_full_name ON public.patients USING btree (full_name);


--
-- Name: ix_patients_phone; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_patients_phone ON public.patients USING btree (phone);


--
-- Name: ix_risk_scores_appointment_id; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_risk_scores_appointment_id ON public.risk_scores USING btree (appointment_id);


--
-- Name: ix_risk_scores_clinic_id; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_risk_scores_clinic_id ON public.risk_scores USING btree (clinic_id);


--
-- Name: ix_risk_scores_level; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_risk_scores_level ON public.risk_scores USING btree (level);


--
-- Name: ix_risk_scores_patient_id; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_risk_scores_patient_id ON public.risk_scores USING btree (patient_id);


--
-- Name: ix_services_clinic_id; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_services_clinic_id ON public.services USING btree (clinic_id);


--
-- Name: ix_users_clinic_id; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_users_clinic_id ON public.users USING btree (clinic_id);


--
-- Name: ix_users_doctor_id; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_users_doctor_id ON public.users USING btree (doctor_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: clinic
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_role; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_users_role ON public.users USING btree (role);


--
-- Name: ix_waiting_list_clinic_id; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_waiting_list_clinic_id ON public.waiting_list USING btree (clinic_id);


--
-- Name: ix_waiting_list_doctor_id; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_waiting_list_doctor_id ON public.waiting_list USING btree (doctor_id);


--
-- Name: ix_waiting_list_patient_id; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_waiting_list_patient_id ON public.waiting_list USING btree (patient_id);


--
-- Name: ix_waiting_list_preferred_day; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_waiting_list_preferred_day ON public.waiting_list USING btree (preferred_day);


--
-- Name: ix_waiting_list_service_id; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_waiting_list_service_id ON public.waiting_list USING btree (service_id);


--
-- Name: ix_waiting_list_status; Type: INDEX; Schema: public; Owner: clinic
--

CREATE INDEX ix_waiting_list_status ON public.waiting_list USING btree (status);


--
-- Name: appointment_events appointment_events_appointment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.appointment_events
    ADD CONSTRAINT appointment_events_appointment_id_fkey FOREIGN KEY (appointment_id) REFERENCES public.appointments(id);


--
-- Name: appointments appointments_clinic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.appointments
    ADD CONSTRAINT appointments_clinic_id_fkey FOREIGN KEY (clinic_id) REFERENCES public.clinics(id);


--
-- Name: appointments appointments_doctor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.appointments
    ADD CONSTRAINT appointments_doctor_id_fkey FOREIGN KEY (doctor_id) REFERENCES public.doctors(id);


--
-- Name: appointments appointments_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.appointments
    ADD CONSTRAINT appointments_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: appointments appointments_service_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.appointments
    ADD CONSTRAINT appointments_service_id_fkey FOREIGN KEY (service_id) REFERENCES public.services(id);


--
-- Name: audit_logs audit_logs_clinic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_clinic_id_fkey FOREIGN KEY (clinic_id) REFERENCES public.clinics(id);


--
-- Name: audit_logs audit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: doctor_schedules doctor_schedules_clinic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.doctor_schedules
    ADD CONSTRAINT doctor_schedules_clinic_id_fkey FOREIGN KEY (clinic_id) REFERENCES public.clinics(id);


--
-- Name: doctor_schedules doctor_schedules_doctor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.doctor_schedules
    ADD CONSTRAINT doctor_schedules_doctor_id_fkey FOREIGN KEY (doctor_id) REFERENCES public.doctors(id);


--
-- Name: doctors doctors_clinic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.doctors
    ADD CONSTRAINT doctors_clinic_id_fkey FOREIGN KEY (clinic_id) REFERENCES public.clinics(id);


--
-- Name: users fk_users_doctor_id_doctors; Type: FK CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT fk_users_doctor_id_doctors FOREIGN KEY (doctor_id) REFERENCES public.doctors(id);


--
-- Name: patients patients_clinic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.patients
    ADD CONSTRAINT patients_clinic_id_fkey FOREIGN KEY (clinic_id) REFERENCES public.clinics(id);


--
-- Name: risk_scores risk_scores_appointment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.risk_scores
    ADD CONSTRAINT risk_scores_appointment_id_fkey FOREIGN KEY (appointment_id) REFERENCES public.appointments(id);


--
-- Name: risk_scores risk_scores_clinic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.risk_scores
    ADD CONSTRAINT risk_scores_clinic_id_fkey FOREIGN KEY (clinic_id) REFERENCES public.clinics(id);


--
-- Name: risk_scores risk_scores_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.risk_scores
    ADD CONSTRAINT risk_scores_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: services services_clinic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.services
    ADD CONSTRAINT services_clinic_id_fkey FOREIGN KEY (clinic_id) REFERENCES public.clinics(id);


--
-- Name: users users_clinic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_clinic_id_fkey FOREIGN KEY (clinic_id) REFERENCES public.clinics(id);


--
-- Name: waiting_list waiting_list_clinic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.waiting_list
    ADD CONSTRAINT waiting_list_clinic_id_fkey FOREIGN KEY (clinic_id) REFERENCES public.clinics(id);


--
-- Name: waiting_list waiting_list_doctor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.waiting_list
    ADD CONSTRAINT waiting_list_doctor_id_fkey FOREIGN KEY (doctor_id) REFERENCES public.doctors(id);


--
-- Name: waiting_list waiting_list_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.waiting_list
    ADD CONSTRAINT waiting_list_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: waiting_list waiting_list_service_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: clinic
--

ALTER TABLE ONLY public.waiting_list
    ADD CONSTRAINT waiting_list_service_id_fkey FOREIGN KEY (service_id) REFERENCES public.services(id);


--
-- PostgreSQL database dump complete
--

\unrestrict fAdFKv0fuUIO1OClCcJ0jFz066soBCW5uhawdYLbMOuZZU1BRnmLbP5D9f2CiWK

