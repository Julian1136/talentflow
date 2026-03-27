--
-- PostgreSQL database dump
--

\restrict 8wTTE7gmfrWJHfWwHOo2MxObxsxZtAhsUGoTcNpHbNqICYblNFKRjtqchD4eIIW

-- Dumped from database version 18.2
-- Dumped by pg_dump version 18.2

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
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: aplicaciones; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.aplicaciones (
    id integer NOT NULL,
    cedula_candidato character varying(20) NOT NULL,
    id_vacante integer NOT NULL,
    estado character varying(60) DEFAULT 'hoja_de_vida_recibida'::character varying,
    fecha_aplicacion timestamp without time zone DEFAULT now(),
    score numeric(5,2),
    analisis_ia_text text
);


--
-- Name: aplicaciones_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.aplicaciones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: aplicaciones_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.aplicaciones_id_seq OWNED BY public.aplicaciones.id;


--
-- Name: asignaciones_laborales; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.asignaciones_laborales (
    id integer NOT NULL,
    id_empleado integer NOT NULL,
    id_cargo integer NOT NULL,
    id_sede integer NOT NULL,
    id_jefe integer,
    fecha_inicio date DEFAULT CURRENT_DATE NOT NULL,
    fecha_fin date,
    salario numeric(12,2),
    es_actual boolean DEFAULT true NOT NULL,
    observaciones text,
    fecha_creacion timestamp without time zone DEFAULT now()
);


--
-- Name: asignaciones_laborales_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.asignaciones_laborales_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: asignaciones_laborales_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.asignaciones_laborales_id_seq OWNED BY public.asignaciones_laborales.id;


--
-- Name: auditoria_catalogos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auditoria_catalogos (
    id integer NOT NULL,
    entidad character varying(50) NOT NULL,
    id_entidad integer,
    accion character varying(40) NOT NULL,
    detalle text,
    id_usuario integer,
    fecha_evento timestamp without time zone DEFAULT now()
);


--
-- Name: auditoria_catalogos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.auditoria_catalogos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: auditoria_catalogos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.auditoria_catalogos_id_seq OWNED BY public.auditoria_catalogos.id;


--
-- Name: candidatos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.candidatos (
    cedula character varying(20) NOT NULL,
    nombres character varying(100) NOT NULL,
    apellidos character varying(100) NOT NULL,
    telefono character varying(20),
    correo character varying(150),
    direccion text,
    ciudad character varying(80),
    fecha_nacimiento date,
    fuente_captacion character varying(80),
    activo boolean DEFAULT true,
    fecha_registro timestamp without time zone DEFAULT now()
);


--
-- Name: cargos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cargos (
    id integer NOT NULL,
    codigo character varying(40) NOT NULL,
    nombre character varying(120) NOT NULL,
    area character varying(100),
    nivel character varying(50),
    competencias_json text,
    activo boolean DEFAULT true,
    fecha_creacion timestamp without time zone DEFAULT now()
);


--
-- Name: cargos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cargos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cargos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cargos_id_seq OWNED BY public.cargos.id;


--
-- Name: configuracion_tema; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.configuracion_tema (
    id integer NOT NULL,
    nombre character varying(100) DEFAULT 'Tema corporativo'::character varying NOT NULL,
    logo_texto character varying(100) DEFAULT 'TalentFlow'::character varying,
    color_primario character varying(12) DEFAULT '#2563eb'::character varying,
    color_secundario character varying(12) DEFAULT '#0f172a'::character varying,
    fondo character varying(12) DEFAULT '#f5f4f0'::character varying,
    superficie character varying(12) DEFAULT '#ffffff'::character varying,
    radio_px integer DEFAULT 10,
    actualizado_por integer,
    fecha_actualizacion timestamp without time zone DEFAULT now()
);


--
-- Name: configuracion_tema_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.configuracion_tema_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: configuracion_tema_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.configuracion_tema_id_seq OWNED BY public.configuracion_tema.id;


--
-- Name: contactos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.contactos (
    id integer NOT NULL,
    cedula_candidato character varying(20),
    id_aplicacion integer,
    id_usuario integer,
    fecha_contacto timestamp without time zone NOT NULL,
    canal character varying(50),
    resultado character varying(50),
    observaciones text,
    fecha_registro timestamp without time zone DEFAULT now()
);


--
-- Name: contactos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.contactos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: contactos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.contactos_id_seq OWNED BY public.contactos.id;


--
-- Name: correo_cola_reintento; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.correo_cola_reintento (
    id integer NOT NULL,
    destinatario character varying(255) NOT NULL,
    asunto character varying(500) NOT NULL,
    cuerpo_html text NOT NULL,
    intentos integer DEFAULT 0,
    max_intentos integer DEFAULT 5,
    ultimo_error text,
    proximo_intento_en timestamp without time zone,
    creado_en timestamp without time zone DEFAULT now(),
    enviado_en timestamp without time zone
);


--
-- Name: correo_cola_reintento_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.correo_cola_reintento_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: correo_cola_reintento_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.correo_cola_reintento_id_seq OWNED BY public.correo_cola_reintento.id;


--
-- Name: desvinculaciones; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.desvinculaciones (
    id integer NOT NULL,
    id_empleado integer NOT NULL,
    tipo character varying(40) NOT NULL,
    causa text,
    fecha_efectiva date NOT NULL,
    documento_ref character varying(255),
    id_usuario integer NOT NULL,
    fecha_registro timestamp without time zone DEFAULT now()
);


--
-- Name: desvinculaciones_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.desvinculaciones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: desvinculaciones_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.desvinculaciones_id_seq OWNED BY public.desvinculaciones.id;


--
-- Name: documentos_adjuntos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.documentos_adjuntos (
    id integer NOT NULL,
    cedula_candidato character varying(20),
    id_aplicacion integer,
    tipo_documento character varying(80),
    nombre_original character varying(255),
    nombre_archivo character varying(255),
    ruta_archivo character varying(500),
    tamano_bytes bigint,
    subido_por integer,
    fecha_subida timestamp without time zone DEFAULT now()
);


--
-- Name: documentos_adjuntos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.documentos_adjuntos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: documentos_adjuntos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.documentos_adjuntos_id_seq OWNED BY public.documentos_adjuntos.id;


--
-- Name: empleados; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.empleados (
    id integer NOT NULL,
    cedula character varying(20) NOT NULL,
    id_usuario integer,
    id_aplicacion_origen integer,
    estado_laboral character varying(30) DEFAULT 'activo'::character varying NOT NULL,
    fecha_ingreso date DEFAULT CURRENT_DATE,
    fecha_salida date,
    motivo_salida character varying(120),
    notas text,
    fecha_creacion timestamp without time zone DEFAULT now(),
    fecha_actualizacion timestamp without time zone DEFAULT now()
);


--
-- Name: empleados_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.empleados_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: empleados_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.empleados_id_seq OWNED BY public.empleados.id;


--
-- Name: entrevistas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.entrevistas (
    id integer NOT NULL,
    id_aplicacion integer NOT NULL,
    tipo character varying(50),
    fecha_programada timestamp without time zone,
    lugar character varying(150),
    id_entrevistador integer,
    resultado character varying(50) DEFAULT 'pendiente'::character varying,
    observaciones text,
    fecha_realizada timestamp without time zone,
    fecha_creacion timestamp without time zone DEFAULT now(),
    recordatorio_enviado_en timestamp without time zone
);


--
-- Name: entrevistas_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.entrevistas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: entrevistas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.entrevistas_id_seq OWNED BY public.entrevistas.id;


