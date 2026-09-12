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
      <h2>My Account</h2>

      <p>Email: {user?.email}</p>
      <p>Role: {user?.role}</p>
      <p>Status: {user?.status}</p>

      <button onClick={deactivateAccount} disabled={deactivating}>
        {deactivating ? "Deactivating..." : "Deactivate Account"}
      </button>

      {error && <p>{error}</p>}
    </main>
  );
}

export default AccountPage;
