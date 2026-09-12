import { useEffect, useState } from "react";
import { API_URL } from "../config";

type Reservation = {
  id: number;
  user_id: number;
  equipment_id: number;
  equipment_name: string;
  start_date: string;
  end_date: string;
  status: string;
};

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
    return <p>Loading reservations...</p>;
  }

  if (error) {
    return <p>{error}</p>;
  }

  return (
    <main>
      <h2>My Reservations</h2>

      {reservations.length === 0 && <p>No reservations found.</p>}

      {reservations.map((reservation) => (
        <article key={reservation.id}>
          <p>Equipment: {reservation.equipment_name}</p>
          <p>Start: {reservation.start_date}</p>
          <p>End: {reservation.end_date}</p>
          <p>Status: {reservation.status}</p>

          {reservation.status === "active" && (
            <button
              onClick={() => cancelReservation(reservation.id)}
              disabled={cancellingId === reservation.id}
            >
              {cancellingId === reservation.id ? "Cancelling..." : "Cancel"}
            </button>
          )}
        </article>
      ))}

      {cancelError && <p>{cancelError}</p>}
    </main>
  );
}

export default MyReservationsPage;
