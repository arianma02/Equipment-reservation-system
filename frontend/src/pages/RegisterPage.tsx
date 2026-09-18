import { useState } from "react";
import { API_URL } from "../config";
import { useNavigate, Navigate, Link } from "react-router-dom";
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
    return (
      <main>
        <div className="page-state">Loading...</div>
      </main>
    );
  }

  if (user) {
    return <Navigate to="/equipment" replace />;
  }

  return (
    <main className="auth-page">
      <div className="auth-card">
        <div className="auth-heading">
          <p className="eyebrow">CREATE ACCOUNT</p>
          <h2>Register</h2>
          <p>Create an account to reserve available equipment.</p>
        </div>

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

          <button className="auth-submit" type="submit">
            Register
          </button>

          {error && <p className="error-message">{error}</p>}
        </form>

        <p className="auth-switch">
          Already have an account? <Link to="/login">Login</Link>
        </p>
      </div>
    </main>
  );
}

export default RegisterPage;