--
-- Name: evaluaciones_desempeno; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.evaluaciones_desempeno (
    id integer NOT NULL,
    id_empleado integer NOT NULL,
    id_plantilla integer NOT NULL,
    periodo character varying(40) NOT NULL,
    id_jefe_evaluador integer NOT NULL,
    puntaje_total numeric(6,2),
    detalle_json text NOT NULL,
    comentario_jefe text,
    estado_aceptacion character varying(30) DEFAULT 'pendiente_empleado'::character varying,
    comentario_empleado text,
    fecha_evaluacion date DEFAULT CURRENT_DATE,
    fecha_aceptacion timestamp without time zone,
    fecha_registro timestamp without time zone DEFAULT now()
);


--
-- Name: evaluaciones_desempeno_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.evaluaciones_desempeno_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: evaluaciones_desempeno_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.evaluaciones_desempeno_id_seq OWNED BY public.evaluaciones_desempeno.id;


--
-- Name: evaluaciones_plantilla_respuestas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.evaluaciones_plantilla_respuestas (
    id integer NOT NULL,
    id_aplicacion integer NOT NULL,
    id_plantilla integer NOT NULL,
    id_usuario integer NOT NULL,
    respuestas_json text NOT NULL,
    puntaje_total numeric(6,2),
    fecha_registro timestamp without time zone DEFAULT now()
);


--
-- Name: evaluaciones_plantilla_respuestas_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.evaluaciones_plantilla_respuestas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: evaluaciones_plantilla_respuestas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.evaluaciones_plantilla_respuestas_id_seq OWNED BY public.evaluaciones_plantilla_respuestas.id;


--
-- Name: evaluaciones_psicologicas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.evaluaciones_psicologicas (
    id integer NOT NULL,
    id_aplicacion integer NOT NULL,
    id_psicologo integer,
    tipo_evaluacion character varying(100),
    fecha_evaluacion date,
    resultado character varying(50),
    observaciones text,
    recomendaciones text,
    fecha_registro timestamp without time zone DEFAULT now()
);


--
-- Name: evaluaciones_psicologicas_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.evaluaciones_psicologicas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: evaluaciones_psicologicas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.evaluaciones_psicologicas_id_seq OWNED BY public.evaluaciones_psicologicas.id;


--
-- Name: evaluaciones_tecnicas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.evaluaciones_tecnicas (
    id integer NOT NULL,
    id_aplicacion integer NOT NULL,
    tipo character varying(80),
    nombre_prueba character varying(150),
    fecha_aplicacion date,
    puntaje numeric(5,2),
    puntaje_maximo numeric(5,2),
    resultado character varying(50),
    observaciones text,
    id_evaluador integer,
    fecha_registro timestamp without time zone DEFAULT now()
);


--
-- Name: evaluaciones_tecnicas_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.evaluaciones_tecnicas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: evaluaciones_tecnicas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.evaluaciones_tecnicas_id_seq OWNED BY public.evaluaciones_tecnicas.id;


--
-- Name: eventos_laborales; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.eventos_laborales (
    id integer NOT NULL,
    id_empleado integer NOT NULL,
    tipo_evento character varying(60) NOT NULL,
    descripcion character varying(200) NOT NULL,
    metadata_json text,
    id_usuario integer,
    fecha_evento timestamp without time zone DEFAULT now()
);


--
-- Name: eventos_laborales_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.eventos_laborales_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: eventos_laborales_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.eventos_laborales_id_seq OWNED BY public.eventos_laborales.id;


--
-- Name: firma_aceptaciones; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.firma_aceptaciones (
    id integer NOT NULL,
    token character varying(96) NOT NULL,
    id_aplicacion integer,
    cedula_candidato character varying(20),
    tipo_documento character varying(100),
    hash_documento character varying(128),
    ip_aceptacion character varying(64),
    user_agent text,
    fecha_aceptacion timestamp without time zone DEFAULT now()
);


--
-- Name: firma_aceptaciones_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.firma_aceptaciones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: firma_aceptaciones_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.firma_aceptaciones_id_seq OWNED BY public.firma_aceptaciones.id;


--
-- Name: historial_procesos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.historial_procesos (
    id integer NOT NULL,
    cedula_candidato character varying(20),
    id_aplicacion integer,
    id_usuario integer,
    accion character varying(150) NOT NULL,
    estado_anterior character varying(80),
    estado_nuevo character varying(80),
    observaciones text,
    fecha_accion timestamp without time zone DEFAULT now()
);


--
-- Name: historial_procesos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.historial_procesos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: historial_procesos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.historial_procesos_id_seq OWNED BY public.historial_procesos.id;


--
-- Name: hojas_de_vida; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.hojas_de_vida (
    id integer NOT NULL,
    cedula_candidato character varying(20) NOT NULL,
    experiencia_laboral jsonb,
    formacion_academica jsonb,
    habilidades text[],
    idiomas text[],
    resumen_profesional text,
    fecha_actualizacion timestamp without time zone DEFAULT now()
);


--
-- Name: hojas_de_vida_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.hojas_de_vida_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: hojas_de_vida_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.hojas_de_vida_id_seq OWNED BY public.hojas_de_vida.id;


--
-- Name: movimientos_laborales; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.movimientos_laborales (
    id integer NOT NULL,
    id_empleado integer NOT NULL,
    tipo character varying(40) NOT NULL,
    id_asignacion_anterior integer,
    id_asignacion_nueva integer,
    fecha_movimiento date DEFAULT CURRENT_DATE NOT NULL,
    motivo text,
    id_usuario integer NOT NULL,
    fecha_registro timestamp without time zone DEFAULT now()
);


--
-- Name: movimientos_laborales_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.movimientos_laborales_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: movimientos_laborales_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.movimientos_laborales_id_seq OWNED BY public.movimientos_laborales.id;


--
-- Name: notas_internas_aplicacion; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.notas_internas_aplicacion (
    id integer NOT NULL,
    id_aplicacion integer NOT NULL,
    id_usuario integer,
    cuerpo text NOT NULL,
    fecha_creacion timestamp without time zone DEFAULT now()
);


--
-- Name: notas_internas_aplicacion_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.notas_internas_aplicacion_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: notas_internas_aplicacion_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.notas_internas_aplicacion_id_seq OWNED BY public.notas_internas_aplicacion.id;


--
-- Name: novedades_disciplinarias; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.novedades_disciplinarias (
    id integer NOT NULL,
    id_empleado integer NOT NULL,
    tipo character varying(50) NOT NULL,
    severidad character varying(30),
    descripcion text NOT NULL,
    estado character varying(30) DEFAULT 'registrada'::character varying,
    fecha_falta date DEFAULT CURRENT_DATE,
    fecha_registro timestamp without time zone DEFAULT now(),
    id_reporta integer NOT NULL,
    id_aprueba integer,
    sancion text
);


--
-- Name: novedades_disciplinarias_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.novedades_disciplinarias_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: novedades_disciplinarias_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.novedades_disciplinarias_id_seq OWNED BY public.novedades_disciplinarias.id;


--
-- Name: plantillas_desempeno_cargo; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plantillas_desempeno_cargo (
    id integer NOT NULL,
    id_cargo integer NOT NULL,
    nombre character varying(200) NOT NULL,
    version integer DEFAULT 1 NOT NULL,
    criterios_json text NOT NULL,
    activa boolean DEFAULT true,
    fecha_creacion timestamp without time zone DEFAULT now()
);


--
-- Name: plantillas_desempeno_cargo_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.plantillas_desempeno_cargo_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: plantillas_desempeno_cargo_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.plantillas_desempeno_cargo_id_seq OWNED BY public.plantillas_desempeno_cargo.id;


--
-- Name: plantillas_evaluacion; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plantillas_evaluacion (
    id integer NOT NULL,
    nombre character varying(200) NOT NULL,
    criterios_json text NOT NULL,
    activa boolean DEFAULT true,
    fecha_creacion timestamp without time zone DEFAULT now()
);


