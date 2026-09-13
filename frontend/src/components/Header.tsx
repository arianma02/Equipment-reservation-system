import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="site-header">
      <div className="header-content">
        <h1>Equipment Reservation System</h1>

        <nav className="header-nav">
          <Link to="/equipment">Equipment</Link>

          {user ? (
            <>
              <Link to="/reservations/me">My Reservations</Link>
              <Link to="/account">My Account</Link>

              {user.role === "admin" && <Link to="/admin">Admin</Link>}

              <span className="header-user">Logged in as {user.email}</span>

              <button onClick={logout}>Logout</button>
            </>
          ) : (
            <>
              <Link to="/login">Login</Link>
              <Link to="/register">Register</Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}

export default Header;
