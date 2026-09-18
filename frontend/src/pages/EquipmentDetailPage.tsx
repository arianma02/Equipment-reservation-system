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
    return (
      <main>
        <div className="page-state">Loading equipment...</div>
      </main>
    );
  }

  if (error || !equipment) {
    return (
      <main>
        <div className="page-state error-state">Failed to load equipment</div>
      </main>
    );
  }

  return (
    <main>
      <Link className="back-link" to="/">
        ← Back to equipment
      </Link>

      <section className="page-heading equipment-detail-heading">
        <p className="eyebrow">{equipment.category_name}</p>

        <div className="detail-title-row">
          <h2>{equipment.name}</h2>

          <span className={`status-badge status-${equipment.status}`}>
            {equipment.status}
          </span>
        </div>

        <p className="page-description">
          View equipment information and check reservation availability.
        </p>
      </section>

      <div className="equipment-detail-layout">
        <section className="equipment-detail-card">
          <h3>Equipment details</h3>

          <div className="equipment-detail-meta">
            <div>
              <span>Asset tag</span>
              <strong>{equipment.asset_tag}</strong>
            </div>

            <div>
              <span>Category</span>
              <strong>{equipment.category_name}</strong>
            </div>
          </div>
        </section>

        <section className="availability-card">
          {equipment.status === "active" ? (
            <>
              <div className="availability-heading">
                <h3>Check availability</h3>
                <p>Select the dates you want to reserve this equipment.</p>
              </div>

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

              {availability === true && (
                <p className="success-message">Available</p>
              )}

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
                    {reservationLoading ? "Reserving..." : "Reserve equipment"}
                  </button>

                  {reservationMessage && (
                    <p className="reservation-message">{reservationMessage}</p>
                  )}
                </div>
              ) : (
                <p className="login-prompt">
                  <Link to="/login">Login</Link> to reserve this equipment.
                </p>
              )}
            </>
          ) : (
            <div className="unavailable-message">
              This equipment is not currently available for reservation.
            </div>
          )}
        </section>
      </div>
    </main>
  );
}

export default EquipmentDetailPage;
