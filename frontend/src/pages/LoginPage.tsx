import { useState } from "react";
import { useNavigate, useLocation, Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { API_URL } from "../config";

function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const navigate = useNavigate();
  const { refreshUser, user, authLoading } = useAuth();

  const location = useLocation();
  const message = location.state?.message;

  async function handleLogin(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    try {
      const response = await fetch(`${API_URL}/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          password,
        }),
      });

      if (!response.ok) {
        throw new Error("Login failed");
      }

      const data = await response.json();
      localStorage.setItem("access_token", data.access_token);
      await refreshUser();
      navigate("/equipment");
    } catch {
      setError("Login failed");
    }
  }
  if (authLoading) {
    return (
      <main>
        <p>Loading...</p>
      </main>
    );
  }

  if (user) {
    return <Navigate to="/equipment" replace />;
  }

  return (
    <main className="auth-page">
      <div className="auth-card">
        <h2>Login</h2>

        {message && <p>{message}</p>}

        <form className="auth-form" onSubmit={handleLogin}>
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
              required
            />
          </label>

          <button type="submit">Login</button>

          {error && <p>{error}</p>}
        </form>
      </div>
    </main>
  );
}

export default LoginPage;