--
-- Name: plantillas_evaluacion_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.plantillas_evaluacion_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: plantillas_evaluacion_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.plantillas_evaluacion_id_seq OWNED BY public.plantillas_evaluacion.id;


--
-- Name: roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.roles (
    id integer NOT NULL,
    nombre character varying(50) NOT NULL,
    descripcion text
);


--
-- Name: roles_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.roles_id_seq OWNED BY public.roles.id;


--
-- Name: sedes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sedes (
    id integer NOT NULL,
    codigo character varying(30) NOT NULL,
    nombre character varying(120) NOT NULL,
    ciudad character varying(80),
    direccion character varying(255),
    activa boolean DEFAULT true,
    fecha_creacion timestamp without time zone DEFAULT now()
);


--
-- Name: sedes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sedes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sedes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sedes_id_seq OWNED BY public.sedes.id;


--
-- Name: tareas_onboarding_empleado; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tareas_onboarding_empleado (
    id integer NOT NULL,
    id_empleado integer NOT NULL,
    titulo character varying(200) NOT NULL,
    hecha boolean DEFAULT false,
    orden integer DEFAULT 0,
    fecha_creacion timestamp without time zone DEFAULT now()
);


--
-- Name: tareas_onboarding_empleado_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tareas_onboarding_empleado_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tareas_onboarding_empleado_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tareas_onboarding_empleado_id_seq OWNED BY public.tareas_onboarding_empleado.id;


--
-- Name: usuarios; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.usuarios (
    id integer NOT NULL,
    cedula character varying(20) NOT NULL,
    nombres character varying(100) NOT NULL,
    apellidos character varying(100) NOT NULL,
    correo character varying(150) NOT NULL,
    password_hash character varying(255) NOT NULL,
    id_rol integer NOT NULL,
    activo boolean DEFAULT true,
    fecha_creacion timestamp without time zone DEFAULT now()
);


--
-- Name: usuarios_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: usuarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.usuarios_id_seq OWNED BY public.usuarios.id;


--
-- Name: vacantes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vacantes (
    id integer NOT NULL,
    titulo character varying(150) NOT NULL,
    descripcion text,
    area character varying(100),
    ciudad character varying(80),
    tipo_contrato character varying(50),
    salario_min numeric(12,2),
    salario_max numeric(12,2),
    requisitos text,
    estado character varying(30) DEFAULT 'abierta'::character varying,
    id_responsable integer,
    fecha_apertura date DEFAULT CURRENT_DATE,
    fecha_cierre date,
    fecha_creacion timestamp without time zone DEFAULT now()
);


--
-- Name: vacantes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.vacantes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: vacantes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.vacantes_id_seq OWNED BY public.vacantes.id;


--
-- Name: aplicaciones id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.aplicaciones ALTER COLUMN id SET DEFAULT nextval('public.aplicaciones_id_seq'::regclass);


--
-- Name: asignaciones_laborales id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.asignaciones_laborales ALTER COLUMN id SET DEFAULT nextval('public.asignaciones_laborales_id_seq'::regclass);


--
-- Name: auditoria_catalogos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auditoria_catalogos ALTER COLUMN id SET DEFAULT nextval('public.auditoria_catalogos_id_seq'::regclass);


--
-- Name: cargos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cargos ALTER COLUMN id SET DEFAULT nextval('public.cargos_id_seq'::regclass);


--
-- Name: configuracion_tema id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.configuracion_tema ALTER COLUMN id SET DEFAULT nextval('public.configuracion_tema_id_seq'::regclass);


--
-- Name: contactos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contactos ALTER COLUMN id SET DEFAULT nextval('public.contactos_id_seq'::regclass);


--
-- Name: correo_cola_reintento id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.correo_cola_reintento ALTER COLUMN id SET DEFAULT nextval('public.correo_cola_reintento_id_seq'::regclass);


--
-- Name: desvinculaciones id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.desvinculaciones ALTER COLUMN id SET DEFAULT nextval('public.desvinculaciones_id_seq'::regclass);


--
-- Name: documentos_adjuntos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documentos_adjuntos ALTER COLUMN id SET DEFAULT nextval('public.documentos_adjuntos_id_seq'::regclass);


--
-- Name: empleados id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.empleados ALTER COLUMN id SET DEFAULT nextval('public.empleados_id_seq'::regclass);


--
-- Name: entrevistas id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entrevistas ALTER COLUMN id SET DEFAULT nextval('public.entrevistas_id_seq'::regclass);


--
-- Name: evaluaciones_desempeno id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluaciones_desempeno ALTER COLUMN id SET DEFAULT nextval('public.evaluaciones_desempeno_id_seq'::regclass);


--
-- Name: evaluaciones_plantilla_respuestas id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluaciones_plantilla_respuestas ALTER COLUMN id SET DEFAULT nextval('public.evaluaciones_plantilla_respuestas_id_seq'::regclass);


--
-- Name: evaluaciones_psicologicas id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluaciones_psicologicas ALTER COLUMN id SET DEFAULT nextval('public.evaluaciones_psicologicas_id_seq'::regclass);


--
-- Name: evaluaciones_tecnicas id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluaciones_tecnicas ALTER COLUMN id SET DEFAULT nextval('public.evaluaciones_tecnicas_id_seq'::regclass);


--
-- Name: eventos_laborales id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eventos_laborales ALTER COLUMN id SET DEFAULT nextval('public.eventos_laborales_id_seq'::regclass);


--
-- Name: firma_aceptaciones id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.firma_aceptaciones ALTER COLUMN id SET DEFAULT nextval('public.firma_aceptaciones_id_seq'::regclass);


--
-- Name: historial_procesos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.historial_procesos ALTER COLUMN id SET DEFAULT nextval('public.historial_procesos_id_seq'::regclass);


--
-- Name: hojas_de_vida id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hojas_de_vida ALTER COLUMN id SET DEFAULT nextval('public.hojas_de_vida_id_seq'::regclass);


--
-- Name: movimientos_laborales id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimientos_laborales ALTER COLUMN id SET DEFAULT nextval('public.movimientos_laborales_id_seq'::regclass);


--
-- Name: notas_internas_aplicacion id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notas_internas_aplicacion ALTER COLUMN id SET DEFAULT nextval('public.notas_internas_aplicacion_id_seq'::regclass);


--
-- Name: novedades_disciplinarias id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.novedades_disciplinarias ALTER COLUMN id SET DEFAULT nextval('public.novedades_disciplinarias_id_seq'::regclass);


--
-- Name: plantillas_desempeno_cargo id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plantillas_desempeno_cargo ALTER COLUMN id SET DEFAULT nextval('public.plantillas_desempeno_cargo_id_seq'::regclass);


--
-- Name: plantillas_evaluacion id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plantillas_evaluacion ALTER COLUMN id SET DEFAULT nextval('public.plantillas_evaluacion_id_seq'::regclass);


--
-- Name: roles id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles ALTER COLUMN id SET DEFAULT nextval('public.roles_id_seq'::regclass);


--
-- Name: sedes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sedes ALTER COLUMN id SET DEFAULT nextval('public.sedes_id_seq'::regclass);


--
-- Name: tareas_onboarding_empleado id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tareas_onboarding_empleado ALTER COLUMN id SET DEFAULT nextval('public.tareas_onboarding_empleado_id_seq'::regclass);


--
-- Name: usuarios id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuarios ALTER COLUMN id SET DEFAULT nextval('public.usuarios_id_seq'::regclass);


--
-- Name: vacantes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vacantes ALTER COLUMN id SET DEFAULT nextval('public.vacantes_id_seq'::regclass);


--
-- Data for Name: aplicaciones; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.aplicaciones (id, cedula_candidato, id_vacante, estado, fecha_aplicacion, score, analisis_ia_text) FROM stdin;
1	1007819715	1	contratado	2026-03-25 19:44:42.579904	20.00	\N
\.


