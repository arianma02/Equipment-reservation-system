import { Link } from "react-router-dom";

function AdminPage() {
  return (
    <main>
      <h2>Admin</h2>

      <Link to="/admin/users">Manage Users</Link>
      <Link to="/admin/equipment">Manage Equipment</Link>
      <Link to="/admin/categories">Manage Categories</Link>
      <Link to="/admin/reservations">Manage Reservations</Link>
    </main>
  );
}

export default AdminPage;
