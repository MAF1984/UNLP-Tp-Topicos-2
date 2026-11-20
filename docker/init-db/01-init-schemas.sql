-- =====================================================================
-- Script de Inicialización de Esquemas Lógicos - Ticketera Virtual
-- Trabajo Final Tópicos de Ingeniería de Software II (2026)
-- Estrategia: Database-per-Service Lógico sobre PostgreSQL (ADR 001)
-- =====================================================================

-- Extensiones globales requeridas
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Esquemas aislados por Bounded Context
CREATE SCHEMA IF NOT EXISTS identity;
CREATE SCHEMA IF NOT EXISTS catalog;
CREATE SCHEMA IF NOT EXISTS ticketing;
CREATE SCHEMA IF NOT EXISTS payments;
CREATE SCHEMA IF NOT EXISTS reco;

-- Configuración de permisos y comentarios
COMMENT ON SCHEMA identity IS 'Bounded Context: Usuarios, credenciales, roles y tokens (ADR 010)';
COMMENT ON SCHEMA catalog IS 'Bounded Context: Eventos, organizadores, participantes y sedes (ADR 006)';
COMMENT ON SCHEMA ticketing IS 'Bounded Context: Inventario numerado y por zonas, holds, órdenes y tickets (ADR 002, 011)';
COMMENT ON SCHEMA payments IS 'Bounded Context: Adaptador de pasarela de pagos, transacciones y reembolsos (ADR 009)';
COMMENT ON SCHEMA reco IS 'Bounded Context: Motor de recomendaciones y métricas de afinidad (ADR 007)';