--
-- Data for Name: asignaciones_laborales; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.asignaciones_laborales (id, id_empleado, id_cargo, id_sede, id_jefe, fecha_inicio, fecha_fin, salario, es_actual, observaciones, fecha_creacion) FROM stdin;
1	1	1	1	1	2026-03-27	\N	\N	t	Asignación inicial generada al contratar.	2026-03-27 15:59:36.474691
\.


--
-- Data for Name: auditoria_catalogos; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auditoria_catalogos (id, entidad, id_entidad, accion, detalle, id_usuario, fecha_evento) FROM stdin;
\.


--
-- Data for Name: candidatos; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.candidatos (cedula, nombres, apellidos, telefono, correo, direccion, ciudad, fecha_nacimiento, fuente_captacion, activo, fecha_registro) FROM stdin;
1007819715	Julian Eduardo	Gonzalez Ortiz	3208624965	julian87668@gmail.com	calle 5 # ejemplo	facatativa	\N	Elempleo	t	2026-03-25 18:29:10.905324
\.


--
-- Data for Name: cargos; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.cargos (id, codigo, nombre, area, nivel, competencias_json, activo, fecha_creacion) FROM stdin;
1	ANL-SYS	Analista de Sistemas	Tecnología	Profesional	\N	t	2026-03-27 10:30:14.464408
2	JEF-OPS	Jefe de Operaciones	Operaciones	Jefatura	\N	t	2026-03-27 10:30:14.464408
\.


--
-- Data for Name: configuracion_tema; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.configuracion_tema (id, nombre, logo_texto, color_primario, color_secundario, fondo, superficie, radio_px, actualizado_por, fecha_actualizacion) FROM stdin;
1	Tema corporativo	TalentFlow	#2563eb	#f40b0b	#ffffff	#ffffff	10	1	2026-03-27 15:31:48.713416
\.


--
-- Data for Name: contactos; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.contactos (id, cedula_candidato, id_aplicacion, id_usuario, fecha_contacto, canal, resultado, observaciones, fecha_registro) FROM stdin;
1	1007819715	1	1	2026-03-27 10:33:00	telefono	exitoso		2026-03-27 15:33:26.57203
\.


--
-- Data for Name: correo_cola_reintento; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.correo_cola_reintento (id, destinatario, asunto, cuerpo_html, intentos, max_intentos, ultimo_error, proximo_intento_en, creado_en, enviado_en) FROM stdin;
\.


--
-- Data for Name: desvinculaciones; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.desvinculaciones (id, id_empleado, tipo, causa, fecha_efectiva, documento_ref, id_usuario, fecha_registro) FROM stdin;
\.


--
-- Data for Name: documentos_adjuntos; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.documentos_adjuntos (id, cedula_candidato, id_aplicacion, tipo_documento, nombre_original, nombre_archivo, ruta_archivo, tamano_bytes, subido_por, fecha_subida) FROM stdin;
1	1007819715	\N	hoja_de_vida	Cv_JULIAN_GONZALEZ_.pdf	ea902348e21244babf57a1fe78ba5815.pdf	C:\\xampp\\htdocs\\talentflow-main\\uploads/candidatos\\1007819715\\hoja_de_vida\\ea902348e21244babf57a1fe78ba5815.pdf	113636	1	2026-03-25 18:29:10.948646
\.


--
-- Data for Name: empleados; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.empleados (id, cedula, id_usuario, id_aplicacion_origen, estado_laboral, fecha_ingreso, fecha_salida, motivo_salida, notas, fecha_creacion, fecha_actualizacion) FROM stdin;
1	1007819715	\N	1	activo	2026-03-27	\N	\N	\N	2026-03-27 15:59:36.470938	2026-03-27 15:59:36.470938
\.


--
-- Data for Name: entrevistas; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.entrevistas (id, id_aplicacion, tipo, fecha_programada, lugar, id_entrevistador, resultado, observaciones, fecha_realizada, fecha_creacion, recordatorio_enviado_en) FROM stdin;
1	1	reclutador	2026-03-27 10:33:00	aca	1	apto		2026-03-27 15:57:21.232306	2026-03-27 15:33:53.092205	\N
\.


--
-- Data for Name: evaluaciones_desempeno; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.evaluaciones_desempeno (id, id_empleado, id_plantilla, periodo, id_jefe_evaluador, puntaje_total, detalle_json, comentario_jefe, estado_aceptacion, comentario_empleado, fecha_evaluacion, fecha_aceptacion, fecha_registro) FROM stdin;
\.


--
-- Data for Name: evaluaciones_plantilla_respuestas; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.evaluaciones_plantilla_respuestas (id, id_aplicacion, id_plantilla, id_usuario, respuestas_json, puntaje_total, fecha_registro) FROM stdin;
1	1	1	1	{"comunicacion": 5.0, "tecnico": 5.0, "actitud": 5.0}	100.00	2026-03-27 15:59:07.268934
\.


--
-- Data for Name: evaluaciones_psicologicas; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.evaluaciones_psicologicas (id, id_aplicacion, id_psicologo, tipo_evaluacion, fecha_evaluacion, resultado, observaciones, recomendaciones, fecha_registro) FROM stdin;
1	1	1	Entrevista psicológica	2026-03-27	apto	ninguna	ninguna	2026-03-27 15:57:53.397671
\.


--
-- Data for Name: evaluaciones_tecnicas; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.evaluaciones_tecnicas (id, id_aplicacion, tipo, nombre_prueba, fecha_aplicacion, puntaje, puntaje_maximo, resultado, observaciones, id_evaluador, fecha_registro) FROM stdin;
1	1	tecnica	Excel avanzado	2026-03-27	85.00	100.00	aprobado	ninguno	1	2026-03-27 15:58:26.19173
\.


--
-- Data for Name: eventos_laborales; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.eventos_laborales (id, id_empleado, tipo_evento, descripcion, metadata_json, id_usuario, fecha_evento) FROM stdin;
1	1	contratacion	Empleado creado a partir de proceso de selección.	{"id_aplicacion": 1}	1	2026-03-27 15:59:36.546275
\.


--
-- Data for Name: firma_aceptaciones; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.firma_aceptaciones (id, token, id_aplicacion, cedula_candidato, tipo_documento, hash_documento, ip_aceptacion, user_agent, fecha_aceptacion) FROM stdin;
1	OwBWhA9f_IMeYJc1DfkwzEcKkjI22IUp8M-svs7CpFI	1	1007819715	contrato_oferta	13fefff94daa162307aa09495a0184d4800d49b33aae8aa545e63ec155515c4f	\N	\N	2026-03-26 21:56:03.061053
\.


--
-- Data for Name: historial_procesos; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.historial_procesos (id, cedula_candidato, id_aplicacion, id_usuario, accion, estado_anterior, estado_nuevo, observaciones, fecha_accion) FROM stdin;
1	1007819715	\N	1	Candidato registrado en el sistema	\N	\N	\N	2026-03-25 18:29:10.92068
2	1007819715	1	1	Aplicación creada	\N	hoja_de_vida_recibida	\N	2026-03-25 19:44:42.615111
3	1007819715	1	1	Contacto registrado	hoja_de_vida_recibida	contactado	\N	2026-03-27 15:33:26.584526
4	1007819715	1	1	Contacto vía telefono: exitoso	\N	\N	\N	2026-03-27 15:33:26.584526
5	1007819715	1	1	Entrevista programada	contactado	entrevista_programada	Tipo: reclutador, Lugar: aca	2026-03-27 15:33:53.097143
6	1007819715	1	1	Entrevista realizada — resultado: apto	entrevista_programada	entrevista_realizada		2026-03-27 15:57:21.246599
7	1007819715	1	1	Evaluación psicológica registrada — apto	entrevista_realizada	en_pruebas_tecnicas	\N	2026-03-27 15:57:53.404483
8	1007819715	1	1	Prueba técnica 'Excel avanzado' — aprobado	\N	\N	\N	2026-03-27 15:58:26.192813
9	1007819715	1	1	Evaluación con plantilla «Entrevista estándar RRHH» — puntaje 100.0	\N	\N	\N	2026-03-27 15:59:07.274565
10	1007819715	1	1	Estado cambiado: en_pruebas_tecnicas → contratado	en_pruebas_tecnicas	contratado		2026-03-27 15:59:36.445541
\.


