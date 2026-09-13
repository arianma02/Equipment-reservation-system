import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

function Header() {
  const { user, logout } = useAuth();

  return (
    <header>
      <h1>Equipment Reservation System</h1>

      <Link to="/equipment">Equipment</Link>

      {user ? (
        <div>
          <Link to="/reservations/me">My Reservations</Link>
          <Link to="/account">My Account</Link>

          {user.role === "admin" && <Link to="/admin">Admin</Link>}
          <p>Logged in as {user.email}</p>
          <button onClick={logout}>Logout</button>
        </div>
      ) : (
        <Link to="/login">Login</Link>
      )}
    </header>
  );
}

export default Header;
