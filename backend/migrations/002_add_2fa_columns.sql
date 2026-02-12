-- Migración 002: Agregar columnas 2FA a la tabla users
-- Ejecutar: psql -U <usuario> -d <base_de_datos> -f migrations/002_add_2fa_columns.sql

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS two_factor_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS two_factor_secret VARCHAR(255),
    ADD COLUMN IF NOT EXISTS two_factor_backup_codes TEXT[];
