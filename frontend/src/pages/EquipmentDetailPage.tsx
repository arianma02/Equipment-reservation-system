import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import type { Equipment } from "../types";
import { API_URL } from "../config";

function EquipmentDetailPage() {
  const { id } = useParams();

  const [equipment, setEquipment] = useState<Equipment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const [availability, setAvailability] = useState<boolean | null>(null);
  const [availabilityLoading, setAvailabilityLoading] = useState(false);
  const [availabilityError, setAvailabilityError] = useState("");

  const { user } = useAuth();

  const [reservationLoading, setReservationLoading] = useState(false);
  const [reservationMessage, setReservationMessage] = useState("");

  const today = new Date().toISOString().split("T")[0];

  useEffect(() => {
    async function loadEquipment() {
      setLoading(true);
      setError("");
      setEquipment(null);

      try {
        const response = await fetch(`${API_URL}/equipment/${id}`);

        if (!response.ok) {
          throw new Error("Failed to load equipment");
        }

        const data = await response.json();
        setEquipment(data);
      } catch {
        setError("Failed to load equipment");
      } finally {
        setLoading(false);
      }
    }

    loadEquipment();
  }, [id]);

  async function checkAvailability() {
    setAvailabilityLoading(true);
    setAvailabilityError("");
    setAvailability(null);

    try {
      const params = new URLSearchParams();

      params.append("start_date", startDate);
      params.append("end_date", endDate);

      const response = await fetch(
        `${API_URL}/equipment/${id}/availability?${params.toString()}`,
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to check availability");
      }

      setAvailability(data.available);
    } catch (error) {
      if (error instanceof Error) {
        setAvailabilityError(error.message);
      } else {
        setAvailabilityError("Failed to check availability");
      }
    } finally {
      setAvailabilityLoading(false);
    }
  }

  async function createReservation() {
    const token = localStorage.getItem("access_token");

    if (!token || !equipment) {
      return;
    }

    setReservationLoading(true);
    setReservationMessage("");

    try {
      const response = await fetch(
        `${API_URL}/equipment/${equipment.id}/reservations`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            start_date: startDate,
            end_date: endDate,
          }),
        },
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to create reservation");
      }

      setReservationMessage("Reservation created");
      setAvailability(null);
    } catch (error) {
      if (error instanceof Error) {
        setReservationMessage(error.message);
      } else {
        setReservationMessage("Failed to create reservation");
      }
    } finally {
      setReservationLoading(false);
    }
  }
  function handleStartDateChange(event: React.ChangeEvent<HTMLInputElement>) {
    setStartDate(event.target.value);
    setAvailability(null);
    setAvailabilityError("");
    setReservationMessage("");
  }

  function handleEndDateChange(event: React.ChangeEvent<HTMLInputElement>) {
    setEndDate(event.target.value);
    setAvailability(null);
    setAvailabilityError("");
    setReservationMessage("");
  }

  if (loading) {
    return <p>Loading equipment...</p>;
  }

  if (error || !equipment) {
    return <p>Failed to load equipment</p>;
  }

  return (
    <main>
      <h2>{equipment.name}</h2>

      <section className="equipment-detail-card">
        <div className="equipment-detail-info">
          <p>Asset tag: {equipment.asset_tag}</p>
          <p>Category: {equipment.category_name}</p>
          <p>Status: {equipment.status}</p>
        </div>

        <h3>Check availability</h3>

        <div className="date-fields">
          <label>
            Start date
            <input
              type="date"
              value={startDate}
              min={today}
              onChange={handleStartDateChange}
            />
          </label>

          <label>
            End date
            <input
              type="date"
              value={endDate}
              min={today}
              onChange={handleEndDateChange}
            />
          </label>
        </div>

        <button
          onClick={checkAvailability}
          disabled={!startDate || !endDate || availabilityLoading}
        >
          {availabilityLoading ? "Checking..." : "Check availability"}
        </button>

        {availability === true && <p className="success-message">Available</p>}

        {availability === false && (
          <p className="error-message">Not available</p>
        )}

        {availabilityError && (
          <p className="error-message">{availabilityError}</p>
        )}

        {user ? (
          <div className="reservation-action">
            <button
              onClick={createReservation}
              disabled={!startDate || !endDate || reservationLoading}
            >
              {reservationLoading ? "Reserving..." : "Reserve"}
            </button>

            {reservationMessage && <p>{reservationMessage}</p>}
          </div>
        ) : (
          <p>
            <Link to="/login">Login</Link> to reserve this equipment.
          </p>
        )}
      </section>
    </main>
  );
}

export default EquipmentDetailPage;