--
-- Data for Name: hojas_de_vida; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.hojas_de_vida (id, cedula_candidato, experiencia_laboral, formacion_academica, habilidades, idiomas, resumen_profesional, fecha_actualizacion) FROM stdin;
1	1007819715	[]	[]	{Python,SQL,Liderazgo}	\N	Python, SQL, Liderazgo	2026-03-25 18:29:10.909702
\.


--
-- Data for Name: movimientos_laborales; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.movimientos_laborales (id, id_empleado, tipo, id_asignacion_anterior, id_asignacion_nueva, fecha_movimiento, motivo, id_usuario, fecha_registro) FROM stdin;
1	1	ingreso	\N	1	2026-03-27	Ingreso desde aplicación #1	1	2026-03-27 15:59:36.554267
\.


--
-- Data for Name: notas_internas_aplicacion; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.notas_internas_aplicacion (id, id_aplicacion, id_usuario, cuerpo, fecha_creacion) FROM stdin;
\.


--
-- Data for Name: novedades_disciplinarias; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.novedades_disciplinarias (id, id_empleado, tipo, severidad, descripcion, estado, fecha_falta, fecha_registro, id_reporta, id_aprueba, sancion) FROM stdin;
\.


--
-- Data for Name: plantillas_desempeno_cargo; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.plantillas_desempeno_cargo (id, id_cargo, nombre, version, criterios_json, activa, fecha_creacion) FROM stdin;
1	1	Desempeño base Analista de Sistemas	1	[{"id":"mantenimientos","texto":"Cumplimiento de mantenimientos planificados","peso":4,"max":10},{"id":"tickets","texto":"Resolución de tickets del área","peso":3,"max":10},{"id":"documentacion","texto":"Documentación técnica y reportes","peso":3,"max":10}]	t	2026-03-27 10:30:14.466992
\.


--
-- Data for Name: plantillas_evaluacion; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.plantillas_evaluacion (id, nombre, criterios_json, activa, fecha_creacion) FROM stdin;
1	Entrevista estándar RRHH	[{"id":"comunicacion","texto":"Comunicación y claridad","peso":1,"max":5},{"id":"tecnico","texto":"Conocimiento técnico del cargo","peso":2,"max":5},{"id":"actitud","texto":"Actitud y ajuste cultural","peso":1,"max":5}]	t	2026-03-25 14:39:18.538233
\.


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.roles (id, nombre, descripcion) FROM stdin;
1	administrador	Rol de administrador
2	reclutador	Rol de reclutador
3	psicologo	Rol de psicologo
4	jefe_area	Rol de jefe de area
\.


--
-- Data for Name: sedes; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.sedes (id, codigo, nombre, ciudad, direccion, activa, fecha_creacion) FROM stdin;
1	PRINCIPAL	Sede Principal	N/D	N/D	t	2026-03-27 10:30:14.462391
\.


--
-- Data for Name: tareas_onboarding_empleado; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tareas_onboarding_empleado (id, id_empleado, titulo, hecha, orden, fecha_creacion) FROM stdin;
\.


--
-- Data for Name: usuarios; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.usuarios (id, cedula, nombres, apellidos, correo, password_hash, id_rol, activo, fecha_creacion) FROM stdin;
1	1234567890	Admin	Sistema	admin@empresa.com	$2a$06$SaXxRm9Z7QavjZRjnEcEseIhX/YWM8QpwM5CAYWcfyOIaH3fXGfK.	1	t	2026-03-25 12:51:07.350952
2	1007819715	Julian Eduardo	Gonzalez Ortiz	admin1@empresa.com	scrypt:32768:8:1$T9rpzL0RxbwA58VY$b37014796e6a20e479eb1941b0ce9745929f3c188e76d1017f59d00d7768c95abe68f733d2ff2e81316b700bc14a81f3cdca9cc8f745d32d1c3298a1598336fd	3	t	2026-03-25 20:15:04.884627
4	1007819714	Julian Eduardo	Gonzalez Ortiz	admin3@empresa.com	scrypt:32768:8:1$EFQSuQGG8b0xj1rC$b2220c44c54770d6cad8b7bfbeb9a8b4d1b1a01eeb9ecd019f5ea88be6b7adf2a57538f6f63a981370116a137cd49d28403f2645a1450bb79ad6fc83cbebca01	2	t	2026-03-25 20:16:43.128424
5	1007819712	Julian Eduardo	Gonzalez Ortiz	admin4@empresa.com	scrypt:32768:8:1$wfHdidJcSKmDjh62$a3c6cab3318b3f217365eba2283d0ba6dc5c4f4116a1797e100624acda75bbeb8a6f4bdf666418e62175f1a6e085e5bc49c0f399911eecbc7f14579b8005d73a	4	t	2026-03-25 20:17:42.133858
\.


--
-- Data for Name: vacantes; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.vacantes (id, titulo, descripcion, area, ciudad, tipo_contrato, salario_min, salario_max, requisitos, estado, id_responsable, fecha_apertura, fecha_cierre, fecha_creacion) FROM stdin;
1	Analista de ejemplo	Indefinido	Ejemplo	faca	Indefinido	1800000.00	2500000.00	que sea regalado	abierta	1	2026-03-25	\N	2026-03-25 18:31:02.257411
\.


--
-- Name: aplicaciones_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.aplicaciones_id_seq', 1, true);


--
-- Name: asignaciones_laborales_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.asignaciones_laborales_id_seq', 1, true);


--
-- Name: auditoria_catalogos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auditoria_catalogos_id_seq', 1, false);


--
-- Name: cargos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cargos_id_seq', 2, true);


--
-- Name: configuracion_tema_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.configuracion_tema_id_seq', 1, false);


--
-- Name: contactos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.contactos_id_seq', 1, true);


--
-- Name: correo_cola_reintento_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.correo_cola_reintento_id_seq', 1, false);


--
-- Name: desvinculaciones_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.desvinculaciones_id_seq', 1, false);


--
-- Name: documentos_adjuntos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.documentos_adjuntos_id_seq', 1, true);


--
-- Name: empleados_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.empleados_id_seq', 1, true);


--
-- Name: entrevistas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.entrevistas_id_seq', 1, true);


--
-- Name: evaluaciones_desempeno_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.evaluaciones_desempeno_id_seq', 1, false);


--
-- Name: evaluaciones_plantilla_respuestas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.evaluaciones_plantilla_respuestas_id_seq', 1, true);


--
-- Name: evaluaciones_psicologicas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.evaluaciones_psicologicas_id_seq', 1, true);


--
-- Name: evaluaciones_tecnicas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.evaluaciones_tecnicas_id_seq', 1, true);


--
-- Name: eventos_laborales_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.eventos_laborales_id_seq', 1, true);


--
-- Name: firma_aceptaciones_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.firma_aceptaciones_id_seq', 1, true);


--
-- Name: historial_procesos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.historial_procesos_id_seq', 10, true);


--
-- Name: hojas_de_vida_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.hojas_de_vida_id_seq', 1, true);


--
-- Name: movimientos_laborales_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.movimientos_laborales_id_seq', 1, true);


--
-- Name: notas_internas_aplicacion_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.notas_internas_aplicacion_id_seq', 1, false);


