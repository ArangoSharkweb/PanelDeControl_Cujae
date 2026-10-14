"""init: esquema completo (config, indicadores, importacion, auditoria)

Revision ID: c3d4e5f6a7b8
Revises:
Create Date: 2026-10-14

Equivalente a `alembic revision --autogenerate` sobre los modelos de
app/models. Compatible con PostgreSQL 15 y 16.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "c3d4e5f6a7b8"
down_revision = None
branch_labels = None
depends_on = None

UUID_ = lambda: UUID(as_uuid=True)  # noqa: E731
NOW = sa.text("now()")
TRUE = sa.text("true")
FALSE = sa.text("false")


def pk(nombre_tabla: str) -> sa.Column:
    return sa.Column(
        "id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
    )


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    ]


def upgrade() -> None:
    for esquema in ("config", "indicadores", "importacion", "auditoria"):
        op.execute(f"CREATE SCHEMA IF NOT EXISTS {esquema}")

    # ==========================================================
    # ESQUEMA config
    # ==========================================================
    op.create_table(
        "usuarios",
        pk("usuarios"),
        sa.Column("username", sa.String(120), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255)),
        sa.Column("email", sa.String(200)),
        sa.Column("rol", sa.String(20), nullable=False),
        sa.Column("auth_type", sa.String(10), nullable=False),
        sa.Column("alcance_tipo", sa.String(20)),
        sa.Column("alcance_id", UUID_()),
        sa.Column("activo", sa.Boolean(), server_default=TRUE, nullable=False),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column(
            "ultima_modificacion", sa.DateTime(timezone=True), server_default=NOW, nullable=False
        ),
        sa.CheckConstraint(
            "rol IN ('administrador','alta_direccion','directivo','jefe_proceso','auditor')",
            name="ck_usuarios_rol",
        ),
        sa.CheckConstraint("auth_type IN ('ldap','local')", name="ck_usuarios_auth"),
        sa.CheckConstraint(
            "alcance_tipo IN ('institucional','unidad','proceso')", name="ck_usuarios_alcance"
        ),
        schema="config",
    )

    op.create_table(
        "procesos",
        pk("procesos"),
        sa.Column("codigo", sa.String(20), nullable=False, unique=True),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("descripcion", sa.Text()),
        sa.Column(
            "responsable_id",
            UUID_(),
            sa.ForeignKey(
                "config.usuarios.id",
                name="fk_procesos_responsable_id_usuarios",
                ondelete="SET NULL",
            ),
        ),
        sa.Column("activo", sa.Boolean(), server_default=TRUE, nullable=False),
        *timestamps(),
        sa.CheckConstraint(
            "tipo IN ('rectorado','direccion','vicerrectorado','facultad','proceso')",
            name="ck_procesos_tipo",
        ),
        schema="config",
    )

    op.create_table(
        "objetivos_estrategicos",
        pk("objetivos_estrategicos"),
        sa.Column("codigo", sa.String(20), nullable=False, unique=True),
        sa.Column("nombre", sa.String(300), nullable=False),
        sa.Column("descripcion", sa.Text()),
        sa.Column(
            "proceso_id",
            UUID_(),
            sa.ForeignKey(
                "config.procesos.id",
                name="fk_objetivos_estrategicos_proceso_id_procesos",
                ondelete="CASCADE",
            ),
        ),
        sa.Column("activo", sa.Boolean(), server_default=TRUE, nullable=False),
        schema="config",
    )
    op.create_index(
        "idx_objetivos_proceso", "objetivos_estrategicos", ["proceso_id"]
    ,
        schema="config",)

    op.create_table(
        "metricas_proceso",
        pk("metricas_proceso"),
        sa.Column("codigo", sa.String(20), nullable=False, unique=True),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column(
            "proceso_id",
            UUID_(),
            sa.ForeignKey(
                "config.procesos.id",
                name="fk_metricas_proceso_proceso_id_procesos",
                ondelete="CASCADE",
            ),
        ),
        schema="config",
    )

    op.create_table(
        "unidades_organizativas",
        pk("unidades_organizativas"),
        sa.Column("codigo", sa.String(50), nullable=False, unique=True),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("tipo", sa.String(50)),
        sa.Column(
            "responsable_id",
            UUID_(),
            sa.ForeignKey(
                "config.usuarios.id",
                name="fk_unidades_organizativas_responsable_id_usuarios",
                ondelete="SET NULL",
            ),
        ),
        sa.Column("lat", sa.Numeric(10, 8), nullable=True),
        sa.Column("lng", sa.Numeric(11, 8), nullable=True),
        sa.Column("activo", sa.Boolean(), server_default=TRUE, nullable=False),
        schema="config",
    )

    op.create_table(
        "cursos",
        pk("cursos"),
        sa.Column("nombre", sa.String(50), nullable=False, unique=True),
        sa.Column("anio_inicio", sa.Integer()),
        sa.Column("anio_fin", sa.Integer()),
        sa.Column("activo", sa.Boolean(), server_default=TRUE, nullable=False),
        sa.Column("es_curso_actual", sa.Boolean(), server_default=FALSE, nullable=False),
        schema="config",
    )
    op.create_index(
        "uq_curso_actual",
        "cursos",
        ["es_curso_actual"],
        unique=True,
        postgresql_where=sa.text("es_curso_actual"),
        schema="config",)

    op.create_table(
        "configuracion_sistema",
        pk("configuracion_sistema"),
        sa.Column("clave", sa.String(100), nullable=False, unique=True),
        sa.Column("valor", sa.Text(), nullable=False),
        sa.Column("descripcion", sa.Text()),
        sa.Column(
            "ultima_modificacion_por",
            UUID_(),
            sa.ForeignKey(
                "config.usuarios.id",
                name="fk_configuracion_sistema_ultima_modificacion_por_usuarios",
                ondelete="SET NULL",
            ),
        ),
        sa.Column(
            "ultima_modificacion_en",
            sa.DateTime(timezone=True),
            server_default=NOW,
            nullable=False,
        ),
        schema="config",
    )

    # ==========================================================
    # ESQUEMA indicadores
    # ==========================================================
    op.create_table(
        "fuentes_datos",
        pk("fuentes_datos"),
        sa.Column("codigo", sa.String(50), nullable=False, unique=True),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("motor", sa.String(50)),
        sa.Column("host", sa.String(255)),
        sa.Column("puerto", sa.Integer()),
        sa.Column("database", sa.String(100)),
        sa.Column("credenciales_cifradas", sa.Text()),
        sa.Column("activo", sa.Boolean(), server_default=TRUE, nullable=False),
        sa.Column("solo_lectura", sa.Boolean(), server_default=TRUE, nullable=False),
        sa.Column("ultima_prueba", sa.DateTime(timezone=True)),
        sa.Column("estado_prueba", sa.String(20)),
        sa.CheckConstraint(
            "tipo IN ('postgresql','sqlserver','excel')", name="ck_fuentes_tipo"
        ),
        schema="indicadores",
    )

    op.create_table(
        "indicadores",
        pk("indicadores"),
        sa.Column("codigo", sa.String(50), nullable=False, unique=True),
        sa.Column("nombre", sa.String(300), nullable=False),
        sa.Column("descripcion", sa.Text()),
        sa.Column("unidad_medida", sa.String(50)),
        sa.Column("periodicidad", sa.String(20), nullable=False),
        sa.Column("sentido", sa.String(20), nullable=False),
        sa.Column("formula", sa.String(500)),
        sa.Column(
            "proceso_id",
            UUID_(),
            sa.ForeignKey(
                "config.procesos.id",
                name="fk_indicadores_proceso_id_procesos",
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),
        sa.Column(
            "metrica_id",
            UUID_(),
            sa.ForeignKey(
                "config.metricas_proceso.id",
                name="fk_indicadores_metrica_id_metricas_proceso",
                ondelete="SET NULL",
            ),
        ),
        sa.Column("nivel", sa.String(20), nullable=False),
        sa.Column("esencial", sa.Boolean(), server_default=FALSE, nullable=False),
        sa.Column("activo", sa.Boolean(), server_default=TRUE, nullable=False),
        *timestamps(),
        sa.CheckConstraint(
            "periodicidad IN ('anual','semestral','trimestral','mensual')",
            name="ck_indicadores_periodicidad",
        ),
        sa.CheckConstraint(
            "sentido IN ('ascendente','descendente')", name="ck_indicadores_sentido"
        ),
        sa.CheckConstraint(
            "nivel IN ('Universidad','Facultad','Direccion')", name="ck_indicadores_nivel"
        ),
        schema="indicadores",
    )
    op.create_index(
        "idx_indicadores_proceso", "indicadores", ["proceso_id"]
    ,
        schema="indicadores",)
    op.create_index("idx_indicadores_activo", "indicadores", ["activo"],
    schema="indicadores",)

    op.create_table(
        "variables_indicador",
        pk("variables_indicador"),
        sa.Column(
            "indicador_id",
            UUID_(),
            sa.ForeignKey(
                "indicadores.indicadores.id",
                name="fk_variables_indicador_indicador_id_indicadores",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column("nombre", sa.String(10), nullable=False),
        sa.Column(
            "fuente_id",
            UUID_(),
            sa.ForeignKey(
                "indicadores.fuentes_datos.id",
                name="fk_variables_indicador_fuente_id_fuentes_datos",
                ondelete="RESTRICT",
            ),
        ),
        sa.Column("tabla", sa.String(100)),
        sa.Column("columna", sa.String(100)),
        sa.Column("funcion_agregacion", sa.String(20)),
        sa.Column("filtros", JSONB(), server_default=sa.text("'{}'")),
        sa.UniqueConstraint("indicador_id", "nombre", name="uq_variables_indicador_nombre"),
        sa.CheckConstraint(
            "funcion_agregacion IN ('COUNT','SUM','AVG','MIN','MAX')",
            name="ck_variables_funcion",
        ),
        schema="indicadores",
    )

    op.create_table(
        "metas_indicador",
        pk("metas_indicador"),
        sa.Column(
            "indicador_id",
            UUID_(),
            sa.ForeignKey(
                "indicadores.indicadores.id",
                name="fk_metas_indicador_indicador_id_indicadores",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "curso_id",
            UUID_(),
            sa.ForeignKey(
                "config.cursos.id",
                name="fk_metas_indicador_curso_id_cursos",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column("valor_meta", sa.Numeric(15, 4), nullable=False),
        sa.Column("umbral_verde", sa.Numeric(5, 2), server_default=sa.text("90")),
        sa.Column("umbral_amarillo", sa.Numeric(5, 2), server_default=sa.text("70")),
        sa.UniqueConstraint("indicador_id", "curso_id", name="uq_metas_indicador_curso"),
        schema="indicadores",
    )

    op.create_table(
        "historial_snapshot",
        pk("historial_snapshot"),
        sa.Column(
            "indicador_id",
            UUID_(),
            sa.ForeignKey(
                "indicadores.indicadores.id",
                name="fk_historial_snapshot_indicador_id_indicadores",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column("periodo", sa.String(30), nullable=False),
        sa.Column("valor", sa.Numeric(15, 4)),
        sa.Column("estado_semaforo", sa.String(10)),
        sa.UniqueConstraint("indicador_id", "periodo", name="uq_snapshot_periodo"),
        sa.CheckConstraint(
            "estado_semaforo IN ('verde','amarillo','rojo')", name="ck_snapshot_semaforo"
        ),
        schema="indicadores",
    )

    op.create_table(
        "valores_indicadores",
        pk("valores_indicadores"),
        sa.Column(
            "indicador_id",
            UUID_(),
            sa.ForeignKey(
                "indicadores.indicadores.id",
                name="fk_valores_indicadores_indicador_id_indicadores",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "curso_id",
            UUID_(),
            sa.ForeignKey(
                "config.cursos.id",
                name="fk_valores_indicadores_curso_id_cursos",
                ondelete="RESTRICT",
            ),
        ),
        sa.Column(
            "unidad_id",
            UUID_(),
            sa.ForeignKey(
                "config.unidades_organizativas.id",
                name="fk_valores_indicadores_unidad_id_unidades_organizativas",
                ondelete="CASCADE",
            ),
        ),
        sa.Column("valor", sa.Numeric(15, 4)),
        sa.Column("estado_semaforo", sa.String(10)),
        sa.Column("porcentaje_meta", sa.Numeric(5, 2)),
        sa.Column("calculado_en", sa.DateTime(timezone=True)),
        sa.Column("vigente_hasta", sa.DateTime(timezone=True)),
        sa.Column("fuente_origen", sa.String(50)),
        sa.UniqueConstraint(
            "indicador_id",
            "curso_id",
            "unidad_id",
            "vigente_hasta",
            name="uq_valores_vigencia",
        ),
        sa.CheckConstraint(
            "estado_semaforo IN ('verde','amarillo','rojo')", name="ck_valores_semaforo"
        ),
        schema="indicadores",
    )
    op.create_index(
        "idx_valores_indicador",
        "valores_indicadores",
        ["indicador_id", "calculado_en"],
        schema="indicadores",)
    op.create_index(
        "idx_valores_vigencia", "valores_indicadores", ["vigente_hasta"]
    ,
        schema="indicadores",)

    op.create_table(
        "narrativas_ia",
        pk("narrativas_ia"),
        sa.Column(
            "valor_indicador_id",
            UUID_(),
            sa.ForeignKey(
                "indicadores.valores_indicadores.id",
                name="fk_narrativas_ia_valor_indicador_id_valores_indicadores",
                ondelete="CASCADE",
            ),
            nullable=False,
            unique=True,
        ),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("proveedor", sa.String(30)),
        sa.Column("modelo", sa.String(100)),
        sa.Column("tokens_entrada", sa.Integer()),
        sa.Column("tokens_salida", sa.Integer()),
        sa.Column("es_fallback", sa.Boolean(), server_default=FALSE, nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        schema="indicadores",
    )

    # ==========================================================
    # ESQUEMA importacion
    # ==========================================================
    op.create_table(
        "registros_importados",
        pk("registros_importados"),
        sa.Column(
            "fuente_id",
            UUID_(),
            sa.ForeignKey(
                "indicadores.fuentes_datos.id",
                name="fk_registros_importados_fuente_id_fuentes_datos",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column("tabla_origen", sa.String(100)),
        sa.Column("fila_original", sa.Integer()),
        sa.Column("datos", JSONB(), nullable=False),
        sa.Column("normalizado", sa.Boolean(), server_default=FALSE, nullable=False),
        sa.Column("conciliado", sa.Boolean(), server_default=FALSE, nullable=False),
        sa.Column("editado_manualmente", sa.Boolean(), server_default=FALSE, nullable=False),
        sa.Column("importado_en", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column(
            "usuario_id",
            UUID_(),
            sa.ForeignKey(
                "config.usuarios.id",
                name="fk_registros_importados_usuario_id_usuarios",
                ondelete="SET NULL",
            ),
        ),
        sa.Column("error_validacion", sa.Text()),
        schema="importacion",
    )
    op.create_index(
        "idx_registros_fuente",
        "registros_importados",
        ["fuente_id", "importado_en"],
        schema="importacion",)
    op.create_index(
        "idx_registros_pendientes",
        "registros_importados",
        ["normalizado", "conciliado"],
        postgresql_where=sa.text("normalizado = false OR conciliado = false"),
        schema="importacion",)

    # ==========================================================
    # ESQUEMA auditoria
    # ==========================================================
    op.create_table(
        "auditoria",
        pk("auditoria"),
        sa.Column(
            "usuario_id",
            UUID_(),
            sa.ForeignKey(
                "config.usuarios.id", name="fk_auditoria_usuario_id_usuarios", ondelete="SET NULL"
            ),
        ),
        sa.Column("accion", sa.String(50), nullable=False),
        sa.Column("recurso_tipo", sa.String(50), nullable=False),
        sa.Column("recurso_id", UUID_()),
        sa.Column("detalles", JSONB()),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        schema="auditoria",
    )
    op.create_index("idx_auditoria_timestamp", "auditoria", ["timestamp"],
    schema="auditoria",)
    op.create_index(
        "idx_auditoria_usuario", "auditoria", ["usuario_id", "timestamp"]
    ,
        schema="auditoria",)
    op.create_index("idx_auditoria_accion", "auditoria", ["accion"],
    schema="auditoria",)

    op.create_table(
        "security_logs",
        sa.Column(
            "log_id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("ts", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("severity", sa.String(10), nullable=False),
        sa.Column("usuario", JSONB(), nullable=False),
        sa.Column("session", JSONB(), nullable=False),
        sa.Column("action", JSONB(), nullable=False),
        sa.Column("system", JSONB(), nullable=False),
        sa.CheckConstraint(
            "severity IN ('INFO','WARNING','CRITICAL')", name="ck_seclogs_severidad"
        ),
        schema="auditoria",
    )
    op.create_index("idx_seclogs_ts", "security_logs", ["ts"],
    schema="auditoria",)
    op.create_index(
        "idx_seclogs_evento", "security_logs", ["event_type", "ts"]
    ,
        schema="auditoria",)

    op.create_table(
        "log_ai_analysis",
        pk("log_ai_analysis"),
        sa.Column("tipo_analisis", sa.String(30), nullable=False),
        sa.Column("proveedor", sa.String(30), nullable=False),
        sa.Column("modelo", sa.String(100)),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("respuesta", sa.Text()),
        sa.Column("rango_inicio", sa.DateTime(timezone=True)),
        sa.Column("rango_fin", sa.DateTime(timezone=True)),
        sa.Column("tokens_entrada", sa.Integer(), server_default=sa.text("0")),
        sa.Column("tokens_salida", sa.Integer(), server_default=sa.text("0")),
        sa.Column("costo_estimado", sa.Numeric(10, 6)),
        sa.Column("duracion_ms", sa.Integer()),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("error", sa.Text()),
        sa.Column(
            "usuario_id",
            UUID_(),
            sa.ForeignKey(
                "config.usuarios.id",
                name="fk_log_ai_analysis_usuario_id_usuarios",
                ondelete="SET NULL",
            ),
        ),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.CheckConstraint("tipo_analisis IN ('logs','narrativa')", name="ck_ai_tipo"),
        sa.CheckConstraint("estado IN ('ok','error','fallback')", name="ck_ai_estado"),
        schema="auditoria",
    )
    op.create_index(
        "idx_ai_analysis_tipo",
        "log_ai_analysis",
        ["tipo_analisis", "creado_en"],
        schema="auditoria",)

    op.create_table(
        "notificaciones",
        pk("notificaciones"),
        sa.Column(
            "usuario_id",
            UUID_(),
            sa.ForeignKey(
                "config.usuarios.id",
                name="fk_notificaciones_usuario_id_usuarios",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column("tipo", sa.String(30), nullable=False),
        sa.Column("mensaje", sa.Text(), nullable=False),
        sa.Column(
            "indicador_id",
            UUID_(),
            sa.ForeignKey(
                "indicadores.indicadores.id",
                name="fk_notificaciones_indicador_id_indicadores",
                ondelete="CASCADE",
            ),
        ),
        sa.Column("leida", sa.Boolean(), server_default=FALSE, nullable=False),
        sa.Column("creada_en", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        schema="auditoria",
    )
    op.create_index(
        "idx_notif_usuario", "notificaciones", ["usuario_id", "leida"]
    ,
        schema="auditoria",)

    _crear_triggers_append_only()


def _crear_triggers_append_only() -> None:
    """RF-51/52: auditoria y security_logs solo aceptan INSERT."""
    op.execute(
        """
        CREATE OR REPLACE FUNCTION auditoria.fn_bloquear_modificacion() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'Tabla append-only: % prohibido', TG_OP;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    for tabla in ("auditoria", "security_logs"):
        for accion in ("UPDATE", "DELETE"):
            op.execute(
                f"""
                CREATE TRIGGER trg_{tabla}_no_{accion.lower()}
                BEFORE {accion} ON auditoria.{tabla}
                FOR EACH ROW EXECUTE FUNCTION auditoria.fn_bloquear_modificacion()
                """
            )


def downgrade() -> None:
    for esquema in ("auditoria", "importacion", "indicadores", "config"):
        op.execute(f"DROP SCHEMA IF EXISTS {esquema} CASCADE")
