"""
Electric Tariffs App - Repositorios SQL
=======================================
Implementación de acceso a datos para las 5 entidades.
Maneja I/O con SQLite. Core nunca ve SQL.
"""

import sqlite3
from datetime import datetime, date
from typing import Optional

from core.models import (
    Usuario,
    Medidor,
    Vinculacion,
    Tarifa,
    Lectura,
    RolUsuario,
    EstadoUsuario,
    TemaPreferido,
)
from core.errors import (
    UsuarioNoEncontradoError,
    UsuarioYaExisteError,
    MedidorNoEncontradoError,
    EtiquetaDuplicadaError,
    LecturaNoEncontradaError,
    PeriodoDuplicadoError,
    VinculacionYaExisteError,
    VinculacionNoEncontradaError,
)
from data.database import get_db


# =============================================================================
# REPOSITORIO DE USUARIOS
# =============================================================================

class UsuarioRepository:
    """Repositorio para operaciones CRUD de usuarios."""
    
    def __init__(self) -> None:
        self._db = get_db()
    
    def _row_to_usuario(self, row: sqlite3.Row) -> Usuario:
        """Convierte fila SQL a entidad Usuario."""
        return Usuario(
            id=row["id"],
            nombre=row["nombre"],
            username=row["username"],
            password_hash=row["password_hash"],
            rol=RolUsuario(row["rol"]),
            estado=EstadoUsuario(row["estado"]),
            debe_cambiar_pass=bool(row["debe_cambiar_pass"]),
            tema_preferido=TemaPreferido(row["tema_preferido"]),
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
        )
    
    def get_by_id(self, usuario_id: int) -> Usuario:
        """Obtiene usuario por ID."""
        with self._db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM usuarios WHERE id = ?",
                (usuario_id,)
            )
            row = cursor.fetchone()
            if row is None:
                raise UsuarioNoEncontradoError(usuario_id)
            return self._row_to_usuario(row)
    
    def get_by_username(self, username: str) -> Optional[Usuario]:
        """Obtiene usuario por nombre de usuario. Retorna None si no existe."""
        with self._db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM usuarios WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return self._row_to_usuario(row)
    
    def get_all(self, solo_activos: bool = False) -> list[Usuario]:
        """Obtiene todos los usuarios."""
        with self._db.get_connection() as conn:
            query = "SELECT * FROM usuarios"
            if solo_activos:
                query += " WHERE estado = 'ACTIVO'"
            query += " ORDER BY nombre"
            cursor = conn.execute(query)
            return [self._row_to_usuario(row) for row in cursor.fetchall()]
    
    def get_all_except_admin(self, solo_activos: bool = True) -> list[Usuario]:
        """Obtiene todos los usuarios excepto admin."""
        with self._db.get_connection() as conn:
            query = "SELECT * FROM usuarios WHERE rol != 'admin'"
            if solo_activos:
                query += " AND estado = 'ACTIVO'"
            query += " ORDER BY nombre"
            cursor = conn.execute(query)
            return [self._row_to_usuario(row) for row in cursor.fetchall()]
    
    def create(self, usuario: Usuario) -> Usuario:
        """Crea nuevo usuario. Retorna usuario con ID asignado."""
        with self._db.get_connection() as conn:
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO usuarios (nombre, username, password_hash, rol, estado, 
                                          debe_cambiar_pass, tema_preferido)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        usuario.nombre,
                        usuario.username,
                        usuario.password_hash,
                        usuario.rol.value,
                        usuario.estado.value,
                        int(usuario.debe_cambiar_pass),
                        usuario.tema_preferido.value,
                    )
                )
                conn.commit()
                usuario.id = cursor.lastrowid
                return usuario
            except sqlite3.IntegrityError:
                raise UsuarioYaExisteError(usuario.username)
    
    def update(self, usuario: Usuario) -> None:
        """Actualiza usuario existente."""
        with self._db.get_connection() as conn:
            conn.execute(
                """
                UPDATE usuarios 
                SET nombre = ?, password_hash = ?, rol = ?, estado = ?,
                    debe_cambiar_pass = ?, tema_preferido = ?
                WHERE id = ?
                """,
                (
                    usuario.nombre,
                    usuario.password_hash,
                    usuario.rol.value,
                    usuario.estado.value,
                    int(usuario.debe_cambiar_pass),
                    usuario.tema_preferido.value,
                    usuario.id,
                )
            )
            conn.commit()
    
    def update_password(self, usuario_id: int, password_hash: str) -> None:
        """Actualiza solo la contraseña y quita flag de cambio obligatorio."""
        with self._db.get_connection() as conn:
            conn.execute(
                """
                UPDATE usuarios 
                SET password_hash = ?, debe_cambiar_pass = 0
                WHERE id = ?
                """,
                (password_hash, usuario_id)
            )
            conn.commit()
    
    def update_tema(self, usuario_id: int, tema: TemaPreferido) -> None:
        """Actualiza preferencia de tema."""
        with self._db.get_connection() as conn:
            conn.execute(
                "UPDATE usuarios SET tema_preferido = ? WHERE id = ?",
                (tema.value, usuario_id)
            )
            conn.commit()
    
    def desactivar(self, usuario_id: int) -> None:
        """Desactiva usuario (RF-49 Opción B)."""
        with self._db.get_connection() as conn:
            conn.execute(
                "UPDATE usuarios SET estado = 'INACTIVO' WHERE id = ?",
                (usuario_id,)
            )
            conn.commit()


