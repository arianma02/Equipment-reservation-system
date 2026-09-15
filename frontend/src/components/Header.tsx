import { NavLink } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="site-header">
      <div className="header-content">
        <h1>Equipment Reservation System</h1>

        <nav className="header-nav">
          <NavLink to="/equipment">Equipment</NavLink>

          {user ? (
            <>
              <NavLink to="/reservations/me">My Reservations</NavLink>
              <NavLink to="/account">My Account</NavLink>

              {user.role === "admin" && <NavLink to="/admin">Admin</NavLink>}

              <span className="header-user">Logged in as {user.email}</span>

              <button onClick={logout}>Logout</button>
            </>
          ) : (
            <>
              <NavLink to="/login">Login</NavLink>
              <NavLink to="/register">Register</NavLink>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}

export default Header;
