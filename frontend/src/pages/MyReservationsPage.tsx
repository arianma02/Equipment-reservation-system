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
        <p>Loading reservations...</p>
      </main>
    );
  }

  if (error) {
    return (
      <main>
        <p>{error}</p>
      </main>
    );
  }

  return (
    <main>
      <h2>My Reservations</h2>

      {reservations.length === 0 ? (
        <p>No reservations found.</p>
      ) : (
        <div className="reservation-list">
          {reservations.map((reservation) => (
            <article className="reservation-card" key={reservation.id}>
              <h3>{reservation.equipment_name}</h3>

              <p>Start: {reservation.start_date}</p>
              <p>End: {reservation.end_date}</p>
              <p>
                Status:{" "}
                <span className={`status-badge status-${reservation.status}`}>
                  {reservation.status}
                </span>
              </p>

              {reservation.status === "active" && (
                <button
                  className="danger-button"
                  onClick={() => cancelReservation(reservation.id)}
                  disabled={cancellingId === reservation.id}
                >
                  {cancellingId === reservation.id ? "Cancelling..." : "Cancel"}
                </button>
              )}
            </article>
          ))}
        </div>
      )}

      {cancelError && <p>{cancelError}</p>}
    </main>
  );
}

export default MyReservationsPage;
