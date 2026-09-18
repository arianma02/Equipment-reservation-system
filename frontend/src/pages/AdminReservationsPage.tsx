import { useEffect, useState } from "react";
import { API_URL } from "../config";
import type { AdminReservation } from "../types";

function AdminReservationsPage() {
  const [reservations, setReservations] = useState<AdminReservation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [cancelError, setCancelError] = useState("");
  const [cancellingId, setCancellingId] = useState<number | null>(null);

  useEffect(() => {
    async function loadReservations() {
      const token = localStorage.getItem("access_token");

      if (!token) {
        setError("You must be logged in");
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(`${API_URL}/reservations`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error("Failed to load reservations");
        }

        const data = await response.json();
        setReservations(data);
      } catch {
        setError("Failed to load reservations");
      } finally {
        setLoading(false);
      }
    }

    loadReservations();
  }, []);

  async function cancelReservation(reservationId: number) {
    const token = localStorage.getItem("access_token");

    if (!token) {
      setCancelError("You must be logged in");
      return;
    }

    setCancelError("");
    setCancellingId(reservationId);

    try {
      const response = await fetch(
        `${API_URL}/reservations/${reservationId}/cancel`,
        {
          method: "PATCH",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to cancel reservation");
      }

      setReservations((previousReservations) =>
        previousReservations.map((reservation) =>
          reservation.id === reservationId
            ? { ...reservation, ...data }
            : reservation,
        ),
      );
    } catch (error) {
      if (error instanceof Error) {
        setCancelError(error.message);
      } else {
        setCancelError("Failed to cancel reservation");
      }
    } finally {
      setCancellingId(null);
    }
  }

  if (loading) {
    return (
      <main>
        <div className="page-state">Loading reservations...</div>
      </main>
    );
  }

  if (error) {
    return (
      <main>
        <div className="page-state error-state">{error}</div>
      </main>
    );
  }

  return (
    <main>
      <section className="page-heading">
        <p className="eyebrow">ADMINISTRATION</p>
        <h2>Manage reservations</h2>
        <p className="page-description">
          Review equipment reservations and cancel active bookings when needed.
        </p>
      </section>

      {reservations.length === 0 ? (
        <div className="empty-message">No reservations found.</div>
      ) : (
        <div className="admin-item-list">
          {reservations.map((reservation) => (
            <article className="admin-item-card" key={reservation.id}>
              <div className="admin-item-heading">
                <div>
                  <p className="admin-card-label">RESERVATION</p>
                  <h3>{reservation.equipment_name}</h3>
                </div>

                <span className={`status-badge status-${reservation.status}`}>
                  {reservation.status}
                </span>
              </div>

              <div className="admin-reservation-user">
                <span>User</span>
                <strong>{reservation.user_email}</strong>
              </div>

              <div className="admin-reservation-dates">
                <div>
                  <span>Start date</span>
                  <strong>{reservation.start_date}</strong>
                </div>

                <div>
                  <span>End date</span>
                  <strong>{reservation.end_date}</strong>
                </div>
              </div>

              {reservation.status === "active" && (
                <div className="admin-reservation-actions">
                  <button
                    className="danger-button"
                    onClick={() => cancelReservation(reservation.id)}
                    disabled={cancellingId === reservation.id}
                  >
                    {cancellingId === reservation.id
                      ? "Cancelling..."
                      : "Cancel reservation"}
                  </button>
                </div>
              )}
            </article>
          ))}
        </div>
      )}

      {cancelError && <p className="error-message">{cancelError}</p>}
    </main>
  );
}

export default AdminReservationsPage;