# =============================================================================
# REPOSITORIO DE MEDIDORES
# =============================================================================

class MedidorRepository:
    """Repositorio para operaciones CRUD de medidores."""
    
    def __init__(self) -> None:
        self._db = get_db()
    
    def _row_to_medidor(self, row: sqlite3.Row) -> Medidor:
        """Convierte fila SQL a entidad Medidor."""
        return Medidor(
            id=row["id"],
            propietario_id=row["propietario_id"],
            etiqueta=row["etiqueta"],
            numero_serie=row["numero_serie"],
            umbral_alerta=row["umbral_alerta"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
        )
    
    def get_by_id(self, medidor_id: int) -> Medidor:
        """Obtiene medidor por ID."""
        with self._db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM medidores WHERE id = ?",
                (medidor_id,)
            )
            row = cursor.fetchone()
            if row is None:
                raise MedidorNoEncontradoError(medidor_id)
            return self._row_to_medidor(row)
    
    def get_by_propietario(self, propietario_id: int) -> list[Medidor]:
        """Obtiene medidores de un propietario."""
        with self._db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM medidores WHERE propietario_id = ? ORDER BY etiqueta",
                (propietario_id,)
            )
            return [self._row_to_medidor(row) for row in cursor.fetchall()]
    
    def get_accesibles_por_usuario(self, usuario_id: int) -> list[Medidor]:
        """
        Obtiene medidores accesibles por un usuario.
        Incluye propios + vinculados.
        """
        with self._db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT m.* FROM medidores m
                WHERE m.propietario_id = ?
                UNION
                SELECT m.* FROM medidores m
                INNER JOIN vinculaciones v ON m.id = v.medidor_id
                WHERE v.usuario_id = ?
                ORDER BY etiqueta
                """,
                (usuario_id, usuario_id)
            )
            return [self._row_to_medidor(row) for row in cursor.fetchall()]
    
    def create(self, medidor: Medidor) -> Medidor:
        """Crea nuevo medidor. Retorna medidor con ID asignado."""
        with self._db.get_connection() as conn:
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO medidores (propietario_id, etiqueta, numero_serie, umbral_alerta)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        medidor.propietario_id,
                        medidor.etiqueta,
                        medidor.numero_serie,
                        medidor.umbral_alerta,
                    )
                )
                conn.commit()
                medidor.id = cursor.lastrowid
                return medidor
            except sqlite3.IntegrityError:
                raise EtiquetaDuplicadaError(medidor.etiqueta)
    
    def update(self, medidor: Medidor) -> None:
        """Actualiza medidor existente."""
        with self._db.get_connection() as conn:
            try:
                conn.execute(
                    """
                    UPDATE medidores 
                    SET etiqueta = ?, numero_serie = ?, umbral_alerta = ?
                    WHERE id = ?
                    """,
                    (
                        medidor.etiqueta,
                        medidor.numero_serie,
                        medidor.umbral_alerta,
                        medidor.id,
                    )
                )
                conn.commit()
            except sqlite3.IntegrityError:
                raise EtiquetaDuplicadaError(medidor.etiqueta)
    
    def delete(self, medidor_id: int) -> None:
        """Elimina medidor (CASCADE elimina lecturas asociadas)."""
        with self._db.get_connection() as conn:
            conn.execute("DELETE FROM medidores WHERE id = ?", (medidor_id,))
            conn.commit()
    
    def transferir_a_admin(self, usuario_id: int, admin_id: int) -> int:
        """
        Transfiere medidores de un usuario al admin (RF-49 Opción A).
        Retorna cantidad de medidores transferidos.
        """
        with self._db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM medidores WHERE propietario_id = ?",
                (usuario_id,)
            )
            cantidad = cursor.fetchone()[0]
            
            conn.execute(
                "UPDATE medidores SET propietario_id = ? WHERE propietario_id = ?",
                (admin_id, usuario_id)
            )
            conn.commit()
            return cantidad
    
    def contar_lecturas(self, medidor_id: int) -> int:
        """Cuenta lecturas de un medidor."""
        with self._db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM lecturas WHERE medidor_id = ?",
                (medidor_id,)
            )
            return cursor.fetchone()[0]


# =============================================================================
# REPOSITORIO DE VINCULACIONES
# =============================================================================

class VinculacionRepository:
    """Repositorio para operaciones CRUD de vinculaciones."""
    
    def __init__(self) -> None:
        self._db = get_db()
    
    def _row_to_vinculacion(self, row: sqlite3.Row) -> Vinculacion:
        """Convierte fila SQL a entidad Vinculacion."""
        return Vinculacion(
            id=row["id"],
            usuario_id=row["usuario_id"],
            medidor_id=row["medidor_id"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
        )
    
    def get_by_usuario(self, usuario_id: int) -> list[Vinculacion]:
        """Obtiene vinculaciones de un usuario."""
        with self._db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM vinculaciones WHERE usuario_id = ?",
                (usuario_id,)
            )
            return [self._row_to_vinculacion(row) for row in cursor.fetchall()]
    
    def get_by_medidor(self, medidor_id: int) -> list[Vinculacion]:
        """Obtiene vinculaciones de un medidor."""
        with self._db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM vinculaciones WHERE medidor_id = ?",
                (medidor_id,)
            )
            return [self._row_to_vinculacion(row) for row in cursor.fetchall()]
    
    def existe(self, usuario_id: int, medidor_id: int) -> bool:
        """Verifica si existe vinculación."""
        with self._db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM vinculaciones WHERE usuario_id = ? AND medidor_id = ?",
                (usuario_id, medidor_id)
            )
            return cursor.fetchone() is not None
    
    def create(self, vinculacion: Vinculacion) -> Vinculacion:
        """Crea nueva vinculación."""
        with self._db.get_connection() as conn:
            try:
                cursor = conn.execute(
                    "INSERT INTO vinculaciones (usuario_id, medidor_id) VALUES (?, ?)",
                    (vinculacion.usuario_id, vinculacion.medidor_id)
                )
                conn.commit()
                vinculacion.id = cursor.lastrowid
                return vinculacion
            except sqlite3.IntegrityError:
                raise VinculacionYaExisteError(vinculacion.usuario_id, vinculacion.medidor_id)
    
    def delete(self, usuario_id: int, medidor_id: int) -> None:
        """Elimina vinculación."""
        with self._db.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM vinculaciones WHERE usuario_id = ? AND medidor_id = ?",
                (usuario_id, medidor_id)
            )
            conn.commit()
            if cursor.rowcount == 0:
                raise VinculacionNoEncontradaError(usuario_id, medidor_id)
    
    def delete_by_usuario(self, usuario_id: int) -> None:
        """Elimina todas las vinculaciones de un usuario."""
        with self._db.get_connection() as conn:
            conn.execute(
                "DELETE FROM vinculaciones WHERE usuario_id = ?",
                (usuario_id,)
            )
            conn.commit()


# =============================================================================
# REPOSITORIO DE TARIFAS
# =============================================================================

class TarifaRepository:
    """Repositorio para operaciones CRUD de tarifas."""
    
    def __init__(self) -> None:
        self._db = get_db()
    
    def _row_to_tarifa(self, row: sqlite3.Row) -> Tarifa:
        """Convierte fila SQL a entidad Tarifa."""
        return Tarifa(
            id=row["id"],
            limite_min=row["limite_min"],
            limite_max=row["limite_max"],
            precio_kwh=row["precio_kwh"],
        )
    
    def get_all(self) -> list[Tarifa]:
        """Obtiene todas las tarifas ordenadas por límite mínimo."""
        with self._db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM tarifas ORDER BY limite_min"
            )
            return [self._row_to_tarifa(row) for row in cursor.fetchall()]
    
    def get_by_id(self, tarifa_id: int) -> Optional[Tarifa]:
        """Obtiene tarifa por ID."""
        with self._db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM tarifas WHERE id = ?",
                (tarifa_id,)
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return self._row_to_tarifa(row)
    
    def create(self, tarifa: Tarifa) -> Tarifa:
        """Crea nueva tarifa."""
        with self._db.get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO tarifas (limite_min, limite_max, precio_kwh) VALUES (?, ?, ?)",
                (tarifa.limite_min, tarifa.limite_max, tarifa.precio_kwh)
            )
            conn.commit()
            tarifa.id = cursor.lastrowid
            return tarifa
    
    def update(self, tarifa: Tarifa) -> None:
        """Actualiza tarifa existente."""
        with self._db.get_connection() as conn:
            conn.execute(
                "UPDATE tarifas SET limite_min = ?, limite_max = ?, precio_kwh = ? WHERE id = ?",
                (tarifa.limite_min, tarifa.limite_max, tarifa.precio_kwh, tarifa.id)
            )
            conn.commit()
    
    def delete(self, tarifa_id: int) -> None:
        """Elimina tarifa."""
        with self._db.get_connection() as conn:
            conn.execute("DELETE FROM tarifas WHERE id = ?", (tarifa_id,))
            conn.commit()
    
    def replace_all(self, tarifas: list[Tarifa]) -> None:
        """Reemplaza todas las tarifas (transacción atómica)."""
        with self._db.get_connection() as conn:
            conn.execute("DELETE FROM tarifas")
            for tarifa in tarifas:
                conn.execute(
                    "INSERT INTO tarifas (limite_min, limite_max, precio_kwh) VALUES (?, ?, ?)",
                    (tarifa.limite_min, tarifa.limite_max, tarifa.precio_kwh)
                )
            conn.commit()


# =============================================================================
# REPOSITORIO DE LECTURAS
# =============================================================================

class LecturaRepository:
    """Repositorio para operaciones CRUD de lecturas."""
    
    def __init__(self) -> None:
        self._db = get_db()
    
    def _row_to_lectura(self, row: sqlite3.Row) -> Lectura:
        """Convierte fila SQL a entidad Lectura."""
        return Lectura(
            id=row["id"],
            medidor_id=row["medidor_id"],
            autor_user_id=row["autor_user_id"],
            fecha_inicio=date.fromisoformat(row["fecha_inicio"]) if row["fecha_inicio"] else None,
            fecha_fin=date.fromisoformat(row["fecha_fin"]) if row["fecha_fin"] else None,
            lectura_anterior=row["lectura_anterior"],
            lectura_actual=row["lectura_actual"],
            consumo_kwh=row["consumo_kwh"],
            importe_total=row["importe_total"],
            es_rollover=bool(row["es_rollover"]),
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
        )
    
    def get_by_id(self, lectura_id: int) -> Lectura:
        """Obtiene lectura por ID."""
        with self._db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM lecturas WHERE id = ?",
                (lectura_id,)
            )
            row = cursor.fetchone()
            if row is None:
                raise LecturaNoEncontradaError(lectura_id)
            return self._row_to_lectura(row)
    
    def get_by_medidor(
        self,
        medidor_id: int,
        anio: Optional[int] = None
    ) -> list[Lectura]:
        """
        Obtiene lecturas de un medidor ordenadas por fecha.
        Opcionalmente filtra por año.
        """
        with self._db.get_connection() as conn:
            if anio:
                cursor = conn.execute(
                    """
                    SELECT * FROM lecturas 
                    WHERE medidor_id = ? AND strftime('%Y', fecha_fin) = ?
                    ORDER BY fecha_fin
                    """,
                    (medidor_id, str(anio))
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM lecturas WHERE medidor_id = ? ORDER BY fecha_fin",
                    (medidor_id,)
                )
            return [self._row_to_lectura(row) for row in cursor.fetchall()]
    
    def get_ultima_lectura(self, medidor_id: int) -> Optional[Lectura]:
        """Obtiene la última lectura de un medidor (para precarga)."""
        with self._db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM lecturas 
                WHERE medidor_id = ? 
                ORDER BY fecha_fin DESC 
                LIMIT 1
                """,
                (medidor_id,)
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return self._row_to_lectura(row)
    
    def get_lectura_anterior_cronologica(
        self,
        medidor_id: int,
        fecha_fin: date
    ) -> Optional[Lectura]:
        """Obtiene la lectura inmediatamente anterior a una fecha."""
        with self._db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM lecturas 
                WHERE medidor_id = ? AND fecha_fin < ?
                ORDER BY fecha_fin DESC
                LIMIT 1
                """,
                (medidor_id, fecha_fin.isoformat())
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return self._row_to_lectura(row)
    
    def get_lectura_posterior_cronologica(
        self,
        medidor_id: int,
        fecha_fin: date
    ) -> Optional[Lectura]:
        """Obtiene la lectura inmediatamente posterior a una fecha."""
        with self._db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM lecturas 
                WHERE medidor_id = ? AND fecha_fin > ?
                ORDER BY fecha_fin ASC
                LIMIT 1
                """,
                (medidor_id, fecha_fin.isoformat())
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return self._row_to_lectura(row)
    
    def get_lecturas_desde(
        self,
        medidor_id: int,
        fecha_desde: date
    ) -> list[Lectura]:
        """Obtiene lecturas desde una fecha (para recálculo en cascada)."""
        with self._db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM lecturas 
                WHERE medidor_id = ? AND fecha_fin >= ?
                ORDER BY fecha_fin
                """,
                (medidor_id, fecha_desde.isoformat())
            )
            return [self._row_to_lectura(row) for row in cursor.fetchall()]
    
    def get_ultimos_n_meses(self, medidor_id: int, n: int = 6) -> list[Lectura]:
        """Obtiene las últimas N lecturas (para gráfico)."""
        with self._db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM lecturas 
                WHERE medidor_id = ?
                ORDER BY fecha_fin DESC
                LIMIT ?
                """,
                (medidor_id, n)
            )
            lecturas = [self._row_to_lectura(row) for row in cursor.fetchall()]
            lecturas.reverse()  # Ordenar cronológicamente
            return lecturas
    
    def existe_periodo(
        self,
        medidor_id: int,
        fecha_inicio: date,
        fecha_fin: date,
        excluir_id: Optional[int] = None
    ) -> bool:
        """Verifica si ya existe lectura para ese período."""
        with self._db.get_connection() as conn:
            if excluir_id:
                cursor = conn.execute(
                    """
                    SELECT 1 FROM lecturas 
                    WHERE medidor_id = ? AND fecha_inicio = ? AND fecha_fin = ? AND id != ?
                    """,
                    (medidor_id, fecha_inicio.isoformat(), fecha_fin.isoformat(), excluir_id)
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT 1 FROM lecturas 
                    WHERE medidor_id = ? AND fecha_inicio = ? AND fecha_fin = ?
                    """,
                    (medidor_id, fecha_inicio.isoformat(), fecha_fin.isoformat())
                )
            return cursor.fetchone() is not None
    
    def create(self, lectura: Lectura) -> Lectura:
        """Crea nueva lectura."""
        with self._db.get_connection() as conn:
            try:
                now = datetime.now().isoformat()
                cursor = conn.execute(
                    """
                    INSERT INTO lecturas (
                        medidor_id, autor_user_id, fecha_inicio, fecha_fin,
                        lectura_anterior, lectura_actual, consumo_kwh, importe_total,
                        es_rollover, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        lectura.medidor_id,
                        lectura.autor_user_id,
                        lectura.fecha_inicio.isoformat() if lectura.fecha_inicio else None,
                        lectura.fecha_fin.isoformat() if lectura.fecha_fin else None,
                        lectura.lectura_anterior,
                        lectura.lectura_actual,
                        lectura.consumo_kwh,
                        lectura.importe_total,
                        int(lectura.es_rollover),
                        now,
                        now,
                    )
                )
                conn.commit()
                lectura.id = cursor.lastrowid
                return lectura
            except sqlite3.IntegrityError:
                raise PeriodoDuplicadoError(
                    str(lectura.fecha_inicio),
                    str(lectura.fecha_fin)
                )
    
    def update(self, lectura: Lectura) -> None:
        """Actualiza lectura existente."""
        with self._db.get_connection() as conn:
            conn.execute(
                """
                UPDATE lecturas 
                SET lectura_anterior = ?, lectura_actual = ?, consumo_kwh = ?,
                    importe_total = ?, es_rollover = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    lectura.lectura_anterior,
                    lectura.lectura_actual,
                    lectura.consumo_kwh,
                    lectura.importe_total,
                    int(lectura.es_rollover),
                    datetime.now().isoformat(),
                    lectura.id,
                )
            )
            conn.commit()
    
    def delete(self, lectura_id: int) -> None:
        """Elimina lectura."""
        with self._db.get_connection() as conn:
            conn.execute("DELETE FROM lecturas WHERE id = ?", (lectura_id,))
            conn.commit()
    
    def get_consumo_total_mes_actual(self, medidor_id: int) -> float:
        """Obtiene consumo total del mes actual."""
        with self._db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT COALESCE(SUM(consumo_kwh), 0) FROM lecturas 
                WHERE medidor_id = ? 
                AND strftime('%Y-%m', fecha_fin) = strftime('%Y-%m', 'now')
                """,
                (medidor_id,)
            )
            return cursor.fetchone()[0]
    
    def get_importe_total_mes_actual(self, medidor_id: int) -> float:
        """Obtiene importe total del mes actual."""
        with self._db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT COALESCE(SUM(importe_total), 0) FROM lecturas 
                WHERE medidor_id = ? 
                AND strftime('%Y-%m', fecha_fin) = strftime('%Y-%m', 'now')
                """,
                (medidor_id,)
            )
            return cursor.fetchone()[0]
    
    def get_anios_con_datos(self, medidor_id: int) -> list[int]:
        """Obtiene lista de años con lecturas registradas."""
        with self._db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT DISTINCT strftime('%Y', fecha_fin) as anio 
                FROM lecturas 
                WHERE medidor_id = ?
                ORDER BY anio DESC
                """,
                (medidor_id,)
            )
            return [int(row[0]) for row in cursor.fetchall()]
