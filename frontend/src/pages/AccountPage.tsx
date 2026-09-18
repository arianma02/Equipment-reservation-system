import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { API_URL } from "../config";
import { useAuth } from "../hooks/useAuth";

function AccountPage() {
  const { user, logout } = useAuth();

  const navigate = useNavigate();

  const [error, setError] = useState("");
  const [deactivating, setDeactivating] = useState(false);

  async function deactivateAccount() {
    const confirmed = window.confirm(
      "Are you sure you want to deactivate your account?",
    );

    if (!confirmed) {
      return;
    }

    const token = localStorage.getItem("access_token");

    if (!token) {
      setError("You must be logged in");
      return;
    }

    setError("");
    setDeactivating(true);

    try {
      const response = await fetch(`${API_URL}/users/me/deactivate`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to deactivate account");
      }

      logout();
      navigate("/login", {
        state: { message: "Account deactivated successfully" },
        replace: true,
      });
    } catch (error) {
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError("Failed to deactivate account");
      }
    } finally {
      setDeactivating(false);
    }
  }

  return (
    <main>
      <section className="page-heading">
        <p className="eyebrow">ACCOUNT</p>
        <h2>My account</h2>
        <p className="page-description">
          View your account information and manage your account.
        </p>
      </section>

      <section className="account-card">
        <h3>Account details</h3>

        <div className="account-details">
          <div>
            <span>Email</span>
            <strong>{user?.email}</strong>
          </div>

          <div>
            <span>Role</span>
            <strong>{user?.role}</strong>
          </div>

          <div>
            <span>Status</span>
            <span className={`status-badge status-${user?.status}`}>
              {user?.status}
            </span>
          </div>
        </div>

        <div className="danger-zone">
          <div>
            <h3>Deactivate account</h3>
            <p>
              Deactivating your account will sign you out and prevent further
              access.
            </p>
          </div>

          <button
            className="danger-button"
            onClick={deactivateAccount}
            disabled={deactivating}
          >
            {deactivating ? "Deactivating..." : "Deactivate account"}
          </button>
        </div>

        {error && <p className="error-message">{error}</p>}
      </section>
    </main>
  );
}

export default AccountPage;
