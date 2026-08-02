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
    inspector = sa.inspect(conn)

    pk = inspector.get_pk_constraint("fact_sales")
    if not pk or not pk.get("constrained_columns"):
        with op.batch_alter_table("fact_sales", schema=None) as batch_op:
            batch_op.create_primary_key("pk_fact_sales", ["sales_key"])

    for tbl, col, pk_name in [
        ("dim_customer", "customer_key", "pk_dim_customer"),
        ("dim_product", "product_key", "pk_dim_product"),
        ("dim_date", "date_key", "pk_dim_date"),
        ("dim_region", "region_key", "pk_dim_region"),
        ("dim_employee", "employee_key", "pk_dim_employee"),
    ]:
        p = inspector.get_pk_constraint(tbl)
        if not p or not p.get("constrained_columns"):
            with op.batch_alter_table(tbl, schema=None) as batch_op:
                batch_op.create_primary_key(pk_name, [col])

    existing_fks = {fk["name"] for fk in inspector.get_foreign_keys("fact_sales")}
    existing_ref_tables = {fk.get("referred_table") for fk in inspector.get_foreign_keys("fact_sales")}
    with op.batch_alter_table("fact_sales", schema=None) as batch_op:
        fks_to_create = [
            ("fk_fact_sales_customer_key", "dim_customer", ["customer_key"], ["customer_key"]),
            ("fk_fact_sales_product_key", "dim_product", ["product_key"], ["product_key"]),
            ("fk_fact_sales_date_key", "dim_date", ["date_key"], ["date_key"]),
            ("fk_fact_sales_region_key", "dim_region", ["region_key"], ["region_key"]),
            ("fk_fact_sales_employee_key", "dim_employee", ["employee_key"], ["employee_key"]),
        ]
        for name, ref_tbl, local_cols, ref_cols in fks_to_create:
            if name not in existing_fks and ref_tbl not in existing_ref_tables:
                batch_op.create_foreign_key(
                    name, ref_tbl, local_cols, ref_cols, ondelete="SET NULL"
                )

    op.create_index(
        "fact_sales_date_id_idx",
        "fact_sales",
        ["date_key"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "fact_sales_customer_id_idx",
        "fact_sales",
        ["customer_key"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "fact_sales_product_id_idx",
        "fact_sales",
        ["product_key"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "fact_sales_region_id_idx",
        "fact_sales",
        ["region_key"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "fact_sales_date_id_region_id_idx",
        "fact_sales",
        ["date_key", "region_key"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "fact_sales_date_id_customer_id_idx",
        "fact_sales",
        ["date_key", "customer_key"],
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
