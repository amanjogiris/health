--
-- PostgreSQL database dump
--

\restrict T00Dx81yGUvAnqsEaymggqOpX4aaM8hkUVywfb8xFfdW5q5VPslbDvUbvaAiqGP

-- Dumped from database version 18.3 (Homebrew)
-- Dumped by pg_dump version 18.3 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: appointment_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.appointment_status AS ENUM (
    'PENDING',
    'CONFIRMED',
    'CANCELLED',
    'COMPLETED',
    'NO_SHOW',
    'REJECTED',
    'BOOKED'
);


--
-- Name: user_roles; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.user_roles AS ENUM (
    'admin',
    'doctor',
    'patient',
    'super_admin'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: appointment_slots; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.appointment_slots (
    id integer NOT NULL,
    doctor_id integer NOT NULL,
    clinic_id integer NOT NULL,
    is_booked boolean NOT NULL,
    capacity integer NOT NULL,
    booked_count integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    is_active boolean NOT NULL,
    start_time timestamp with time zone NOT NULL,
    end_time timestamp with time zone NOT NULL
);


--
-- Name: appointment_slots_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.appointment_slots_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: appointment_slots_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.appointment_slots_id_seq OWNED BY public.appointment_slots.id;


--
-- Name: appointments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.appointments (
    id integer NOT NULL,
    patient_id integer NOT NULL,
    doctor_id integer NOT NULL,
    clinic_id integer NOT NULL,
    slot_id integer NOT NULL,
    status public.appointment_status NOT NULL,
    reason_for_visit text,
    notes text,
    cancelled_at timestamp with time zone,
    cancelled_reason text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    is_active boolean NOT NULL
);


--
-- Name: appointments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.appointments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: appointments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.appointments_id_seq OWNED BY public.appointments.id;


--
-- Name: clinics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.clinics (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    address text NOT NULL,
    phone character varying(20) NOT NULL,
    email character varying(255),
    city character varying(100) NOT NULL,
    state character varying(100) NOT NULL,
    zip_code character varying(10) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    is_active boolean NOT NULL
);


--
-- Name: clinics_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.clinics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: clinics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.clinics_id_seq OWNED BY public.clinics.id;


--
-- Name: doctor_availability; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.doctor_availability (
    id integer NOT NULL,
    doctor_id integer NOT NULL,
    day_of_week integer NOT NULL,
    start_time time without time zone NOT NULL,
    end_time time without time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: doctor_availability_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.doctor_availability_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: doctor_availability_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.doctor_availability_id_seq OWNED BY public.doctor_availability.id;


--
-- Name: doctors; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.doctors (
    id integer NOT NULL,
    user_id integer NOT NULL,
    clinic_id integer NOT NULL,
    specialty character varying(100) NOT NULL,
    license_number character varying(50) NOT NULL,
    qualifications text,
    experience_years integer NOT NULL,
    max_patients_per_day integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    is_active boolean NOT NULL,
    consultation_duration_minutes integer DEFAULT 15 NOT NULL
);


--
-- Name: doctors_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.doctors_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: doctors_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.doctors_id_seq OWNED BY public.doctors.id;


--
-- Name: patients; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.patients (
    id integer NOT NULL,
    user_id integer NOT NULL,
    date_of_birth character varying(10),
    blood_group character varying(5),
    allergies text,
    emergency_contact character varying(20),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    is_active boolean NOT NULL
);


--
-- Name: patients_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patients_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: patients_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.patients_id_seq OWNED BY public.patients.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    name character varying(150) NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(128) NOT NULL,
    mobile_no character varying(20),
    address text,
    image character varying(255),
    role public.user_roles NOT NULL,
    is_verified boolean NOT NULL,
    last_login timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    is_active boolean NOT NULL
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: appointment_slots id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.appointment_slots ALTER COLUMN id SET DEFAULT nextval('public.appointment_slots_id_seq'::regclass);


--
-- Name: appointments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.appointments ALTER COLUMN id SET DEFAULT nextval('public.appointments_id_seq'::regclass);


--
-- Name: clinics id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clinics ALTER COLUMN id SET DEFAULT nextval('public.clinics_id_seq'::regclass);


--
-- Name: doctor_availability id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.doctor_availability ALTER COLUMN id SET DEFAULT nextval('public.doctor_availability_id_seq'::regclass);


--
-- Name: doctors id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.doctors ALTER COLUMN id SET DEFAULT nextval('public.doctors_id_seq'::regclass);


--
-- Name: patients id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.patients ALTER COLUMN id SET DEFAULT nextval('public.patients_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: appointment_slots appointment_slots_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.appointment_slots
    ADD CONSTRAINT appointment_slots_pkey PRIMARY KEY (id);


--
-- Name: appointments appointments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.appointments
    ADD CONSTRAINT appointments_pkey PRIMARY KEY (id);


--
-- Name: clinics clinics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clinics
    ADD CONSTRAINT clinics_pkey PRIMARY KEY (id);


--
-- Name: doctor_availability doctor_availability_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.doctor_availability
    ADD CONSTRAINT doctor_availability_pkey PRIMARY KEY (id);


--
-- Name: doctors doctors_license_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.doctors
    ADD CONSTRAINT doctors_license_number_key UNIQUE (license_number);


--
-- Name: doctors doctors_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.doctors
    ADD CONSTRAINT doctors_pkey PRIMARY KEY (id);


--
-- Name: patients patients_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.patients
    ADD CONSTRAINT patients_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_appointment_slots_clinic_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_appointment_slots_clinic_id ON public.appointment_slots USING btree (clinic_id);


--
-- Name: ix_appointment_slots_doctor_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_appointment_slots_doctor_id ON public.appointment_slots USING btree (doctor_id);


--
-- Name: ix_appointments_doctor_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_appointments_doctor_id ON public.appointments USING btree (doctor_id);


--
-- Name: ix_appointments_patient_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_appointments_patient_id ON public.appointments USING btree (patient_id);


--
-- Name: ix_appointments_slot_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_appointments_slot_id ON public.appointments USING btree (slot_id);


--
-- Name: ix_clinics_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_clinics_name ON public.clinics USING btree (name);


--
-- Name: ix_doctor_availability_doctor_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_doctor_availability_doctor_id ON public.doctor_availability USING btree (doctor_id);


--
-- Name: ix_doctors_clinic_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_doctors_clinic_id ON public.doctors USING btree (clinic_id);


--
-- Name: ix_doctors_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_doctors_user_id ON public.doctors USING btree (user_id);


--
-- Name: ix_patients_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_patients_user_id ON public.patients USING btree (user_id);


--
-- Name: ix_slots_clinic_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_slots_clinic_id ON public.appointment_slots USING btree (clinic_id);


--
-- Name: ix_slots_doctor_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_slots_doctor_id ON public.appointment_slots USING btree (doctor_id);


--
-- Name: ix_slots_start_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_slots_start_time ON public.appointment_slots USING btree (start_time);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- PostgreSQL database dump complete
--

\unrestrict T00Dx81yGUvAnqsEaymggqOpX4aaM8hkUVywfb8xFfdW5q5VPslbDvUbvaAiqGP

