import { useState } from "react";
import { API_URL } from "../config";
import { useNavigate, Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const navigate = useNavigate();
  const { user, authLoading } = useAuth();

  async function handleRegister(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    try {
      const response = await fetch(`${API_URL}/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Registration failed");
      }

      navigate("/login", {
        state: { message: "Account registered successfully" },
        replace: true,
      });
    } catch (error) {
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError("Registration failed");
      }
    }
  }
  if (authLoading) {
    return <p>Loading...</p>;
  }

  if (user) {
    return <Navigate to="/equipment" replace />;
  }

  return (
    <main className="auth-page">
      <div className="auth-card">
        <h2>Register</h2>

        <form className="auth-form" onSubmit={handleRegister}>
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              minLength={8}
              required
            />
          </label>

          <button type="submit">Register</button>

          {error && <p>{error}</p>}
        </form>
      </div>
    </main>
  );
}

export default RegisterPage;