--
-- Name: novedades_disciplinarias_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.novedades_disciplinarias_id_seq', 1, false);


--
-- Name: plantillas_desempeno_cargo_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.plantillas_desempeno_cargo_id_seq', 1, true);


--
-- Name: plantillas_evaluacion_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.plantillas_evaluacion_id_seq', 1, true);


--
-- Name: roles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.roles_id_seq', 4, true);


--
-- Name: sedes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.sedes_id_seq', 1, true);


--
-- Name: tareas_onboarding_empleado_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tareas_onboarding_empleado_id_seq', 1, false);


--
-- Name: usuarios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.usuarios_id_seq', 5, true);


--
-- Name: vacantes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.vacantes_id_seq', 1, true);


--
-- Name: aplicaciones aplicaciones_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.aplicaciones
    ADD CONSTRAINT aplicaciones_pkey PRIMARY KEY (id);


--
-- Name: asignaciones_laborales asignaciones_laborales_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.asignaciones_laborales
    ADD CONSTRAINT asignaciones_laborales_pkey PRIMARY KEY (id);


--
-- Name: auditoria_catalogos auditoria_catalogos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auditoria_catalogos
    ADD CONSTRAINT auditoria_catalogos_pkey PRIMARY KEY (id);


--
-- Name: candidatos candidatos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.candidatos
    ADD CONSTRAINT candidatos_pkey PRIMARY KEY (cedula);


--
-- Name: cargos cargos_codigo_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cargos
    ADD CONSTRAINT cargos_codigo_key UNIQUE (codigo);


--
-- Name: cargos cargos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cargos
    ADD CONSTRAINT cargos_pkey PRIMARY KEY (id);


--
-- Name: configuracion_tema configuracion_tema_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.configuracion_tema
    ADD CONSTRAINT configuracion_tema_pkey PRIMARY KEY (id);


--
-- Name: contactos contactos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contactos
    ADD CONSTRAINT contactos_pkey PRIMARY KEY (id);


--
-- Name: correo_cola_reintento correo_cola_reintento_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.correo_cola_reintento
    ADD CONSTRAINT correo_cola_reintento_pkey PRIMARY KEY (id);


--
-- Name: desvinculaciones desvinculaciones_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.desvinculaciones
    ADD CONSTRAINT desvinculaciones_pkey PRIMARY KEY (id);


--
-- Name: documentos_adjuntos documentos_adjuntos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documentos_adjuntos
    ADD CONSTRAINT documentos_adjuntos_pkey PRIMARY KEY (id);


--
-- Name: empleados empleados_cedula_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.empleados
    ADD CONSTRAINT empleados_cedula_key UNIQUE (cedula);


--
-- Name: empleados empleados_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.empleados
    ADD CONSTRAINT empleados_pkey PRIMARY KEY (id);


--
-- Name: entrevistas entrevistas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entrevistas
    ADD CONSTRAINT entrevistas_pkey PRIMARY KEY (id);


--
-- Name: evaluaciones_desempeno evaluaciones_desempeno_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluaciones_desempeno
    ADD CONSTRAINT evaluaciones_desempeno_pkey PRIMARY KEY (id);


--
-- Name: evaluaciones_plantilla_respuestas evaluaciones_plantilla_respuestas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluaciones_plantilla_respuestas
    ADD CONSTRAINT evaluaciones_plantilla_respuestas_pkey PRIMARY KEY (id);


--
-- Name: evaluaciones_psicologicas evaluaciones_psicologicas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluaciones_psicologicas
    ADD CONSTRAINT evaluaciones_psicologicas_pkey PRIMARY KEY (id);


--
-- Name: evaluaciones_tecnicas evaluaciones_tecnicas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluaciones_tecnicas
    ADD CONSTRAINT evaluaciones_tecnicas_pkey PRIMARY KEY (id);


--
-- Name: eventos_laborales eventos_laborales_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eventos_laborales
    ADD CONSTRAINT eventos_laborales_pkey PRIMARY KEY (id);


--
-- Name: firma_aceptaciones firma_aceptaciones_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.firma_aceptaciones
    ADD CONSTRAINT firma_aceptaciones_pkey PRIMARY KEY (id);


--
-- Name: firma_aceptaciones firma_aceptaciones_token_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.firma_aceptaciones
    ADD CONSTRAINT firma_aceptaciones_token_key UNIQUE (token);


--
-- Name: historial_procesos historial_procesos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.historial_procesos
    ADD CONSTRAINT historial_procesos_pkey PRIMARY KEY (id);


--
-- Name: hojas_de_vida hojas_de_vida_cedula_candidato_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hojas_de_vida
    ADD CONSTRAINT hojas_de_vida_cedula_candidato_key UNIQUE (cedula_candidato);


--
-- Name: hojas_de_vida hojas_de_vida_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hojas_de_vida
    ADD CONSTRAINT hojas_de_vida_pkey PRIMARY KEY (id);


--
-- Name: movimientos_laborales movimientos_laborales_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimientos_laborales
    ADD CONSTRAINT movimientos_laborales_pkey PRIMARY KEY (id);


--
-- Name: notas_internas_aplicacion notas_internas_aplicacion_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notas_internas_aplicacion
    ADD CONSTRAINT notas_internas_aplicacion_pkey PRIMARY KEY (id);


--
-- Name: novedades_disciplinarias novedades_disciplinarias_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.novedades_disciplinarias
    ADD CONSTRAINT novedades_disciplinarias_pkey PRIMARY KEY (id);


--
-- Name: plantillas_desempeno_cargo plantillas_desempeno_cargo_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plantillas_desempeno_cargo
    ADD CONSTRAINT plantillas_desempeno_cargo_pkey PRIMARY KEY (id);


--
-- Name: plantillas_evaluacion plantillas_evaluacion_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plantillas_evaluacion
    ADD CONSTRAINT plantillas_evaluacion_pkey PRIMARY KEY (id);


--
-- Name: roles roles_nombre_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_nombre_key UNIQUE (nombre);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: sedes sedes_codigo_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sedes
    ADD CONSTRAINT sedes_codigo_key UNIQUE (codigo);


--
-- Name: sedes sedes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sedes
    ADD CONSTRAINT sedes_pkey PRIMARY KEY (id);


--
-- Name: tareas_onboarding_empleado tareas_onboarding_empleado_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tareas_onboarding_empleado
    ADD CONSTRAINT tareas_onboarding_empleado_pkey PRIMARY KEY (id);


--
-- Name: aplicaciones uq_candidato_vacante; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.aplicaciones
    ADD CONSTRAINT uq_candidato_vacante UNIQUE (cedula_candidato, id_vacante);


--
-- Name: plantillas_desempeno_cargo uq_plantilla_desempeno_version; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plantillas_desempeno_cargo
    ADD CONSTRAINT uq_plantilla_desempeno_version UNIQUE (id_cargo, nombre, version);


--
-- Name: usuarios usuarios_cedula_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_cedula_key UNIQUE (cedula);


--
-- Name: usuarios usuarios_correo_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_correo_key UNIQUE (correo);


--
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);


--
-- Name: vacantes vacantes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vacantes
    ADD CONSTRAINT vacantes_pkey PRIMARY KEY (id);


--
-- Name: idx_aplicaciones_candidato; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_aplicaciones_candidato ON public.aplicaciones USING btree (cedula_candidato);


--
-- Name: idx_aplicaciones_estado; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_aplicaciones_estado ON public.aplicaciones USING btree (estado);


--
-- Name: idx_aplicaciones_vacante; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_aplicaciones_vacante ON public.aplicaciones USING btree (id_vacante);


--
-- Name: idx_asignaciones_empleado_actual; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_asignaciones_empleado_actual ON public.asignaciones_laborales USING btree (id_empleado, es_actual);


--
-- Name: idx_candidatos_activo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_candidatos_activo ON public.candidatos USING btree (activo);


