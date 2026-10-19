import threading

from sqlalchemy import text

from database import SessionLocal, engine
from services.notificationService import purge_old_notifications
from services.ticketFeedbackService import auto_close_expired

# Tareas periódicas dentro del backend (sin cron ni dependencias extra).
# Un candado de Postgres evita que dos procesos las corran al mismo tiempo.
INTERVAL_SECONDS = 5 * 60
FIRST_RUN_DELAY = 30
LOCK_ID = 7_310_656

_stop = threading.Event()


def run_jobs_once():
    # El candado vive en su propia conexión: la sesión de trabajo hace commits
    # y devuelve su conexión al pool, lo que soltaría (o dejaría colgado) el candado.
    with engine.connect() as lock_conn:
        if not lock_conn.execute(text("SELECT pg_try_advisory_lock(:id)"), {"id": LOCK_ID}).scalar():
            return
        db = SessionLocal()
        try:
            closed, surveys = auto_close_expired(db)
            if closed or surveys:
                print(f"[JOBS] Cierre automático: {closed} ticket(s) cerrados, {surveys} encuesta(s) llenadas")
            purge_old_notifications(db)
        except Exception as e:
            db.rollback()
            print(f"[JOBS] Error en tareas programadas: {e}")
        finally:
            db.close()
            lock_conn.execute(text("SELECT pg_advisory_unlock(:id)"), {"id": LOCK_ID})
            lock_conn.commit()


def _loop():
    if _stop.wait(FIRST_RUN_DELAY):
        return
    while True:
        try:
            run_jobs_once()
        except Exception as e:
            print(f"[JOBS] No se pudieron correr las tareas programadas: {e}")
        if _stop.wait(INTERVAL_SECONDS):
            return


def start_scheduler():
    threading.Thread(target=_loop, name="scheduled-jobs", daemon=True).start()


def stop_scheduler():
    _stop.set()
