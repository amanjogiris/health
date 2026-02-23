"""Add comprehensive health app models

Revision ID: 4021fb30b726
Revises: 4021fb30b725
Create Date: 2024-02-24 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4021fb30b726'
down_revision = '4021fb30b725'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create appointment_status enum type
    op.execute("CREATE TYPE appointment_status AS ENUM ('pending', 'confirmed', 'cancelled', 'completed', 'no_show')")

    # Create patients table
    op.create_table(
        'patients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('date_of_birth', sa.String(length=10), nullable=True),
        sa.Column('blood_group', sa.String(length=5), nullable=True),
        sa.Column('allergies', sa.Text(), nullable=True),
        sa.Column('emergency_contact', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index('ix_patients_user_id', 'patients', ['user_id'])

    # Create clinics table
    op.create_table(
        'clinics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('address', sa.Text(), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('state', sa.String(length=100), nullable=False),
        sa.Column('zip_code', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_clinics_name', 'clinics', ['name'])

    # Create doctors table
    op.create_table(
        'doctors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('clinic_id', sa.Integer(), nullable=False),
        sa.Column('specialty', sa.String(length=100), nullable=False),
        sa.Column('license_number', sa.String(length=50), nullable=False),
        sa.Column('qualifications', sa.Text(), nullable=True),
        sa.Column('experience_years', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_patients_per_day', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ),
        sa.UniqueConstraint('user_id'),
        sa.UniqueConstraint('license_number'),
    )
    op.create_index('ix_doctors_user_id', 'doctors', ['user_id'])
    op.create_index('ix_doctors_clinic_id', 'doctors', ['clinic_id'])

    # Create appointment_slots table
    op.create_table(
        'appointment_slots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('doctor_id', sa.Integer(), nullable=False),
        sa.Column('clinic_id', sa.Integer(), nullable=False),
        sa.Column('slot_datetime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('is_booked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('capacity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('booked_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ),
        sa.ForeignKeyConstraint(['doctor_id'], ['doctors.id'], ),
    )
    op.create_index('ix_slots_doctor_id', 'appointment_slots', ['doctor_id'])
    op.create_index('ix_slots_clinic_id', 'appointment_slots', ['clinic_id'])
    op.create_index('ix_slots_slot_datetime', 'appointment_slots', ['slot_datetime'])

    # Create appointments table
    op.create_table(
        'appointments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('doctor_id', sa.Integer(), nullable=False),
        sa.Column('clinic_id', sa.Integer(), nullable=False),
        sa.Column('slot_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('reason_for_visit', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ),
        sa.ForeignKeyConstraint(['doctor_id'], ['doctors.id'], ),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
        sa.ForeignKeyConstraint(['slot_id'], ['appointment_slots.id'], ),
        sa.UniqueConstraint('slot_id'),
    )
    op.create_index('ix_appointments_patient_id', 'appointments', ['patient_id'])
    op.create_index('ix_appointments_doctor_id', 'appointments', ['doctor_id'])
    op.create_index('ix_appointments_slot_id', 'appointments', ['slot_id'])


def downgrade() -> None:
    op.drop_index('ix_appointments_slot_id', table_name='appointments')
    op.drop_index('ix_appointments_doctor_id', table_name='appointments')
    op.drop_index('ix_appointments_patient_id', table_name='appointments')
    op.drop_table('appointments')
    op.drop_index('ix_slots_slot_datetime', table_name='appointment_slots')
    op.drop_index('ix_slots_clinic_id', table_name='appointment_slots')
    op.drop_index('ix_slots_doctor_id', table_name='appointment_slots')
    op.drop_table('appointment_slots')
    op.drop_index('ix_doctors_clinic_id', table_name='doctors')
    op.drop_index('ix_doctors_user_id', table_name='doctors')
    op.drop_table('doctors')
    op.drop_index('ix_clinics_name', table_name='clinics')
    op.drop_table('clinics')
    op.drop_index('ix_patients_user_id', table_name='patients')
    op.drop_table('patients')
    op.execute("DROP TYPE appointment_status")
    op.execute("DROP TYPE user_roles")