--
-- Name: idx_empleados_estado_laboral; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_empleados_estado_laboral ON public.empleados USING btree (estado_laboral);


--
-- Name: idx_eval_desempeno_periodo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_eval_desempeno_periodo ON public.evaluaciones_desempeno USING btree (periodo, fecha_evaluacion DESC);


--
-- Name: idx_eval_plantilla_aplicacion; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_eval_plantilla_aplicacion ON public.evaluaciones_plantilla_respuestas USING btree (id_aplicacion);


--
-- Name: idx_eval_plantilla_plantilla; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_eval_plantilla_plantilla ON public.evaluaciones_plantilla_respuestas USING btree (id_plantilla);


--
-- Name: idx_eventos_laborales_empleado; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_eventos_laborales_empleado ON public.eventos_laborales USING btree (id_empleado, fecha_evento DESC);


--
-- Name: idx_firma_token; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_firma_token ON public.firma_aceptaciones USING btree (token);


--
-- Name: idx_historial_aplicacion; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_historial_aplicacion ON public.historial_procesos USING btree (id_aplicacion);


--
-- Name: idx_movimientos_empleado_fecha; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_movimientos_empleado_fecha ON public.movimientos_laborales USING btree (id_empleado, fecha_movimiento DESC);


--
-- Name: idx_novedades_estado; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_novedades_estado ON public.novedades_disciplinarias USING btree (estado, fecha_registro DESC);


--
-- Name: idx_usuarios_correo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_usuarios_correo ON public.usuarios USING btree (correo);


--
-- Name: idx_usuarios_rol; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_usuarios_rol ON public.usuarios USING btree (id_rol);


--
-- Name: idx_vacantes_estado; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_vacantes_estado ON public.vacantes USING btree (estado);


--
-- Name: ix_correo_cola_proximo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_correo_cola_proximo ON public.correo_cola_reintento USING btree (proximo_intento_en);


--
-- Name: ix_notas_internas_aplicacion; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_notas_internas_aplicacion ON public.notas_internas_aplicacion USING btree (id_aplicacion);


--
-- Name: ix_tareas_onboarding_empleado; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_tareas_onboarding_empleado ON public.tareas_onboarding_empleado USING btree (id_empleado);


--
-- Name: aplicaciones aplicaciones_cedula_candidato_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.aplicaciones
    ADD CONSTRAINT aplicaciones_cedula_candidato_fkey FOREIGN KEY (cedula_candidato) REFERENCES public.candidatos(cedula);


--
-- Name: aplicaciones aplicaciones_id_vacante_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.aplicaciones
    ADD CONSTRAINT aplicaciones_id_vacante_fkey FOREIGN KEY (id_vacante) REFERENCES public.vacantes(id);


--
-- Name: asignaciones_laborales asignaciones_laborales_id_cargo_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.asignaciones_laborales
    ADD CONSTRAINT asignaciones_laborales_id_cargo_fkey FOREIGN KEY (id_cargo) REFERENCES public.cargos(id);


--
-- Name: asignaciones_laborales asignaciones_laborales_id_empleado_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.asignaciones_laborales
    ADD CONSTRAINT asignaciones_laborales_id_empleado_fkey FOREIGN KEY (id_empleado) REFERENCES public.empleados(id);


--
-- Name: asignaciones_laborales asignaciones_laborales_id_jefe_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.asignaciones_laborales
    ADD CONSTRAINT asignaciones_laborales_id_jefe_fkey FOREIGN KEY (id_jefe) REFERENCES public.usuarios(id);


--
-- Name: asignaciones_laborales asignaciones_laborales_id_sede_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.asignaciones_laborales
    ADD CONSTRAINT asignaciones_laborales_id_sede_fkey FOREIGN KEY (id_sede) REFERENCES public.sedes(id);


--
-- Name: auditoria_catalogos auditoria_catalogos_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auditoria_catalogos
    ADD CONSTRAINT auditoria_catalogos_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuarios(id);


--
-- Name: configuracion_tema configuracion_tema_actualizado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.configuracion_tema
    ADD CONSTRAINT configuracion_tema_actualizado_por_fkey FOREIGN KEY (actualizado_por) REFERENCES public.usuarios(id);


--
-- Name: contactos contactos_cedula_candidato_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contactos
    ADD CONSTRAINT contactos_cedula_candidato_fkey FOREIGN KEY (cedula_candidato) REFERENCES public.candidatos(cedula);


--
-- Name: contactos contactos_id_aplicacion_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contactos
    ADD CONSTRAINT contactos_id_aplicacion_fkey FOREIGN KEY (id_aplicacion) REFERENCES public.aplicaciones(id);


--
-- Name: contactos contactos_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contactos
    ADD CONSTRAINT contactos_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuarios(id);


--
-- Name: desvinculaciones desvinculaciones_id_empleado_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.desvinculaciones
    ADD CONSTRAINT desvinculaciones_id_empleado_fkey FOREIGN KEY (id_empleado) REFERENCES public.empleados(id);


--
-- Name: desvinculaciones desvinculaciones_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.desvinculaciones
    ADD CONSTRAINT desvinculaciones_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuarios(id);


--
-- Name: documentos_adjuntos documentos_adjuntos_cedula_candidato_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documentos_adjuntos
    ADD CONSTRAINT documentos_adjuntos_cedula_candidato_fkey FOREIGN KEY (cedula_candidato) REFERENCES public.candidatos(cedula);


--
-- Name: documentos_adjuntos documentos_adjuntos_id_aplicacion_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documentos_adjuntos
    ADD CONSTRAINT documentos_adjuntos_id_aplicacion_fkey FOREIGN KEY (id_aplicacion) REFERENCES public.aplicaciones(id);


--
-- Name: documentos_adjuntos documentos_adjuntos_subido_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documentos_adjuntos
    ADD CONSTRAINT documentos_adjuntos_subido_por_fkey FOREIGN KEY (subido_por) REFERENCES public.usuarios(id);


--
-- Name: empleados empleados_cedula_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.empleados
    ADD CONSTRAINT empleados_cedula_fkey FOREIGN KEY (cedula) REFERENCES public.candidatos(cedula);


--
-- Name: empleados empleados_id_aplicacion_origen_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.empleados
    ADD CONSTRAINT empleados_id_aplicacion_origen_fkey FOREIGN KEY (id_aplicacion_origen) REFERENCES public.aplicaciones(id);


--
-- Name: empleados empleados_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.empleados
    ADD CONSTRAINT empleados_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuarios(id);


--
-- Name: entrevistas entrevistas_id_aplicacion_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entrevistas
    ADD CONSTRAINT entrevistas_id_aplicacion_fkey FOREIGN KEY (id_aplicacion) REFERENCES public.aplicaciones(id);


--
-- Name: entrevistas entrevistas_id_entrevistador_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entrevistas
    ADD CONSTRAINT entrevistas_id_entrevistador_fkey FOREIGN KEY (id_entrevistador) REFERENCES public.usuarios(id);


--
-- Name: evaluaciones_desempeno evaluaciones_desempeno_id_empleado_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluaciones_desempeno
    ADD CONSTRAINT evaluaciones_desempeno_id_empleado_fkey FOREIGN KEY (id_empleado) REFERENCES public.empleados(id);


--
-- Name: evaluaciones_desempeno evaluaciones_desempeno_id_jefe_evaluador_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluaciones_desempeno
    ADD CONSTRAINT evaluaciones_desempeno_id_jefe_evaluador_fkey FOREIGN KEY (id_jefe_evaluador) REFERENCES public.usuarios(id);


--
-- Name: evaluaciones_desempeno evaluaciones_desempeno_id_plantilla_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluaciones_desempeno
    ADD CONSTRAINT evaluaciones_desempeno_id_plantilla_fkey FOREIGN KEY (id_plantilla) REFERENCES public.plantillas_desempeno_cargo(id);


