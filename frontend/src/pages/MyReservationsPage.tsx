import { useEffect, useState } from "react";
import { API_URL } from "../config";
import type { Reservation } from "../types";

function MyReservationsPage() {
  const [reservations, setReservations] = useState<Reservation[]>([]);
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
        const response = await fetch(`${API_URL}/reservations/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || "Failed to load reservations");
        }

        setReservations(data);
      } catch (error) {
        if (error instanceof Error) {
          setError(error.message);
        } else {
          setError("Failed to load reservations");
        }
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

      setReservations((currentReservations) =>
        currentReservations.map((reservation) =>
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
        <p className="eyebrow">RESERVATIONS</p>
        <h2>My reservations</h2>
        <p className="page-description">
          View your current and previous equipment reservations.
        </p>
      </section>

      {reservations.length === 0 ? (
        <div className="empty-message">No reservations found.</div>
      ) : (
        <div className="reservation-list">
          {reservations.map((reservation) => (
            <article className="reservation-card" key={reservation.id}>
              <div className="reservation-card-header">
                <div>
                  <p className="reservation-label">EQUIPMENT</p>
                  <h3>{reservation.equipment_name}</h3>
                </div>

                <span className={`status-badge status-${reservation.status}`}>
                  {reservation.status}
                </span>
              </div>

              <div className="reservation-dates">
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
                <div className="reservation-card-actions">
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

export default MyReservationsPage;
