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
    return <p>Loading reservations...</p>;
  }

  if (error) {
    return <p>{error}</p>;
  }

  return (
    <main>
      <h2>Manage Reservations</h2>
      {reservations.map((reservation) => (
        <article key={reservation.id}>
          <p>User: {reservation.user_email}</p>
          <p>Equipment: {reservation.equipment_name}</p>
          <p>Start date: {reservation.start_date}</p>
          <p>End date: {reservation.end_date}</p>
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
      ))}{" "}
      {cancelError && <p>{cancelError}</p>}
    </main>
  );
}

export default AdminReservationsPage;