--
-- Name: evaluaciones_plantilla_respuestas evaluaciones_plantilla_respuestas_id_aplicacion_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluaciones_plantilla_respuestas
    ADD CONSTRAINT evaluaciones_plantilla_respuestas_id_aplicacion_fkey FOREIGN KEY (id_aplicacion) REFERENCES public.aplicaciones(id) ON DELETE CASCADE;


--
-- Name: evaluaciones_plantilla_respuestas evaluaciones_plantilla_respuestas_id_plantilla_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluaciones_plantilla_respuestas
    ADD CONSTRAINT evaluaciones_plantilla_respuestas_id_plantilla_fkey FOREIGN KEY (id_plantilla) REFERENCES public.plantillas_evaluacion(id) ON DELETE CASCADE;


--
-- Name: evaluaciones_plantilla_respuestas evaluaciones_plantilla_respuestas_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluaciones_plantilla_respuestas
    ADD CONSTRAINT evaluaciones_plantilla_respuestas_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuarios(id);


--
-- Name: evaluaciones_psicologicas evaluaciones_psicologicas_id_aplicacion_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluaciones_psicologicas
    ADD CONSTRAINT evaluaciones_psicologicas_id_aplicacion_fkey FOREIGN KEY (id_aplicacion) REFERENCES public.aplicaciones(id);


--
-- Name: evaluaciones_psicologicas evaluaciones_psicologicas_id_psicologo_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluaciones_psicologicas
    ADD CONSTRAINT evaluaciones_psicologicas_id_psicologo_fkey FOREIGN KEY (id_psicologo) REFERENCES public.usuarios(id);


--
-- Name: evaluaciones_tecnicas evaluaciones_tecnicas_id_aplicacion_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluaciones_tecnicas
    ADD CONSTRAINT evaluaciones_tecnicas_id_aplicacion_fkey FOREIGN KEY (id_aplicacion) REFERENCES public.aplicaciones(id);


--
-- Name: evaluaciones_tecnicas evaluaciones_tecnicas_id_evaluador_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluaciones_tecnicas
    ADD CONSTRAINT evaluaciones_tecnicas_id_evaluador_fkey FOREIGN KEY (id_evaluador) REFERENCES public.usuarios(id);


--
-- Name: eventos_laborales eventos_laborales_id_empleado_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eventos_laborales
    ADD CONSTRAINT eventos_laborales_id_empleado_fkey FOREIGN KEY (id_empleado) REFERENCES public.empleados(id);


--
-- Name: eventos_laborales eventos_laborales_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eventos_laborales
    ADD CONSTRAINT eventos_laborales_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuarios(id);


--
-- Name: firma_aceptaciones firma_aceptaciones_cedula_candidato_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.firma_aceptaciones
    ADD CONSTRAINT firma_aceptaciones_cedula_candidato_fkey FOREIGN KEY (cedula_candidato) REFERENCES public.candidatos(cedula) ON DELETE SET NULL;


--
-- Name: firma_aceptaciones firma_aceptaciones_id_aplicacion_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.firma_aceptaciones
    ADD CONSTRAINT firma_aceptaciones_id_aplicacion_fkey FOREIGN KEY (id_aplicacion) REFERENCES public.aplicaciones(id) ON DELETE SET NULL;


--
-- Name: historial_procesos historial_procesos_cedula_candidato_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.historial_procesos
    ADD CONSTRAINT historial_procesos_cedula_candidato_fkey FOREIGN KEY (cedula_candidato) REFERENCES public.candidatos(cedula);


--
-- Name: historial_procesos historial_procesos_id_aplicacion_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.historial_procesos
    ADD CONSTRAINT historial_procesos_id_aplicacion_fkey FOREIGN KEY (id_aplicacion) REFERENCES public.aplicaciones(id);


--
-- Name: historial_procesos historial_procesos_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.historial_procesos
    ADD CONSTRAINT historial_procesos_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuarios(id);


--
-- Name: hojas_de_vida hojas_de_vida_cedula_candidato_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hojas_de_vida
    ADD CONSTRAINT hojas_de_vida_cedula_candidato_fkey FOREIGN KEY (cedula_candidato) REFERENCES public.candidatos(cedula);


--
-- Name: movimientos_laborales movimientos_laborales_id_asignacion_anterior_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimientos_laborales
    ADD CONSTRAINT movimientos_laborales_id_asignacion_anterior_fkey FOREIGN KEY (id_asignacion_anterior) REFERENCES public.asignaciones_laborales(id);


--
-- Name: movimientos_laborales movimientos_laborales_id_asignacion_nueva_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimientos_laborales
    ADD CONSTRAINT movimientos_laborales_id_asignacion_nueva_fkey FOREIGN KEY (id_asignacion_nueva) REFERENCES public.asignaciones_laborales(id);


--
-- Name: movimientos_laborales movimientos_laborales_id_empleado_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimientos_laborales
    ADD CONSTRAINT movimientos_laborales_id_empleado_fkey FOREIGN KEY (id_empleado) REFERENCES public.empleados(id);


--
-- Name: movimientos_laborales movimientos_laborales_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimientos_laborales
    ADD CONSTRAINT movimientos_laborales_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuarios(id);


--
-- Name: notas_internas_aplicacion notas_internas_aplicacion_id_aplicacion_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notas_internas_aplicacion
    ADD CONSTRAINT notas_internas_aplicacion_id_aplicacion_fkey FOREIGN KEY (id_aplicacion) REFERENCES public.aplicaciones(id) ON DELETE CASCADE;


--
-- Name: notas_internas_aplicacion notas_internas_aplicacion_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notas_internas_aplicacion
    ADD CONSTRAINT notas_internas_aplicacion_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuarios(id);


--
-- Name: novedades_disciplinarias novedades_disciplinarias_id_aprueba_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.novedades_disciplinarias
    ADD CONSTRAINT novedades_disciplinarias_id_aprueba_fkey FOREIGN KEY (id_aprueba) REFERENCES public.usuarios(id);


--
-- Name: novedades_disciplinarias novedades_disciplinarias_id_empleado_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.novedades_disciplinarias
    ADD CONSTRAINT novedades_disciplinarias_id_empleado_fkey FOREIGN KEY (id_empleado) REFERENCES public.empleados(id);


--
-- Name: novedades_disciplinarias novedades_disciplinarias_id_reporta_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.novedades_disciplinarias
    ADD CONSTRAINT novedades_disciplinarias_id_reporta_fkey FOREIGN KEY (id_reporta) REFERENCES public.usuarios(id);


--
-- Name: plantillas_desempeno_cargo plantillas_desempeno_cargo_id_cargo_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plantillas_desempeno_cargo
    ADD CONSTRAINT plantillas_desempeno_cargo_id_cargo_fkey FOREIGN KEY (id_cargo) REFERENCES public.cargos(id);


--
-- Name: tareas_onboarding_empleado tareas_onboarding_empleado_id_empleado_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tareas_onboarding_empleado
    ADD CONSTRAINT tareas_onboarding_empleado_id_empleado_fkey FOREIGN KEY (id_empleado) REFERENCES public.empleados(id) ON DELETE CASCADE;


--
-- Name: usuarios usuarios_id_rol_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_id_rol_fkey FOREIGN KEY (id_rol) REFERENCES public.roles(id);


--
-- Name: vacantes vacantes_id_responsable_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vacantes
    ADD CONSTRAINT vacantes_id_responsable_fkey FOREIGN KEY (id_responsable) REFERENCES public.usuarios(id);


--
-- PostgreSQL database dump complete
--

\unrestrict 8wTTE7gmfrWJHfWwHOo2MxObxsxZtAhsUGoTcNpHbNqICYblNFKRjtqchD4eIIW

