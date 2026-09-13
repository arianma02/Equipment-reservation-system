import { Link } from "react-router-dom";

function AdminPage() {
  return (
    <main>
      <h2>Admin</h2>

      <nav className="admin-grid">
        <Link to="/admin/users" className="admin-card">
          Manage Users
        </Link>

        <Link to="/admin/equipment" className="admin-card">
          Manage Equipment
        </Link>

        <Link to="/admin/categories" className="admin-card">
          Manage Categories
        </Link>

        <Link to="/admin/reservations" className="admin-card">
          Manage Reservations
        </Link>
      </nav>
    </main>
  );
}

export default AdminPage;
