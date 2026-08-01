"""add star schema constraints and indexes

Revision ID: 001
Revises: 
Create Date: 2026-07-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    dialect_name = conn.dialect.name

    with op.batch_alter_table("fact_sales", schema=None) as batch_op:
        batch_op.create_primary_key("pk_fact_sales", ["sale_id"])

    with op.batch_alter_table("dim_customer", schema=None) as batch_op:
        batch_op.create_primary_key("pk_dim_customer", ["customer_id"])

    with op.batch_alter_table("dim_product", schema=None) as batch_op:
        batch_op.create_primary_key("pk_dim_product", ["product_id"])

    with op.batch_alter_table("dim_date", schema=None) as batch_op:
        batch_op.create_primary_key("pk_dim_date", ["date_id"])

    with op.batch_alter_table("dim_region", schema=None) as batch_op:
        batch_op.create_primary_key("pk_dim_region", ["region_id"])

    with op.batch_alter_table("dim_employee", schema=None) as batch_op:
        batch_op.create_primary_key("pk_dim_employee", ["employee_id"])

    with op.batch_alter_table("fact_sales", schema=None) as batch_op:
        batch_op.create_foreign_key(
            "fk_fact_sales_customer_id",
            "dim_customer",
            ["customer_id"],
            ["customer_id"],
            ondelete="SET NULL",
        )
        batch_op.create_foreign_key(
            "fk_fact_sales_product_id",
            "dim_product",
            ["product_id"],
            ["product_id"],
            ondelete="SET NULL",
        )
        batch_op.create_foreign_key(
            "fk_fact_sales_date_id",
            "dim_date",
            ["date_id"],
            ["date_id"],
            ondelete="SET NULL",
        )
        batch_op.create_foreign_key(
            "fk_fact_sales_region_id",
            "dim_region",
            ["region_id"],
            ["region_id"],
            ondelete="SET NULL",
        )
        batch_op.create_foreign_key(
            "fk_fact_sales_employee_id",
            "dim_employee",
            ["employee_id"],
            ["employee_id"],
            ondelete="SET NULL",
        )

    op.create_index(
        "fact_sales_date_id_idx",
        "fact_sales",
        ["date_id"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "fact_sales_customer_id_idx",
        "fact_sales",
        ["customer_id"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "fact_sales_product_id_idx",
        "fact_sales",
        ["product_id"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "fact_sales_region_id_idx",
        "fact_sales",
        ["region_id"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "fact_sales_date_id_region_id_idx",
        "fact_sales",
        ["date_id", "region_id"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "fact_sales_date_id_customer_id_idx",
        "fact_sales",
        ["date_id", "customer_id"],
        unique=False,
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("fact_sales_date_id_customer_id_idx", table_name="fact_sales", if_exists=True)
    op.drop_index("fact_sales_date_id_region_id_idx", table_name="fact_sales", if_exists=True)
    op.drop_index("fact_sales_region_id_idx", table_name="fact_sales", if_exists=True)
    op.drop_index("fact_sales_product_id_idx", table_name="fact_sales", if_exists=True)
    op.drop_index("fact_sales_customer_id_idx", table_name="fact_sales", if_exists=True)
    op.drop_index("fact_sales_date_id_idx", table_name="fact_sales", if_exists=True)

    with op.batch_alter_table("fact_sales", schema=None) as batch_op:
        batch_op.drop_constraint("fk_fact_sales_employee_id", type_="foreignkey")
        batch_op.drop_constraint("fk_fact_sales_region_id", type_="foreignkey")
        batch_op.drop_constraint("fk_fact_sales_date_id", type_="foreignkey")
        batch_op.drop_constraint("fk_fact_sales_product_id", type_="foreignkey")
        batch_op.drop_constraint("fk_fact_sales_customer_id", type_="foreignkey")

    with op.batch_alter_table("dim_employee", schema=None) as batch_op:
        batch_op.drop_constraint("pk_dim_employee", type_="primary")

    with op.batch_alter_table("dim_region", schema=None) as batch_op:
        batch_op.drop_constraint("pk_dim_region", type_="primary")

    with op.batch_alter_table("dim_date", schema=None) as batch_op:
        batch_op.drop_constraint("pk_dim_date", type_="primary")

    with op.batch_alter_table("dim_product", schema=None) as batch_op:
        batch_op.drop_constraint("pk_dim_product", type_="primary")

    with op.batch_alter_table("dim_customer", schema=None) as batch_op:
        batch_op.drop_constraint("pk_dim_customer", type_="primary")

    with op.batch_alter_table("fact_sales", schema=None) as batch_op:
        batch_op.drop_constraint("pk_fact_sales", type_="primary")
