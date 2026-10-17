"""Datos de ejemplo para probar el sistema. Solo se cargan si no hay pacientes."""
import logging
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Campania, Consulta, Paciente, PedidoAnteojos, Turno
from .services.agenda import proximos_dias_disponibles, slots_del_dia
from .tiempo import ahora, hoy

log = logging.getLogger("seed")


def cargar_demo(db: Session) -> None:
    if db.scalar(select(func.count(Paciente.id))):
        return
    log.info("Cargando datos de ejemplo...")

    ana = Paciente(nombre="Ana", apellido="Martínez", dni="30111222", telefono="5491122334455",
                   obra_social="OSDE", nro_afiliado="61234567801", email="ana@example.com")
    jorge = Paciente(nombre="Jorge", apellido="López", dni="25444555", telefono="5491166778899",
                     obra_social="Particular")
    lucia = Paciente(nombre="Lucía", apellido="Fernández", dni="45888999", telefono="5491155443322",
                     obra_social="Swiss Medical", notas="Paciente pediátrica, viene con su mamá.")
    db.add_all([ana, jorge, lucia])
    db.flush()

    consulta_ana = Consulta(paciente=ana, fecha=ahora() - timedelta(days=10), motivo="Control anual",
                            av_od="8/10", av_oi="9/10", pio_od=Decimal("15"), pio_oi=Decimal("16"),
                            rx_od="-1.25 -0.50 x 180", rx_oi="-1.00", diagnostico="Miopía leve con astigmatismo OD",
                            indicaciones="Anteojos para lejos. Control en 12 meses.")
    consulta_jorge = Consulta(paciente=jorge, fecha=ahora() - timedelta(days=5), motivo="Dificultad para leer",
                              av_od="10/10", av_oi="10/10", pio_od=Decimal("19"), pio_oi=Decimal("21"),
                              rx_od="+0.50", rx_oi="+0.75", adicion="+2.00",
                              diagnostico="Presbicia. PIO límite, sospecha de glaucoma.",
                              indicaciones="Multifocales. Campo visual y OCT de nervio óptico.")
    db.add_all([consulta_ana, consulta_jorge])
    db.flush()

    db.add_all([
        PedidoAnteojos(paciente=ana, consulta_id=consulta_ana.id, tipo="Lejos",
                       descripcion="Armazón acetato negro, cristales orgánicos antirreflex",
                       estado="en_laboratorio", fecha_pedido=hoy() - timedelta(days=8),
                       fecha_estimada=hoy() + timedelta(days=3),
                       monto_total=Decimal("180000"), sena=Decimal("90000")),
        PedidoAnteojos(paciente=jorge, consulta_id=consulta_jorge.id, tipo="Multifocal",
                       descripcion="Multifocales con filtro azul", estado="listo",
                       fecha_pedido=hoy() - timedelta(days=4), monto_total=Decimal("420000"),
                       sena=Decimal("420000")),
    ])

    db.add_all([
        Campania(titulo="Octubre: mes del glaucoma",
                 descripcion="Medición de presión ocular sin cargo para mayores de 40 años.",
                 fecha_inicio=hoy(), fecha_fin=hoy() + timedelta(days=40)),
        Campania(titulo="Control visual para la vuelta a clases",
                 descripcion="Descuento del 20% en consultas pediátricas.",
                 fecha_inicio=hoy() - timedelta(days=90), fecha_fin=hoy() - timedelta(days=30), activa=False),
    ])

    dias = proximos_dias_disponibles(db, 1)
    if dias:
        slots = slots_del_dia(dias[0])
        db.add_all([
            Turno(paciente=lucia, fecha_hora=slots[0], motivo="Control pediátrico", estado="confirmado"),
            Turno(paciente=jorge, fecha_hora=slots[1], motivo="Campo visual", estado="pendiente"),
        ])
    db.commit()
